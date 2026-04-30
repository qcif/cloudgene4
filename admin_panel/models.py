import json
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ServerSettings(models.Model):
    """
    Global server configuration settings
    """
    name = models.CharField(max_length=255, unique=True)
    value = models.TextField(blank=True)
    description = models.TextField(blank=True)
    setting_type = models.CharField(max_length=50, choices=[
        ('string', 'String'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ], default='string')
    category = models.CharField(max_length=100, choices=[
        ('general', 'General'),
        ('nextflow', 'Nextflow'),
        ('mail', 'Mail'),
        ('security', 'Security'),
        ('queue', 'Queue'),
    ], default='general')
    
    class Meta:
        db_table = 'server_settings'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.category}.{self.name}"
    
    def get_value(self):
        """Return the value in the appropriate type"""
        if self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'integer':
            try:
                return int(self.value)
            except (ValueError, TypeError):
                return 0
        elif self.setting_type == 'json':
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return {}
        return self.value


class Template(models.Model):
    """
    HTML templates for pages (home, footer, etc.)
    """
    name = models.CharField(max_length=255, unique=True)
    content = models.TextField(blank=True)
    description = models.TextField(blank=True)
    template_type = models.CharField(max_length=50, choices=[
        ('page', 'Page'),
        ('email', 'Email'),
        ('partial', 'Partial'),
    ], default='page')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'templates'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class NavbarItem(models.Model):
    """
    Navigation bar items configuration
    """
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=500)
    icon = models.CharField(max_length=100, blank=True)
    order = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)
    required_groups = models.ManyToManyField('auth.Group', blank=True)
    admin_only = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'navbar_items'
        ordering = ['order', 'title']
    
    def __str__(self):
        return self.title


class SystemLog(models.Model):
    """
    System logs and events
    """
    LOG_LEVELS = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=20, choices=LOG_LEVELS)
    message = models.TextField()
    component = models.CharField(max_length=100, blank=True)  # e.g., 'jobs', 'workflows', 'auth'
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'system_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'level']),
            models.Index(fields=['component', 'level']),
        ]
    
    def __str__(self):
        return f"{self.timestamp} [{self.level.upper()}] {self.message[:50]}"


class Counter(models.Model):
    """
    System counters for statistics
    """
    name = models.CharField(max_length=255, unique=True)
    value = models.BigIntegerField(default=0)
    description = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'counters'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}: {self.value}"
    
    def increment(self, amount=1):
        """Increment counter by specified amount"""
        self.value += amount
        self.save()


class CounterHistory(models.Model):
    """
    Historical counter values for statistics
    """
    counter = models.ForeignKey(Counter, on_delete=models.CASCADE, related_name='history')
    value = models.BigIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'counter_history'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['counter', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.counter.name}: {self.value} at {self.timestamp}"
