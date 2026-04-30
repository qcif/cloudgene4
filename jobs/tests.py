"""
Unit tests for jobs app
"""
import uuid
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from .models import Job, JobStep, JobMessage, JobDownload
from .queue import JobQueue
from workflows.models import Workflow, WorkflowCategory

User = get_user_model()


class JobModelTest(TestCase):
    """Test cases for Job model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            password='TestPass123'
        )
        self.category = WorkflowCategory.objects.create(
            name='test',
            description='Test category'
        )
        self.workflow = Workflow.objects.create(
            id='test-workflow',
            name='Test Workflow',
            description='A test workflow',
            category=self.category,
            yaml_config='test: config'
        )
    
    def test_create_job(self):
        """Test creating a job"""
        job = Job.objects.create(
            name='test_job',
            workflow=self.workflow,
            user=self.user,
            parameters={'input': 'test_value'}
        )
        
        self.assertIsNotNone(job.id)
        self.assertEqual(job.name, 'test_job')
        self.assertEqual(job.workflow, self.workflow)
        self.assertEqual(job.user, self.user)
        self.assertEqual(job.status, 'pending')
        self.assertEqual(job.parameters, {'input': 'test_value'})
        self.assertIsNotNone(job.submitted_at)
        self.assertIsNone(job.started_at)
        self.assertIsNone(job.completed_at)
    
    def test_job_string_representation(self):
        """Test job string representation"""
        job = Job.objects.create(
            name='test_job',
            workflow=self.workflow,
            user=self.user
        )
        
        expected_str = f"test_job - Test Workflow (pending)"
        self.assertEqual(str(job), expected_str)
        
        # Test without name
        job_no_name = Job.objects.create(
            workflow=self.workflow,
            user=self.user
        )
        expected_str_no_name = f"Job {job_no_name.id} - Test Workflow (pending)"
        self.assertEqual(str(job_no_name), expected_str_no_name)
    
    def test_get_workspace_path(self):
        """Test getting workspace path"""
        job = Job.objects.create(
            workflow=self.workflow,
            user=self.user
        )
        
        workspace_path = job.get_workspace_path()
        self.assertIsNotNone(workspace_path)
        self.assertIn(str(job.user.id), workspace_path)
        self.assertIn(str(job.id), workspace_path)
    
    def test_get_duration(self):
        """Test getting job duration"""
        job = Job.objects.create(
            workflow=self.workflow,
            user=self.user
        )
        
        # No duration if not started
        self.assertIsNone(job.get_duration())
        
        # Duration if started but not completed
        job.started_at = timezone.now()
        job.save()
        duration = job.get_duration()
        self.assertIsNotNone(duration)
        
        # Duration if completed
        job.completed_at = timezone.now()
        job.save()
        duration = job.get_duration()
        self.assertIsNotNone(duration)
    
    def test_can_cancel(self):
        """Test job cancellation eligibility"""
        job = Job.objects.create(
            workflow=self.workflow,
            user=self.user
        )
        
        # Pending job can be cancelled
        job.status = 'pending'
        self.assertTrue(job.can_cancel())
        
        # Running job can be cancelled
        job.status = 'running'
        self.assertTrue(job.can_cancel())
        
        # Completed job cannot be cancelled
        job.status = 'completed'
        self.assertFalse(job.can_cancel())
        
        # Failed job cannot be cancelled
        job.status = 'failed'
        self.assertFalse(job.can_cancel())
    
    def test_can_restart(self):
        """Test job restart eligibility"""
        job = Job.objects.create(
            workflow=self.workflow,
            user=self.user
        )
        
        # Pending job cannot be restarted
        job.status = 'pending'
        self.assertFalse(job.can_restart())
        
        # Running job cannot be restarted
        job.status = 'running'
        self.assertFalse(job.can_restart())
        
        # Completed job can be restarted
        job.status = 'completed'
        self.assertTrue(job.can_restart())
        
        # Failed job can be restarted
        job.status = 'failed'
        self.assertTrue(job.can_restart())
        
        # Cancelled job can be restarted
        job.status = 'cancelled'
        self.assertTrue(job.can_restart())


class JobStepTest(TestCase):
    """Test cases for JobStep model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            password='TestPass123'
        )
        self.workflow = Workflow.objects.create(
            id='test-workflow',
            name='Test Workflow',
            yaml_config='test: config'
        )
        self.job = Job.objects.create(
            workflow=self.workflow,
            user=self.user
        )
    
    def test_create_job_step(self):
        """Test creating a job step"""
        step = JobStep.objects.create(
            job=self.job,
            name='TestStep',
            description='A test step',
            step_type='nextflow',
            order=1,
            parameters={'param': 'value'}
        )
        
        self.assertEqual(step.job, self.job)
        self.assertEqual(step.name, 'TestStep')
        self.assertEqual(step.step_type, 'nextflow')
        self.assertEqual(step.status, 'pending')
        self.assertEqual(step.order, 1)
        self.assertEqual(step.parameters, {'param': 'value'})
        self.assertIsNone(step.started_at)
        self.assertIsNone(step.completed_at)


