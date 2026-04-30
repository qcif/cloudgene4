"""
Management command to set up Cloudgene with initial data
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from admin_panel.models import ServerSettings, Template, NavbarItem, Counter
from workflows.config_loader import CloudgeneConfigLoader

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up Cloudgene with initial configuration and data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-user',
            type=str,
            default='admin',
            help='Admin username'
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            default='admin@cloudgene.io',
            help='Admin email'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='admin123',
            help='Admin password'
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up Cloudgene...')
        
        # Create admin user
        self.create_admin_user(
            options['admin_user'],
            options['admin_email'],
            options['admin_password']
        )
        
        # Create default groups
        self.create_default_groups()
        
        # Load configuration
        self.load_configuration()
        
        # Create default templates
        self.create_default_templates()
        
        # Create navbar items
        self.create_navbar_items()
        
        # Initialize counters
        self.initialize_counters()
        
        # Load sample workflow
        self.load_sample_workflow()
        
        self.stdout.write(
            self.style.SUCCESS('Cloudgene setup completed successfully!')
        )

    def create_admin_user(self, username, email, password):
        """Create admin user if it doesn't exist"""
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                full_name='Administrator',
                is_staff=True,
                is_superuser=True
            )
            user.make_admin()
            self.stdout.write(f'Created admin user: {username}')
        else:
            self.stdout.write(f'Admin user {username} already exists')

    def create_default_groups(self):
        """Create default user groups"""
        groups = ['admin', 'user', 'analyst', 'researcher']
        
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'Created group: {group_name}')

    def load_configuration(self):
        """Load server configuration from YAML"""
        loader = CloudgeneConfigLoader()
        config = loader.load_config()
        
        # Create server settings from config
        server_config = config.get('server', {})
        for key, value in server_config.items():
            ServerSettings.objects.update_or_create(
                name=key,
                category='general',
                defaults={
                    'value': str(value),
                    'description': f'Server setting: {key}'
                }
            )
        
        self.stdout.write('Loaded server configuration')

    def create_default_templates(self):
        """Create default page templates"""
        templates = [
            {
                'name': 'home',
                'content': '''
<div class="jumbotron">
    <h1 class="display-4">Welcome to Cloudgene</h1>
    <p class="lead">Execute your bioinformatics workflows through a user-friendly web interface.</p>
    <hr class="my-4">
    <p>Get started by exploring available workflows or submitting a new job.</p>
    <a class="btn btn-primary btn-lg" href="/workflows" role="button">Browse Workflows</a>
</div>
                ''',
                'template_type': 'page',
                'description': 'Home page template'
            },
            {
                'name': 'footer',
                'content': '''
<footer class="bg-light mt-5 py-4">
    <div class="container">
        <div class="row">
            <div class="col-md-6">
                <p>&copy; 2024 Cloudgene. All rights reserved.</p>
            </div>
            <div class="col-md-6 text-right">
                <p>Powered by Django and Nextflow</p>
            </div>
        </div>
    </div>
</footer>
                ''',
                'template_type': 'partial',
                'description': 'Footer template'
            }
        ]
        
        for template_data in templates:
            Template.objects.update_or_create(
                name=template_data['name'],
                defaults=template_data
            )
        
        self.stdout.write('Created default templates')

    def create_navbar_items(self):
        """Create default navbar items"""
        navbar_items = [
            {'title': 'Home', 'url': '/', 'icon': 'home', 'order': 1},
            {'title': 'Workflows', 'url': '/workflows', 'icon': 'list', 'order': 2},
            {'title': 'Jobs', 'url': '/jobs', 'icon': 'tasks', 'order': 3},
            {'title': 'Admin', 'url': '/admin', 'icon': 'cog', 'order': 4, 'admin_only': True},
        ]
        
        for item_data in navbar_items:
            NavbarItem.objects.update_or_create(
                title=item_data['title'],
                defaults=item_data
            )
        
        self.stdout.write('Created navbar items')

    def initialize_counters(self):
        """Initialize system counters"""
        counters = [
            {'name': 'total_jobs', 'description': 'Total number of jobs submitted'},
            {'name': 'completed_jobs', 'description': 'Number of completed jobs'},
            {'name': 'failed_jobs', 'description': 'Number of failed jobs'},
            {'name': 'total_users', 'description': 'Total number of registered users'},
            {'name': 'active_workflows', 'description': 'Number of active workflows'},
        ]
        
        for counter_data in counters:
            Counter.objects.get_or_create(
                name=counter_data['name'],
                defaults=counter_data
            )
        
        self.stdout.write('Initialized counters')

    def load_sample_workflow(self):
        """Load the sample workflow"""
        try:
            from django.core.management import call_command
            call_command('load_sample_workflow')
            self.stdout.write('Loaded sample workflow')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Failed to load sample workflow: {e}')
            )