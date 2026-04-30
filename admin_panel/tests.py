"""
Unit tests for admin_panel app
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from .models import ServerSettings, Template, NavbarItem, SystemLog, Counter

User = get_user_model()


class ServerSettingsTest(TestCase):
    """Test cases for ServerSettings model"""
    
    def test_create_setting(self):
        """Test creating a server setting"""
        setting = ServerSettings.objects.create(
            name='max_jobs',
            value='10',
            description='Maximum number of jobs',
            setting_type='integer',
            category='general'
        )
        
        self.assertEqual(setting.name, 'max_jobs')
        self.assertEqual(setting.value, '10')
        self.assertEqual(setting.setting_type, 'integer')
        self.assertEqual(str(setting), 'general.max_jobs')
    
    def test_get_value_typed(self):
        """Test getting typed values from settings"""
        # Test integer
        int_setting = ServerSettings.objects.create(
            name='test_int',
            value='42',
            setting_type='integer'
        )
        self.assertEqual(int_setting.get_value(), 42)
        
        # Test boolean
        bool_setting = ServerSettings.objects.create(
            name='test_bool',
            value='true',
            setting_type='boolean'
        )
        self.assertTrue(bool_setting.get_value())
        
        bool_setting2 = ServerSettings.objects.create(
            name='test_bool2',
            value='false',
            setting_type='boolean'
        )
        self.assertFalse(bool_setting2.get_value())
        
        # Test JSON
        json_setting = ServerSettings.objects.create(
            name='test_json',
            value='{"key": "value"}',
            setting_type='json'
        )
        self.assertEqual(json_setting.get_value(), {'key': 'value'})
        
        # Test string (default)
        str_setting = ServerSettings.objects.create(
            name='test_str',
            value='hello world',
            setting_type='string'
        )
        self.assertEqual(str_setting.get_value(), 'hello world')


class TemplateTest(TestCase):
    """Test cases for Template model"""
    
    def test_create_template(self):
        """Test creating a template"""
        template = Template.objects.create(
            name='home',
            content='<h1>Welcome</h1>',
            description='Home page template',
            template_type='page'
        )
        
        self.assertEqual(template.name, 'home')
        self.assertEqual(template.content, '<h1>Welcome</h1>')
        self.assertEqual(template.template_type, 'page')
        self.assertEqual(str(template), 'home')


class CounterTest(TestCase):
    """Test cases for Counter model"""
    
    def test_create_counter(self):
        """Test creating a counter"""
        counter = Counter.objects.create(
            name='total_jobs',
            value=0,
            description='Total number of jobs'
        )
        
        self.assertEqual(counter.name, 'total_jobs')
        self.assertEqual(counter.value, 0)
        self.assertEqual(counter.description, 'Total number of jobs')
        self.assertEqual(str(counter), 'total_jobs: 0')
    
    def test_increment_counter(self):
        """Test incrementing a counter"""
        counter = Counter.objects.create(
            name='test_counter',
            value=5
        )
        
        counter.increment()
        self.assertEqual(counter.value, 6)
        
        counter.increment(3)
        self.assertEqual(counter.value, 9)
