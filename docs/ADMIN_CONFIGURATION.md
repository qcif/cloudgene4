# Cloudgene Admin Configuration Guide

This document provides comprehensive information about configuring your Cloudgene Django server and managing workflow definitions.

## Table of Contents

1. [Server Configuration](#server-configuration)
2. [Environment Variables](#environment-variables)
3. [Configuration File Structure](#configuration-file-structure)
4. [Database Settings](#database-settings)
5. [Queue Configuration](#queue-configuration)
6. [Security Settings](#security-settings)
7. [Email Configuration](#email-configuration)
8. [Nextflow Integration](#nextflow-integration)
9. [Templates and UI Customization](#templates-and-ui-customization)
10. [Performance Tuning](#performance-tuning)
11. [Troubleshooting](#troubleshooting)

---

## Server Configuration

### Main Configuration File

The primary server configuration is stored in `cloudgene_config.yaml`. This file controls all aspects of the Cloudgene server behavior.

**Location**: `cloudgene_config.yaml` (in project root)

### Basic Server Settings

```yaml
server:
  name: "Cloudgene Django Server"    # Server display name
  port: 8000                         # HTTP port (Django development server)
  maintenance: false                 # Enable maintenance mode
  max_jobs: 10                      # Maximum concurrent jobs
  max_queue_size: 50                # Maximum jobs in queue
  debug: false                      # Debug mode (use false in production)
```

#### Server Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | string | "Cloudgene Server" | Display name for the server |
| `port` | integer | 8080 | Port for Django development server |
| `maintenance` | boolean | false | Enable maintenance mode (blocks job submission) |
| `max_jobs` | integer | 10 | Maximum number of concurrent running jobs |
| `max_queue_size` | integer | 50 | Maximum number of jobs allowed in queue |
| `debug` | boolean | false | Enable debug mode (verbose logging) |

---

## Environment Variables

Configure these environment variables for production deployments:

### Django Settings

```bash
# Security
export DJANGO_SECRET_KEY="your-secret-key-here"
export DEBUG="False"
export ALLOWED_HOSTS="your-domain.com,www.your-domain.com"

# Database
export DATABASE_URL="postgresql://user:pass@localhost/cloudgene"

# Redis/Celery
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"

# File Storage
export MEDIA_ROOT="/var/cloudgene/media"
export STATIC_ROOT="/var/cloudgene/static"

# Cloudgene Specific
export CLOUDGENE_CONFIG_FILE="/etc/cloudgene/config.yaml"
export NEXTFLOW_BINARY="/usr/local/bin/nextflow"
export WORKFLOWS_DIR="/var/cloudgene/workflows"
export JOBS_DIR="/var/cloudgene/jobs"
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key for cryptographic signing | `django-insecure-xyz123...` |
| `DATABASE_URL` | Database connection URL | `postgresql://user:pass@host/db` |
| `CELERY_BROKER_URL` | Redis URL for Celery message broker | `redis://localhost:6379/0` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable Django debug mode | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames | `*` |
| `WORKFLOWS_DIR` | Directory for workflow definitions | `./workflows` |
| `JOBS_DIR` | Directory for job workspaces | `./jobs` |

---

## Configuration File Structure

### Complete Configuration Template

```yaml
# Server configuration
server:
  name: "Cloudgene Django Server"
  port: 8000
  maintenance: false
  max_jobs: 10
  max_queue_size: 50
  debug: false

# Navigation bar items
navbar:
  - title: "Home"
    url: "/"
    icon: "home"
    order: 1
    visible: true
    
  - title: "Workflows"
    url: "/workflows"
    icon: "workflow"
    order: 2
    visible: true
    
  - title: "Jobs"
    url: "/jobs"
    icon: "jobs"
    order: 3
    visible: true
    
  - title: "Admin"
    url: "/admin"
    icon: "admin"
    order: 4
    visible: true
    admin_only: true

# HTML templates for pages
templates:
  home: |
    <h1>Welcome to Cloudgene</h1>
    <p>Execute your Nextflow workflows through a user-friendly web interface.</p>
  
  footer: |
    <p>&copy; 2024 Cloudgene. Powered by Django and Nextflow.</p>
  
  about: |
    <h2>About Cloudgene</h2>
    <p>Cloudgene is a workflow execution platform for bioinformatics pipelines.</p>

# Email configuration
mail:
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  smtp_user: "your-email@gmail.com"
  smtp_password: "your-app-password"
  from_email: "noreply@cloudgene.io"
  use_tls: true

# Nextflow settings
nextflow:
  binary: "nextflow"
  work_dir: "/tmp/nextflow-work"
  config_file: "/etc/nextflow/nextflow.config"
  max_memory: "8.GB"
  max_cpus: 4
  executor: "local"

# Security settings
security:
  session_timeout: 3600        # Session timeout in seconds
  max_login_attempts: 5        # Max failed login attempts
  lockout_duration: 300        # Lockout duration in seconds
  require_activation: true     # Require email activation for new users

# Queue management
queue:
  max_concurrent_jobs: 10      # Maximum concurrent jobs across all users
  job_timeout: 86400          # Job timeout in seconds (24 hours)
  cleanup_interval: 3600      # Cleanup interval in seconds (1 hour)
  max_job_age: 604800         # Maximum job age in seconds (7 days)
```

---

## Database Settings

### Supported Databases

**SQLite** (Development)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**PostgreSQL** (Recommended for Production)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cloudgene',
        'USER': 'cloudgene_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}
```

**MySQL**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'cloudgene',
        'USER': 'cloudgene_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'sql_mode': 'traditional',
        },
    }
}
```

### Database Migration

```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data
python manage.py loaddata initial_data.json
```

---

## Queue Configuration

### Queue Settings

```yaml
queue:
  max_concurrent_jobs: 10      # System-wide concurrent job limit
  job_timeout: 86400          # Job timeout (24 hours)
  cleanup_interval: 3600      # Cleanup old jobs every hour
  max_job_age: 604800         # Keep jobs for 7 days
  priority_levels:            # Job priority system
    admin: 100
    premium: 50
    standard: 10
```

### Priority System

Jobs are prioritized based on user type:

| User Type | Priority | Description |
|-----------|----------|-------------|
| Admin/Superuser | 100 | Highest priority |
| Premium Users | 50 | Medium priority |
| Standard Users | 10 | Normal priority |

### Queue Management

**Start Queue Processing**:
```bash
# Start Celery worker
celery -A cloudgene_django worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A cloudgene_django beat --loglevel=info
```

**Monitor Queue**:
```bash
# View queue status
celery -A cloudgene_django inspect active

# View worker stats
celery -A cloudgene_django inspect stats
```

---

## Security Settings

### Authentication Configuration

```yaml
security:
  # Session management
  session_timeout: 3600        # 1 hour session timeout
  session_cookie_age: 86400    # 24 hour cookie lifetime
  
  # Login protection
  max_login_attempts: 5        # Failed login limit
  lockout_duration: 300        # 5 minute lockout
  
  # Account activation
  require_activation: true     # Email verification required
  activation_timeout: 86400    # 24 hour activation window
  
  # Password requirements
  min_password_length: 6
  require_uppercase: true
  require_lowercase: true
  require_numbers: true
  require_special_chars: false
  
  # API security
  api_rate_limit: "100/hour"   # API rate limiting
  token_expiry: 2592000        # 30 day token expiry
```

### SSL/HTTPS Configuration

**Production Settings** (in `settings.py`):
```python
# Security settings for production
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### User Group Management

Configure user groups for workflow access control:

```python
# In Django admin or via API
from django.contrib.auth.models import Group

# Create groups
bioinformatics_group = Group.objects.create(name='bioinformatics')
genomics_group = Group.objects.create(name='genomics')
admin_group = Group.objects.create(name='admin')

# Assign users to groups
user.groups.add(bioinformatics_group)
```

---

## Email Configuration

### SMTP Settings

```yaml
mail:
  smtp_host: "smtp.gmail.com"          # SMTP server hostname
  smtp_port: 587                       # SMTP port (587 for TLS, 465 for SSL)
  smtp_user: "your-email@gmail.com"    # SMTP username
  smtp_password: "app-password"        # SMTP password (use app passwords)
  from_email: "noreply@cloudgene.io"   # From email address
  from_name: "Cloudgene Server"        # From name
  use_tls: true                        # Use TLS encryption
  use_ssl: false                       # Use SSL encryption (alternative to TLS)
  timeout: 30                          # Connection timeout in seconds
```

### Email Providers

**Gmail**:
```yaml
mail:
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  use_tls: true
  # Requires app-specific password
```

**Outlook/Hotmail**:
```yaml
mail:
  smtp_host: "smtp-mail.outlook.com"
  smtp_port: 587
  use_tls: true
```

**SendGrid**:
```yaml
mail:
  smtp_host: "smtp.sendgrid.net"
  smtp_port: 587
  smtp_user: "apikey"
  smtp_password: "your-sendgrid-api-key"
  use_tls: true
```

### Email Templates

Customize email templates in the Django admin panel:

- **Account Activation**: Welcome email with activation link
- **Password Reset**: Password reset instructions
- **Job Notifications**: Job completion/failure notifications

---

## Nextflow Integration

### Nextflow Configuration

```yaml
nextflow:
  binary: "nextflow"                    # Path to Nextflow binary
  work_dir: "/tmp/nextflow-work"       # Working directory for Nextflow
  config_file: ""                      # Custom Nextflow config file
  max_memory: "8.GB"                   # Default memory limit
  max_cpus: 4                          # Default CPU limit
  executor: "local"                    # Default executor
  
  # Advanced settings
  env:                                 # Environment variables
    NXF_OPTS: "-Xmx2g"
    NXF_HOME: "/opt/nextflow"
    
  profiles:                            # Execution profiles
    local:
      executor: "local"
      max_memory: "8.GB"
      max_cpus: 4
      
    cluster:
      executor: "slurm"
      queue: "main"
      max_memory: "32.GB"
      max_cpus: 16
      
    cloud:
      executor: "awsbatch"
      region: "us-west-2"
      queue: "nextflow-queue"
```

### Execution Profiles

Configure different execution environments:

**Local Execution**:
```yaml
profiles:
  local:
    executor: "local"
    cpus: 4
    memory: "8.GB"
```

**SLURM Cluster**:
```yaml
profiles:
  slurm:
    executor: "slurm"
    queue: "main"
    queueSize: 100
    submitRateLimit: "10 sec"
```

**AWS Batch**:
```yaml
profiles:
  aws:
    executor: "awsbatch"
    region: "us-west-2"
    queue: "nextflow-queue"
```

### Custom Nextflow Config

Create a custom Nextflow configuration file:

```groovy
// nextflow.config
params {
    // Default parameters
    max_memory = '8.GB'
    max_cpus = 4
    max_time = '24.h'
}

profiles {
    local {
        executor.name = 'local'
        executor.cpus = params.max_cpus
        executor.memory = params.max_memory
    }
    
    cluster {
        executor.name = 'slurm'
        executor.queueSize = 100
        executor.submitRateLimit = '10 sec'
    }
}

// Resource management
process {
    withName: 'MEMORY_INTENSIVE' {
        memory = '16.GB'
        time = '6.h'
    }
    
    withName: 'CPU_INTENSIVE' {
        cpus = 8
        time = '12.h'
    }
}
```

---

## Templates and UI Customization

### HTML Templates

Customize the user interface through HTML templates:

```yaml
templates:
  # Home page content
  home: |
    <div class="hero-section">
      <h1>Welcome to Our Cloudgene Server</h1>
      <p>Execute bioinformatics workflows with ease</p>
      <a href="/workflows" class="btn btn-primary">Browse Workflows</a>
    </div>
  
  # Page footer
  footer: |
    <footer class="site-footer">
      <p>&copy; 2024 Your Organization. All rights reserved.</p>
      <p>Powered by <a href="https://cloudgene.io">Cloudgene</a></p>
    </footer>
  
  # About page
  about: |
    <h2>About Our Platform</h2>
    <p>This platform provides access to validated bioinformatics pipelines.</p>
    <h3>Available Workflows</h3>
    <ul>
      <li>Quality Control</li>
      <li>Variant Calling</li>
      <li>RNA-Seq Analysis</li>
    </ul>
  
  # Terms of service
  terms: |
    <h2>Terms of Service</h2>
    <p>By using this service, you agree to the following terms...</p>
```

### Navigation Bar

Configure the navigation bar:

```yaml
navbar:
  - title: "Home"
    url: "/"
    icon: "fas fa-home"
    order: 1
    visible: true
    description: "Home page"
    
  - title: "Workflows"
    url: "/workflows"
    icon: "fas fa-project-diagram"
    order: 2
    visible: true
    description: "Available workflows"
    
  - title: "My Jobs"
    url: "/jobs"
    icon: "fas fa-tasks"
    order: 3
    visible: true
    description: "Job management"
    
  - title: "Help"
    url: "/help"
    icon: "fas fa-question-circle"
    order: 4
    visible: true
    description: "Help and documentation"
    
  - title: "Admin"
    url: "/admin"
    icon: "fas fa-cog"
    order: 5
    visible: true
    admin_only: true
    description: "Administrative functions"
```

### Custom CSS and JavaScript

Add custom styling and behavior:

**In templates**:
```html
<!-- Custom CSS -->
<style>
.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 60px 0;
  text-align: center;
}

.workflow-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin: 10px 0;
  transition: box-shadow 0.3s ease;
}

.workflow-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
</style>

<!-- Custom JavaScript -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Auto-refresh job status every 30 seconds
    setInterval(function() {
        if (window.location.pathname.includes('/jobs/')) {
            location.reload();
        }
    }, 30000);
});
</script>
```

---

## Performance Tuning

### Database Optimization

**PostgreSQL Settings**:
```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
```

**Database Indexes**:
```python
# Add indexes in Django models
class Job(models.Model):
    # ... fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['workflow', 'created_at']),
        ]
```

### Redis Configuration

**Redis Settings** (`redis.conf`):
```
# Memory optimization
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Network
timeout 300
tcp-keepalive 60
```

### Celery Optimization

**Worker Configuration**:
```bash
# Production worker command
celery -A cloudgene_django worker \
  --concurrency=4 \
  --prefetch-multiplier=1 \
  --max-tasks-per-child=1000 \
  --time-limit=3600 \
  --soft-time-limit=3000 \
  --loglevel=info
```

**Celery Settings**:
```python
# settings.py
CELERY_TASK_ROUTES = {
    'jobs.tasks.execute_workflow': {'queue': 'workflow'},
    'jobs.tasks.cleanup_old_jobs': {'queue': 'maintenance'},
}

CELERY_TASK_TIME_LIMIT = 3600  # 1 hour
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
```

### File System Optimization

**Storage Configuration**:
```python
# Use separate storage for different file types
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": "/var/cloudgene/media",
        },
    },
    "workflows": {
        "BACKEND": "django.core.files.storage.FileSystemStorage", 
        "OPTIONS": {
            "location": "/var/cloudgene/workflows",
        },
    },
    "jobs": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": "/var/cloudgene/jobs",
        },
    },
}
```

**File Cleanup**:
```python
# Automated cleanup task
@periodic_task(run_every=crontab(hour=2, minute=0))
def cleanup_old_files():
    """Clean up old job files"""
    from datetime import timedelta
    from django.utils import timezone
    
    cutoff = timezone.now() - timedelta(days=30)
    old_jobs = Job.objects.filter(
        created_at__lt=cutoff,
        status__in=['completed', 'failed']
    )
    
    for job in old_jobs:
        job.cleanup_files()
        job.delete()
```

---

## Troubleshooting

### Common Issues

**1. Jobs Stuck in Pending State**
```bash
# Check Celery worker status
celery -A cloudgene_django inspect active

# Restart workers if needed
pkill -f "celery worker"
celery -A cloudgene_django worker --detach

# Check Redis connection
redis-cli ping
```

**2. Database Connection Errors**
```bash
# Check database status
systemctl status postgresql

# Test connection
psql -h localhost -U cloudgene_user -d cloudgene

# Run migrations if needed
python manage.py migrate
```

**3. Nextflow Execution Failures**
```bash
# Check Nextflow installation
nextflow -version

# Test Nextflow execution
nextflow run hello

# Check work directory permissions
ls -la /tmp/nextflow-work
```

**4. Email Not Sending**
```python
# Test email configuration
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

### Log Analysis

**Django Logs**:
```python
# Enable debug logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/cloudgene/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'cloudgene': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

**Celery Logs**:
```bash
# View Celery logs
tail -f /var/log/cloudgene/celery.log

# Monitor specific task
celery -A cloudgene_django events
```

**Nextflow Logs**:
```bash
# Check Nextflow logs in job directory
ls -la /var/cloudgene/jobs/{job_id}/.nextflow/

# View execution report
cat /var/cloudgene/jobs/{job_id}/.nextflow/log
```

### Performance Monitoring

**System Monitoring**:
```bash
# Monitor system resources
htop
iostat -x 1
free -h

# Monitor database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Monitor Redis memory usage
redis-cli info memory
```

**Application Monitoring**:
```python
# Add monitoring middleware
class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        if duration > 1.0:  # Log slow requests
            logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
            
        return response
```

### Backup and Recovery

**Database Backup**:
```bash
# PostgreSQL backup
pg_dump -h localhost -U cloudgene_user cloudgene > backup.sql

# Restore
psql -h localhost -U cloudgene_user cloudgene < backup.sql
```

**File Backup**:
```bash
# Backup job files and workflows
tar -czf cloudgene-files-$(date +%Y%m%d).tar.gz \
  /var/cloudgene/jobs \
  /var/cloudgene/workflows \
  /var/cloudgene/media
```

**Configuration Backup**:
```bash
# Backup configuration
cp cloudgene_config.yaml cloudgene_config.yaml.backup
cp cloudgene_django/settings.py settings.py.backup
```

---

This documentation covers all major configuration aspects of the Cloudgene Django server. For workflow-specific configuration, see the [Workflow YAML Reference](WORKFLOW_YAML_REFERENCE.md).