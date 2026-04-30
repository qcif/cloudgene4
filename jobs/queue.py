"""
Job queue management system
"""
import logging
from collections import deque
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import Max
from celery import current_app

from .models import Job
from workflows.config_loader import CloudgeneConfigLoader

logger = logging.getLogger(__name__)


class JobQueue:
    """
    Manages job queue and execution
    """
    
    def __init__(self):
        self.config_loader = CloudgeneConfigLoader()
        self.config_loader.load_config()  # Initialize config
        self._queue = deque()
        self._running_jobs = set()
    
    def submit_job(self, job):
        """
        Submit a job to the queue
        """
        try:
            # Validate job name to fix space handling bug
            if job.name and ' ' in job.name:
                # Replace spaces with underscores to prevent backend errors
                job.name = job.name.replace(' ', '_')
                job.save()
            
            # Check queue limits
            queue_config = self.config_loader.config.get('queue', {})
            max_queue_size = queue_config.get('max_queue_size', 50)
            
            pending_count = Job.objects.filter(status='pending').count()
            
            if pending_count >= max_queue_size:
                raise Exception(f"Queue is full (max size: {max_queue_size})")
            
            # Set job priority and queue position
            job.priority = self.calculate_priority(job)
            job.queue_position = self.get_next_queue_position()
            job.status = 'pending'
            job.save()
            
            logger.info(f"Job {job.id} submitted to queue at position {job.queue_position}")
            
            # Try to start job immediately if possible
            self.process_queue()
            
            return True
            
        except Exception as e:
            job.status = 'failed'
            job.error_message = f"Failed to submit job: {str(e)}"
            job.save()
            logger.error(f"Failed to submit job {job.id}: {e}")
            raise
    
    def process_queue(self):
        """
        Process pending jobs in the queue
        """
        queue_config = self.config_loader.config.get('queue', {})
        max_concurrent_jobs = queue_config.get('max_concurrent_jobs', 10)
        
        # Count currently running jobs
        running_count = Job.objects.filter(status='running').count()
        
        if running_count >= max_concurrent_jobs:
            logger.debug(f"Maximum concurrent jobs reached ({running_count}/{max_concurrent_jobs})")
            return
        
        # Get pending jobs ordered by priority and submission time
        pending_jobs = Job.objects.filter(
            status='pending'
        ).order_by('-priority', 'submitted_at')
        
        jobs_to_start = max_concurrent_jobs - running_count
        
        for job in pending_jobs[:jobs_to_start]:
            try:
                self.start_job(job)
            except Exception as e:
                logger.error(f"Failed to start job {job.id}: {e}")
                job.status = 'failed'
                job.error_message = f"Failed to start job: {str(e)}"
                job.save()
    
    def start_job(self, job):
        """
        Start a specific job
        """
        with transaction.atomic():
            # Double-check job status to prevent race conditions
            job.refresh_from_db()
            if job.status != 'pending':
                return
            
            job.status = 'running'
            job.started_at = timezone.now()
            job.save()
        
        # Import here to avoid circular imports
        from .tasks import execute_workflow_job
        
        # Start the job execution task
        task = execute_workflow_job.delay(str(job.id))
        
        logger.info(f"Started job {job.id} with task {task.id}")
        
        # Store task ID for potential cancellation
        job.nextflow_process_id = task.id
        job.save()
    
    def cancel_job(self, job_id):
        """
        Cancel a job
        """
        try:
            job = Job.objects.get(id=job_id)
            
            if job.status == 'pending':
                job.status = 'cancelled'
                job.completed_at = timezone.now()
                job.save()
                logger.info(f"Cancelled pending job {job_id}")
                
                # Process queue to potentially start waiting jobs
                self.process_queue()
                
            elif job.status == 'running':
                # Cancel the running task
                if job.nextflow_process_id:
                    current_app.control.revoke(job.nextflow_process_id, terminate=True)
                
                job.status = 'cancelled'
                job.completed_at = timezone.now()
                job.save()
                logger.info(f"Cancelled running job {job_id}")
                
                # Process queue to start next job
                self.process_queue()
            
            else:
                raise Exception(f"Cannot cancel job in status: {job.status}")
            
            return True
            
        except Job.DoesNotExist:
            raise Exception(f"Job {job_id} not found")
    
    def restart_job(self, job_id):
        """
        Restart a failed or cancelled job
        """
        try:
            job = Job.objects.get(id=job_id)
            
            if not job.can_restart():
                raise Exception(f"Cannot restart job in status: {job.status}")
            
            # Reset job status and timestamps
            job.status = 'pending'
            job.started_at = None
            job.completed_at = None
            job.error_message = ''
            job.logs = ''
            job.queue_position = self.get_next_queue_position()
            job.save()
            
            # Clear previous job steps and messages
            job.steps.all().delete()
            job.messages.all().delete()
            
            logger.info(f"Restarted job {job_id}")
            
            # Try to process queue
            self.process_queue()
            
            return True
            
        except Job.DoesNotExist:
            raise Exception(f"Job {job_id} not found")
    
    def calculate_priority(self, job):
        """
        Calculate job priority based on user and workflow
        """
        priority = 0
        
        # Admin users get higher priority
        if job.user.is_admin_user():
            priority += 10
        
        # Priority can be set based on workflow type
        if hasattr(job.workflow, 'priority'):
            priority += job.workflow.priority
        
        return priority
    
    def get_next_queue_position(self):
        """
        Get the next queue position
        """
        last_position = Job.objects.filter(
            status='pending'
        ).aggregate(
            max_position=Max('queue_position')
        )['max_position']
        
        return (last_position or 0) + 1
    
    def get_queue_status(self):
        """
        Get current queue status
        """
        from django.db.models import Count, Q
        
        status_counts = Job.objects.aggregate(
            pending=Count('id', filter=Q(status='pending')),
            running=Count('id', filter=Q(status='running')),
            completed=Count('id', filter=Q(status='completed')),
            failed=Count('id', filter=Q(status='failed')),
            cancelled=Count('id', filter=Q(status='cancelled')),
        )
        
        queue_config = self.config_loader.config.get('queue', {})
        
        return {
            'status_counts': status_counts,
            'max_concurrent_jobs': queue_config.get('max_concurrent_jobs', 10),
            'max_queue_size': queue_config.get('max_queue_size', 50),
            'queue_active': not self.is_maintenance_mode(),
        }
    
    def is_maintenance_mode(self):
        """
        Check if server is in maintenance mode
        """
        server_config = self.config_loader.get_server_settings()
        return server_config.get('maintenance', False)
    
    def pause_queue(self):
        """
        Pause job processing
        """
        # This could update a database flag or configuration
        self.config_loader.config.setdefault('queue', {})['paused'] = True
        self.config_loader.save_config()
        logger.info("Job queue paused")
    
    def resume_queue(self):
        """
        Resume job processing
        """
        self.config_loader.config.setdefault('queue', {})['paused'] = False
        self.config_loader.save_config()
        logger.info("Job queue resumed")
        
        # Process pending jobs
        self.process_queue()
    
    def is_paused(self):
        """
        Check if queue is paused
        """
        queue_config = self.config_loader.config.get('queue', {})
        return queue_config.get('paused', False)


# Global queue instance
job_queue = JobQueue()