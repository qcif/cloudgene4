"""
Celery tasks for job execution and management
"""
import os
import json
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Job, JobStep, JobMessage, JobDownload
from workflows.config_loader import CloudgeneConfigLoader


@shared_task(bind=True)
def execute_workflow_job(self, job_id):
    """
    Execute a workflow job using Nextflow
    """
    try:
        job = Job.objects.get(id=job_id)
        
        # Update job status to running
        job.status = 'running'
        job.started_at = timezone.now()
        job.save()
        
        # Send status update via WebSocket
        send_job_status_update(job_id, 'running', 'Job started')
        
        # Create workspace directory
        workspace = Path(job.get_workspace_path())
        workspace.mkdir(parents=True, exist_ok=True)
        
        # Execute workflow steps
        workflow_config = job.workflow.get_config()
        steps = workflow_config.get('workflow', {}).get('steps', [])
        
        for i, step_config in enumerate(steps):
            step = create_job_step(job, step_config, i)
            execute_step(job, step, workspace)
            
            if step.status == 'failed':
                job.status = 'failed'
                job.error_message = step.error_output
                break
        else:
            # All steps completed successfully
            job.status = 'completed'
            collect_job_outputs(job, workspace)
        
        job.completed_at = timezone.now()
        job.save()
        
        # Send final status update
        send_job_status_update(job_id, job.status, 
                              'Job completed' if job.status == 'completed' else 'Job failed')
        
        # Schedule cleanup
        cleanup_job_workspace.apply_async(args=[job_id], countdown=3600)  # Clean up after 1 hour
        
        return f"Job {job_id} completed with status: {job.status}"
        
    except Job.DoesNotExist:
        return f"Job {job_id} not found"
    except Exception as e:
        # Handle unexpected errors
        try:
            job = Job.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()
            send_job_status_update(job_id, 'failed', f'Job failed: {str(e)}')
        except:
            pass
        return f"Job {job_id} failed: {str(e)}"


def create_job_step(job, step_config, order):
    """Create a job step from configuration"""
    step = JobStep.objects.create(
        job=job,
        name=step_config.get('name', f'Step {order + 1}'),
        description=step_config.get('description', ''),
        step_type=step_config.get('classname', 'unknown'),
        order=order,
        parameters=step_config
    )
    return step


def execute_step(job, step, workspace):
    """Execute a single workflow step"""
    step.status = 'running'
    step.started_at = timezone.now()
    step.save()
    
    try:
        # Determine step type and execute accordingly
        if 'nextflow' in step.step_type.lower():
            execute_nextflow_step(job, step, workspace)
        elif 'bash' in step.step_type.lower() or 'command' in step.step_type.lower():
            execute_bash_step(job, step, workspace)
        elif 'docker' in step.step_type.lower():
            execute_docker_step(job, step, workspace)
        else:
            # Default: try to execute as a Python step
            execute_python_step(job, step, workspace)
        
        step.status = 'completed'
        step.completed_at = timezone.now()
        
    except Exception as e:
        step.status = 'failed'
        step.error_output = str(e)
        step.completed_at = timezone.now()
        
        # Create error message
        JobMessage.objects.create(
            job=job,
            message_type='error',
            message=f"Step '{step.name}' failed: {str(e)}"
        )
    
    finally:
        step.save()


def execute_nextflow_step(job, step, workspace):
    """Execute a Nextflow workflow step"""
    config_loader = CloudgeneConfigLoader()
    nextflow_config = config_loader.get_nextflow_settings()
    
    # Prepare Nextflow command
    nextflow_binary = nextflow_config.get('binary', 'nextflow')
    work_dir = nextflow_config.get('work_dir', workspace / 'work')
    
    # Create Nextflow script from workflow configuration
    script_content = generate_nextflow_script(job)
    script_path = workspace / 'main.nf'
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Prepare input parameters
    params = prepare_nextflow_params(job)
    params_file = workspace / 'params.json'
    
    with open(params_file, 'w') as f:
        json.dump(params, f, indent=2)
    
    # Execute Nextflow
    cmd = [
        nextflow_binary, 'run', str(script_path),
        '-params-file', str(params_file),
        '-work-dir', str(work_dir),
        '--outdir', str(workspace / 'results')
    ]
    
    # Add configuration file if specified
    config_file = job.workflow.config_file or nextflow_config.get('config_file')
    if config_file and os.path.exists(config_file):
        cmd.extend(['-c', config_file])
    
    result = subprocess.run(
        cmd,
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=3600  # 1 hour timeout
    )
    
    step.output = result.stdout
    step.error_output = result.stderr
    
    if result.returncode != 0:
        raise Exception(f"Nextflow execution failed: {result.stderr}")


def execute_bash_step(job, step, workspace):
    """Execute a bash command step"""
    command = step.parameters.get('command', '')
    if not command:
        raise Exception("No command specified for bash step")
    
    # Substitute parameters in command
    command = substitute_parameters(command, job.parameters)
    
    result = subprocess.run(
        command,
        shell=True,
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=1800  # 30 minutes timeout
    )
    
    step.output = result.stdout
    step.error_output = result.stderr
    
    if result.returncode != 0:
        raise Exception(f"Command execution failed: {result.stderr}")


