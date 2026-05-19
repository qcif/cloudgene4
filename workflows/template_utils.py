"""
Utilities for handling template variables in Nextflow configuration
"""
import os
import re
from django.conf import settings


def get_template_variables():
    """
    Get available template variables from Django settings and environment
    """
    variables = {
        'CLOUDGENE_APP_NAME': getattr(settings, 'APP_NAME', 'Cloudgene'),
        'CLOUDGENE_APP_ID': getattr(settings, 'APP_ID', 'cloudgene'),
        'CLOUDGENE_APP_VERSION': getattr(settings, 'APP_VERSION', '1.0.0'),
        'CLOUDGENE_APP_LOCATION': getattr(settings, 'APP_LOCATION', '/app'),
        'CLOUDGENE_SERVICE_NAME': getattr(settings, 'SERVICE_NAME', 'Cloudgene Service'),
        'CLOUDGENE_SERVICE_URL': getattr(settings, 'SERVICE_URL', 'http://localhost:3000'),
        'CLOUDGENE_CONTACT_NAME': getattr(settings, 'CONTACT_NAME', 'Administrator'),
        'CLOUDGENE_CONTACT_EMAIL': getattr(settings, 'CONTACT_EMAIL', 'admin@example.com'),
        'CLOUDGENE_WORKSPACE_TYPE': getattr(settings, 'WORKSPACE_TYPE', 'local'),
        'CLOUDGENE_WORKSPACE_HOME': getattr(settings, 'WORKSPACE_HOME', '/tmp/cloudgene'),
        'CLOUDGENE_SMTP_HOST': getattr(settings, 'SMTP_HOST', 'localhost'),
        'CLOUDGENE_SMTP_PORT': str(getattr(settings, 'SMTP_PORT', 25)),
        'CLOUDGENE_SMTP_USER': getattr(settings, 'SMTP_USER', ''),
        'CLOUDGENE_SMTP_PASSWORD': getattr(settings, 'SMTP_PASSWORD', ''),
        'CLOUDGENE_SMTP_NAME': getattr(settings, 'SMTP_NAME', 'Cloudgene'),
        'CLOUDGENE_SMTP_SENDER': getattr(settings, 'SMTP_SENDER', 'noreply@example.com'),
    }
    
    # Override with environment variables if they exist
    for key in variables.keys():
        env_value = os.getenv(key)
        if env_value is not None:
            variables[key] = env_value
    
    return variables


def substitute_template_variables(text):
    """
    Substitute template variables in text using ${VARIABLE_NAME} syntax
    
    Args:
        text (str): Text containing template variables
        
    Returns:
        str: Text with variables substituted
    """
    if not text:
        return text
    
    variables = get_template_variables()
    
    # Pattern to match ${VARIABLE_NAME}
    pattern = r'\$\{([A-Z_][A-Z0-9_]*)\}'
    
    def replace_var(match):
        var_name = match.group(1)
        return variables.get(var_name, match.group(0))  # Return original if not found
    
    return re.sub(pattern, replace_var, text)


def generate_nextflow_env_file(workflow):
    """
    Generate nextflow.env file content for a workflow
    
    Args:
        workflow: Workflow instance
        
    Returns:
        str: Content for nextflow.env file
    """
    if not workflow.env_vars:
        return ""
    
    return substitute_template_variables(workflow.env_vars)


def generate_nextflow_config_file(workflow):
    """
    Generate nextflow.config file content for a workflow
    
    Args:
        workflow: Workflow instance
        
    Returns:
        str: Content for nextflow.config file
    """
    if not workflow.nextflow_config:
        return ""
    
    return substitute_template_variables(workflow.nextflow_config)


def get_workflow_execution_config(workflow):
    """
    Get complete execution configuration for a workflow
    
    Args:
        workflow: Workflow instance
        
    Returns:
        dict: Configuration dictionary for Nextflow execution
    """
    config = {
        'profile': substitute_template_variables(workflow.nextflow_profile) if workflow.nextflow_profile else None,
        'work_dir': substitute_template_variables(workflow.working_directory) if workflow.working_directory else None,
        'env_file_content': generate_nextflow_env_file(workflow),
        'config_file_content': generate_nextflow_config_file(workflow),
    }
    
    return {k: v for k, v in config.items() if v is not None}