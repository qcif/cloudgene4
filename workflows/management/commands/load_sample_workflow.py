"""
Management command to load the sample workflow
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from workflows.config_loader import CloudgeneConfigLoader


class Command(BaseCommand):
    help = 'Load sample workflow from YAML file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='sample_workflow.yaml',
            help='Path to workflow YAML file'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        if not os.path.isabs(file_path):
            file_path = os.path.join(settings.BASE_DIR, file_path)
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'Workflow file not found: {file_path}')
            )
            return
        
        try:
            with open(file_path, 'r') as f:
                yaml_content = f.read()
            
            loader = CloudgeneConfigLoader()
            workflow = loader.load_workflow_from_yaml(yaml_content)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully loaded workflow: {workflow.name}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to load workflow: {str(e)}')
            )