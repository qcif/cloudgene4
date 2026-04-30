# Cloudgene Django Rebuild

This project rebuilds the original Java Cloudgene application as a modern Django web application with Python.

## Features

### Core Functionality
- ✅ **User Authentication & Group Management**: Custom user model with group-based workflow access control
- ✅ **Workflow Management**: YAML-based workflow configuration with dynamic parameter handling  
- ✅ **Job Queue System**: Celery-based job execution with Redis backend
- ✅ **Nextflow Integration**: Execute Nextflow workflows with parameter substitution
- ✅ **Admin Panel**: Comprehensive admin interface for server settings, users, workflows, and jobs
- ✅ **Real-time Updates**: WebSocket support for live job status updates
- ✅ **File Downloads**: Secure job result downloads with expiration

### API Features
- RESTful API with Django REST Framework
- Token-based authentication
- Comprehensive job management endpoints
- Workflow browsing and submission
- Admin dashboard with statistics

### Bug Fixes Addressed
- ✅ **Space Handling in Job Names**: Job names with spaces are automatically sanitized
- ✅ **Improved Queue Logic**: Robust job queue management to prevent stuck jobs
- ✅ **User Deduplication**: Enhanced user registration to prevent duplicate accounts

## Architecture

```
cloudgene_django/           # Main Django project
├── accounts/               # User authentication and management
├── workflows/              # Workflow configuration and management  
├── jobs/                   # Job execution and queue management
├── admin_panel/            # Admin interface and system settings
├── cloudgene_config.yaml   # Main configuration file
└── sample_workflow.yaml    # Example workflow definition
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- Redis server (for Celery and Channels)
- Nextflow (for workflow execution)

### Quick Start
1. **Set up the environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Initialize the database:**
   ```bash
   python manage.py migrate
   python manage.py setup_cloudgene
   ```

3. **Start Redis (required for Celery and WebSockets):**
   ```bash
   redis-server
   ```

4. **Start Celery worker (in a separate terminal):**
   ```bash
   source venv/bin/activate
   celery -A cloudgene_django worker --loglevel=info
   ```

5. **Start Django development server:**
   ```bash
   python manage.py runserver
   ```

## Configuration

### Main Configuration (`cloudgene_config.yaml`)
```yaml
server:
  name: "Cloudgene Django Server"
  port: 8000
  max_jobs: 10
  
nextflow:
  binary: "nextflow"
  work_dir: "/tmp/nextflow-work"
  
queue:
  max_concurrent_jobs: 10
  job_timeout: 86400
```

### Workflow Configuration Example
```yaml
id: example-workflow
name: Example Workflow
description: A sample bioinformatics workflow
category: analysis

workflow:
  steps:
    - name: ProcessData
      classname: workflows.steps.DataProcessor
      
  inputs:
    - id: input_file
      description: Input data file
      type: file
      required: true
      
  outputs:
    - id: results
      description: Analysis results
      type: folder
      download: true
```

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout  
- `POST /api/auth/register/` - User registration
- `GET /api/auth/token/` - Get API token

### Jobs
- `GET /api/jobs/` - List jobs
- `POST /api/jobs/` - Submit new job
- `GET /api/jobs/{id}/` - Get job details
- `POST /api/jobs/{id}/cancel/` - Cancel job
- `POST /api/jobs/{id}/restart/` - Restart job
- `GET /api/jobs/{id}/logs/` - Get job logs
- `GET /api/jobs/{id}/download/` - List downloadable files

### Workflows
- `GET /api/workflows/` - List available workflows
- `GET /api/workflows/{id}/` - Get workflow details
- `GET /api/categories/` - List workflow categories

### Admin (Admin users only)
- `GET /api/admin/dashboard/` - Admin dashboard
- `GET/POST /api/admin/server-settings/` - Server settings
- `GET/POST /api/admin/templates/` - Page templates
- `GET /api/admin/system-logs/` - System logs
- `GET /api/admin/counters/` - System counters

## WebSocket Endpoints

### Job Status Updates
```javascript
ws://localhost:8000/ws/jobs/{job_id}/
```

Receives real-time job status updates:
```json
{
  "type": "job_status",
  "job_id": "uuid",
  "status": "running",
  "progress": 50,
  "message": "Processing step 2 of 4"
}
```

## Usage Examples

### Submit a Job via API
```bash
curl -X POST http://localhost:8000/api/jobs/ \
  -H "Authorization: Token your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "hello-cloudgene",
    "name": "test_job",
    "parameters": {
      "input_text": "Hello World",
      "number_input": 42
    }
  }'
```

### Load a Custom Workflow
```bash
python manage.py load_sample_workflow --file /path/to/workflow.yaml
```

## Development

### Running Tests
```bash
python manage.py test
```

### Code Structure
- **Models**: Django ORM models for data persistence
- **Serializers**: DRF serializers for API data formatting
- **Views**: API views and business logic
- **Tasks**: Celery tasks for background job processing
- **Consumers**: WebSocket consumers for real-time updates

### Key Components
1. **Job Queue** (`jobs/queue.py`): Manages job execution and prioritization
2. **Config Loader** (`workflows/config_loader.py`): Handles YAML workflow definitions
3. **Task Executor** (`jobs/tasks.py`): Executes workflows using Nextflow
4. **WebSocket Consumer** (`jobs/consumers.py`): Provides real-time job updates

## Deployment

### Production Considerations
- Use PostgreSQL instead of SQLite for production
- Set up proper Redis configuration
- Use a reverse proxy (nginx) for static files
- Configure Celery with proper monitoring
- Set up log rotation and monitoring
- Use environment variables for sensitive settings

### Environment Variables
```bash
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:pass@localhost/cloudgene
REDIS_URL=redis://localhost:6379/0
```

## Comparison with Original Java Version

| Feature | Java Cloudgene | Django Cloudgene | Status |
|---------|----------------|------------------|---------|
| User Management | ✅ | ✅ | Improved with proper validation |
| Workflow Config | ✅ | ✅ | Enhanced YAML processing |
| Job Queue | ✅ | ✅ | More robust with Celery |
| Admin Panel | ✅ | ✅ | RESTful API + better UX |
| Real-time Updates | ✅ | ✅ | WebSocket-based |
| Nextflow Support | ✅ | ✅ | Full compatibility |
| Bug Fixes | ❌ | ✅ | Space handling, queue logic, user deduplication |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality  
5. Submit a pull request

## License

This project maintains compatibility with the original Cloudgene license terms.