class JobMessageTest(TestCase):
    """Test cases for JobMessage model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            password='TestPass123'
        )
        self.workflow = Workflow.objects.create(
            id='test-workflow',
            name='Test Workflow',
            yaml_config='test: config'
        )
        self.job = Job.objects.create(
            workflow=self.workflow,
            user=self.user
        )
    
    def test_create_job_message(self):
        """Test creating a job message"""
        message = JobMessage.objects.create(
            job=self.job,
            message_type='info',
            message='Job started successfully'
        )
        
        self.assertEqual(message.job, self.job)
        self.assertEqual(message.message_type, 'info')
        self.assertEqual(message.message, 'Job started successfully')
        self.assertIsNotNone(message.created_at)


class JobDownloadTest(TestCase):
    """Test cases for JobDownload model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            password='TestPass123'
        )
        self.workflow = Workflow.objects.create(
            id='test-workflow',
            name='Test Workflow',
            yaml_config='test: config'
        )
        self.job = Job.objects.create(
            workflow=self.workflow,
            user=self.user
        )
    
    def test_create_job_download(self):
        """Test creating a job download"""
        download = JobDownload.objects.create(
            job=self.job,
            filename='results.txt',
            file_path='/path/to/results.txt',
            file_size=1024
        )
        
        self.assertEqual(download.job, self.job)
        self.assertEqual(download.filename, 'results.txt')
        self.assertEqual(download.file_path, '/path/to/results.txt')
        self.assertEqual(download.file_size, 1024)
        self.assertEqual(download.download_count, 0)
        self.assertFalse(download.is_expired())
    
    def test_download_expiration(self):
        """Test download expiration"""
        from datetime import timedelta
        
        # Create expired download
        download = JobDownload.objects.create(
            job=self.job,
            filename='expired.txt',
            file_path='/path/to/expired.txt',
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        self.assertTrue(download.is_expired())
        
        # Create non-expired download
        download2 = JobDownload.objects.create(
            job=self.job,
            filename='valid.txt',
            file_path='/path/to/valid.txt',
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        self.assertFalse(download2.is_expired())


class JobQueueTest(TestCase):
    """Test cases for JobQueue"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            full_name='Test User',
            password='TestPass123'
        )
        self.workflow = Workflow.objects.create(
            id='test-workflow',
            name='Test Workflow',
            yaml_config='test: config'
        )
        self.queue = JobQueue()
    
    def test_job_name_sanitization(self):
        """Test that job names with spaces are sanitized"""
        job = Job.objects.create(
            name='Job with spaces',
            workflow=self.workflow,
            user=self.user
        )
        
        # Mock the queue processing to avoid Celery dependencies
        with patch.object(self.queue, 'process_queue'):
            self.queue.submit_job(job)
        
        job.refresh_from_db()
        self.assertEqual(job.name, 'Job_with_spaces')
    
    def test_calculate_priority(self):
        """Test priority calculation"""
        job = Job.objects.create(
            workflow=self.workflow,
            user=self.user
        )
        
        priority = self.queue.calculate_priority(job)
        self.assertEqual(priority, 0)  # Regular user, no special priority
        
        # Test admin user priority
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123',
            full_name='Admin User'
        )
        admin_job = Job.objects.create(
            workflow=self.workflow,
            user=admin_user
        )
        
        admin_priority = self.queue.calculate_priority(admin_job)
        self.assertGreater(admin_priority, priority)
    
    def test_get_queue_status(self):
        """Test getting queue status"""
        # Create some test jobs
        Job.objects.create(workflow=self.workflow, user=self.user, status='pending')
        Job.objects.create(workflow=self.workflow, user=self.user, status='running')
        Job.objects.create(workflow=self.workflow, user=self.user, status='completed')
        
        status = self.queue.get_queue_status()
        
        self.assertIn('status_counts', status)
        self.assertIn('max_concurrent_jobs', status)
        self.assertIn('max_queue_size', status)
        self.assertIn('queue_active', status)
        
        # Check counts
        self.assertEqual(status['status_counts']['pending'], 1)
        self.assertEqual(status['status_counts']['running'], 1)
        self.assertEqual(status['status_counts']['completed'], 1)