def execute_docker_step(job, step, workspace):
    """Execute a Docker container step"""
    image = step.parameters.get('image', '')
    command = step.parameters.get('command', '')
    
    if not image:
        raise Exception("No Docker image specified")
    
    # Prepare Docker command
    docker_cmd = [
        'docker', 'run', '--rm',
        '-v', f'{workspace}:/workspace',
        '-w', '/workspace',
        image
    ]
    
    if command:
        docker_cmd.extend(['sh', '-c', command])
    
    result = subprocess.run(
        docker_cmd,
        capture_output=True,
        text=True,
        timeout=1800  # 30 minutes timeout
    )
    
    step.output = result.stdout
    step.error_output = result.stderr
    
    if result.returncode != 0:
        raise Exception(f"Docker execution failed: {result.stderr}")


def execute_python_step(job, step, workspace):
    """Execute a Python step (placeholder)"""
    # This would typically import and execute custom Python workflow steps
    step.output = "Python step executed successfully"


def generate_nextflow_script(job):
    """Generate Nextflow script from job parameters"""
    # Basic Nextflow script template
    script = """#!/usr/bin/env nextflow

params.outdir = 'results'

process MAIN {
    publishDir params.outdir, mode: 'copy'
    
    input:
"""
    
    # Add inputs based on workflow parameters
    for param in job.workflow.get_inputs():
        if param.get('type') == 'file':
            script += f"    path {param['id']}\n"
        else:
            script += f"    val {param['id']}\n"
    
    script += """
    output:
    path "*", emit: results
    
    script:
    '''
    echo "Processing workflow..."
    # Add your workflow logic here
    '''
}

workflow {
    MAIN(
"""
    
    # Add parameter values
    for i, param in enumerate(job.workflow.get_inputs()):
        param_value = job.parameters.get(param['id'], param.get('value', ''))
        if i > 0:
            script += ",\n        "
        script += f"params.{param['id']}"
    
    script += """
    )
}
"""
    
    return script


def prepare_nextflow_params(job):
    """Prepare parameters for Nextflow execution"""
    params = {}
    
    for param_id, value in job.parameters.items():
        params[param_id] = value
    
    return params


def substitute_parameters(template, parameters):
    """Substitute parameters in command template"""
    for param_id, value in parameters.items():
        template = template.replace(f"${{{param_id}}}", str(value))
    
    return template


def collect_job_outputs(job, workspace):
    """Collect job outputs and create download links"""
    results_dir = workspace / 'results'
    
    if not results_dir.exists():
        return
    
    # Collect all output files
    for file_path in results_dir.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(results_dir)
            
            JobDownload.objects.create(
                job=job,
                filename=str(relative_path),
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                expires_at=timezone.now() + timedelta(days=7)  # Expire after 7 days
            )


def send_job_status_update(job_id, status, message=None):
    """Send job status update via WebSocket"""
    channel_layer = get_channel_layer()
    
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f'job_{job_id}',
            {
                'type': 'job_status_update',
                'job_id': str(job_id),
                'status': status,
                'message': message,
                'timestamp': timezone.now().isoformat(),
            }
        )


@shared_task
def cleanup_job_workspace(job_id):
    """Clean up job workspace after completion"""
    try:
        job = Job.objects.get(id=job_id)
        workspace = Path(job.get_workspace_path())
        
        if workspace.exists():
            shutil.rmtree(workspace)
            
        return f"Cleaned up workspace for job {job_id}"
        
    except Job.DoesNotExist:
        return f"Job {job_id} not found"
    except Exception as e:
        return f"Failed to clean up job {job_id}: {str(e)}"


@shared_task
def cancel_job(job_id):
    """Cancel a running job"""
    try:
        job = Job.objects.get(id=job_id)
        
        if job.status in ['pending', 'running']:
            job.status = 'cancelled'
            job.completed_at = timezone.now()
            job.save()
            
            # Try to kill the Nextflow process if it exists
            if job.nextflow_process_id:
                try:
                    subprocess.run(['kill', '-TERM', job.nextflow_process_id])
                except:
                    pass
            
            send_job_status_update(job_id, 'cancelled', 'Job was cancelled')
            
        return f"Job {job_id} cancelled"
        
    except Job.DoesNotExist:
        return f"Job {job_id} not found"


@shared_task
def cleanup_expired_jobs():
    """Clean up expired jobs and their workspaces"""
    config_loader = CloudgeneConfigLoader()
    queue_config = config_loader.config.get('queue', {})
    max_job_age = queue_config.get('max_job_age', 604800)  # Default 7 days
    
    cutoff_date = timezone.now() - timedelta(seconds=max_job_age)
    
    expired_jobs = Job.objects.filter(
        completed_at__lt=cutoff_date,
        status__in=['completed', 'failed', 'cancelled']
    )
    
    count = 0
    for job in expired_jobs:
        try:
            # Clean up workspace
            workspace = Path(job.get_workspace_path())
            if workspace.exists():
                shutil.rmtree(workspace)
            
            # Delete job record
            job.delete()
            count += 1
            
        except Exception as e:
            print(f"Failed to clean up job {job.id}: {e}")
    
    return f"Cleaned up {count} expired jobs"