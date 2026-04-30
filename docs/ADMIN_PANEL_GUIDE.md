# Cloudgene Admin Panel User Guide

This guide provides comprehensive information about using the Cloudgene administrative interface to manage your server, users, workflows, and jobs.

## Table of Contents

1. [Accessing the Admin Panel](#accessing-the-admin-panel)
2. [Dashboard Overview](#dashboard-overview)
3. [User Management](#user-management)
4. [Workflow Management](#workflow-management)
5. [Job Management](#job-management)
6. [Server Settings](#server-settings)
7. [Templates and UI Customization](#templates-and-ui-customization)
8. [System Monitoring](#system-monitoring)
9. [Queue Management](#queue-management)
10. [Email Configuration](#email-configuration)
11. [Security Settings](#security-settings)
12. [Backup and Maintenance](#backup-and-maintenance)
13. [API Management](#api-management)
14. [Troubleshooting](#troubleshooting)

---

## Accessing the Admin Panel

### Requirements

To access the admin panel, you must have administrative privileges:

1. **Superuser Account**: Created during initial setup
2. **Admin Group Membership**: Regular users added to the 'admin' group
3. **Staff Status**: Users with `is_staff = True`

### Login Process

1. Navigate to your Cloudgene server URL
2. Click **"Admin"** in the navigation bar (visible only to admin users)
3. Enter your administrative credentials
4. You'll be redirected to the admin dashboard

### Alternative Access

Direct URL access: `https://your-server.com/admin/`

---

## Dashboard Overview

The admin dashboard provides a comprehensive overview of your Cloudgene server status and quick access to management functions.

### Main Dashboard Sections

**1. System Status**
- Server uptime and version information
- Current system load and resource usage
- Active jobs and queue status
- Recent system events and alerts

**2. Quick Statistics**
- Total registered users
- Active workflows
- Jobs executed (today/this month/total)
- Storage usage

**3. Recent Activity**
- Latest user registrations
- Recent job submissions
- System log entries
- Failed operations requiring attention

**4. Quick Actions**
- Add new user
- Upload workflow
- View job queue
- Check system logs

### Navigation Menu

The admin panel includes the following main sections:

- **Dashboard**: Overview and statistics
- **Users**: User account management
- **Workflows**: Workflow definitions and categories
- **Jobs**: Job monitoring and management
- **Settings**: Server configuration
- **Templates**: HTML content management
- **Logs**: System logs and events
- **Queue**: Job queue management

---

## User Management

### User List View

Access: **Admin Panel → Users → All Users**

**Features:**
- Search users by username, email, or full name
- Filter by user status (active/inactive)
- Filter by user groups
- Bulk operations (activate/deactivate users)
- Export user list to CSV

**User Information Displayed:**
- Username and email
- Full name
- Registration date
- Last login
- Account status (active/inactive)
- Group memberships
- Job count

### Creating New Users

**Manual User Creation:**

1. Go to **Users → Add User**
2. Fill in required information:
   - Username (4+ characters, alphanumeric)
   - Email address
   - Full name
   - Password (6+ chars with numbers and mixed case)
3. Set initial groups and permissions
4. Choose whether to send activation email
5. Click **"Save"** to create user

**Bulk User Import:**

1. Go to **Users → Import Users**
2. Download the CSV template
3. Fill in user information following the template format:
   ```csv
   username,email,full_name,groups
   user1,user1@example.com,User One,"bioinformatics,genomics"
   user2,user2@example.com,User Two,"admin"
   ```
4. Upload the CSV file
5. Review import preview
6. Confirm import

### Editing User Accounts

**Basic Information:**
- Update username, email, full name
- Change password (with validation)
- Modify account status (active/inactive)

**Groups and Permissions:**
- Add/remove group memberships
- Grant/revoke admin privileges
- Set staff status

**Account Settings:**
- Reset password and send email
- Force password change on next login
- Set account expiration date
- Configure API access

### Group Management

**Creating Groups:**

1. Go to **Users → Groups → Add Group**
2. Enter group name and description
3. Set default permissions for the group
4. Save the group

**Managing Group Membership:**

- **Individual Assignment**: Edit user and add/remove groups
- **Bulk Assignment**: Select multiple users and assign to groups
- **Group-based Workflow Access**: Configure which workflows are accessible to each group

**Built-in Groups:**
- `admin`: Administrative privileges
- `bioinformatics`: General bioinformatics workflows
- `genomics`: Genomics-specific workflows
- `proteomics`: Proteomics workflows

### User Activity Monitoring

**Login Activity:**
- View login history for each user
- Monitor failed login attempts
- Track session duration and activity

**Job Activity:**
- View jobs submitted by each user
- Monitor resource usage patterns
- Generate usage reports

**API Usage:**
- Track API token usage
- Monitor API call frequency
- View API error rates

---

## Workflow Management

### Workflow Overview

Access: **Admin Panel → Workflows → All Workflows**

**Workflow List Features:**
- View all registered workflows
- Search by name, ID, or category
- Filter by status (enabled/disabled)
- Filter by access level (public/private)
- Sort by creation date, usage, or popularity

### Adding New Workflows

**Method 1: YAML Upload**

1. Go to **Workflows → Add Workflow → Upload YAML**
2. Select your workflow YAML file
3. The system will:
   - Validate the YAML syntax
   - Check for required fields
   - Validate parameter definitions
   - Create the workflow record
4. Configure access permissions
5. Test the workflow

**Method 2: Manual Creation**

1. Go to **Workflows → Add Workflow → Manual**
2. Fill in basic information:
   - Workflow ID (unique identifier)
   - Name and description
   - Version and category
3. Add input parameters:
   - Parameter ID, type, and description
   - Default values and validation rules
   - Required/optional status
4. Add output parameters:
   - Output ID, type, and description
   - Download and temporary file settings
5. Configure workflow steps:
   - Step name and implementation class
   - Parameter mappings
   - Execution order
6. Set access control:
   - Public vs. group-restricted access
   - Allowed groups
   - Admin-only parameters

### Workflow Configuration

**Basic Settings:**
- Enable/disable workflow
- Update description and documentation
- Modify version information
- Change category assignment

**Access Control:**
- Set public access (available to all authenticated users)
- Configure group-based access restrictions
- Define admin-only parameters
- Set user quotas and limits

**Parameter Management:**
- Add/remove input parameters
- Modify parameter types and validation
- Update default values
- Configure conditional parameters

**Resource Requirements:**
- Set minimum/maximum CPU and memory
- Configure execution time limits
- Define storage requirements
- Set priority levels

### Workflow Categories

**Managing Categories:**

1. Go to **Workflows → Categories**
2. Create new categories:
   - Category name and description
   - Icon and color coding
   - Default access permissions
3. Organize workflows by category
4. Set category-specific settings

**Default Categories:**
- `bioinformatics`: General bioinformatics tools
- `genomics`: Genome analysis workflows
- `transcriptomics`: RNA-seq and gene expression
- `proteomics`: Protein analysis workflows
- `quality-control`: Data QC and validation
- `statistics`: Statistical analysis tools

### Workflow Testing

**Test Mode:**
- Enable test mode for new workflows
- Run validation checks
- Test with sample data
- Monitor execution logs
- Verify output generation

**Deployment:**
- Move from test to production
- Update workflow documentation
- Notify users of new workflows
- Monitor initial usage

---

## Job Management

### Job Queue Overview

Access: **Admin Panel → Jobs → Job Queue**

**Queue Status Display:**
- Currently running jobs
- Pending jobs in queue
- Recently completed jobs
- Failed jobs requiring attention

**Queue Management Actions:**
- Pause/resume job execution
- Reorder jobs by priority
- Cancel pending or running jobs
- View detailed job logs

### Job Monitoring

**Real-time Monitoring:**
- Live job status updates
- Resource usage monitoring
- Progress tracking
- Error detection and alerting

**Job Details View:**
- Job parameters and input files
- Execution timeline
- Resource consumption
- Output files and logs
- Error messages and debugging info

### Job Operations

**Individual Job Management:**

1. **View Job Details**: Click on job ID to see comprehensive information
2. **Cancel Job**: Stop a running or pending job
3. **Restart Job**: Resubmit a failed job with same parameters
4. **Download Results**: Access job outputs and logs
5. **Delete Job**: Remove job and associated files

**Bulk Operations:**
- Select multiple jobs for bulk operations
- Cancel multiple pending jobs
- Delete completed jobs older than specified date
- Export job statistics to CSV

### Job Status Management

**Job States:**
- `pending`: Waiting in queue
- `running`: Currently executing
- `completed`: Finished successfully
- `failed`: Execution failed
- `cancelled`: Cancelled by user or admin
- `error`: System error occurred

**Status Transitions:**
- Monitor normal state transitions
- Identify stuck jobs
- Handle error conditions
- Manage job restarts

### Resource Usage Analysis

**System Resources:**
- CPU usage per job
- Memory consumption
- Disk I/O patterns
- Network usage

**User Resource Patterns:**
- Resource usage by user
- Popular workflows and resource requirements
- Peak usage times
- Resource allocation efficiency

### Job Queue Configuration

**Queue Settings:**
- Maximum concurrent jobs
- Job timeout limits
- Priority calculation rules
- Resource allocation policies

**User Quotas:**
- Jobs per user limits
- Resource usage quotas
- Storage limitations
- Priority levels

---

## Server Settings

### General Settings

Access: **Admin Panel → Settings → General**

**Basic Configuration:**
- Server name and description
- Contact information
- Time zone settings
- Default language
- Maintenance mode

**Example Configuration:**
```
Server Name: Lab Bioinformatics Server
Description: Computational biology pipeline server
Contact Email: admin@lab.edu
Time Zone: America/New_York
Maintenance Mode: Disabled
```

### System Settings

**Performance Configuration:**
- Maximum concurrent jobs
- Job timeout settings
- Memory and CPU limits
- Temporary file cleanup intervals

**Storage Configuration:**
- Data directory paths
- Storage quotas per user
- File retention policies
- Backup schedules

**Security Settings:**
- Session timeout duration
- Password complexity requirements
- Login attempt limits
- API rate limiting

### Nextflow Configuration

**Basic Nextflow Settings:**
- Nextflow binary path
- Default working directory
- Configuration file location
- Environment variables

**Execution Profiles:**
- Local execution settings
- Cluster configuration (SLURM, PBS, etc.)
- Cloud execution (AWS, Azure, GCP)
- Container settings (Docker, Singularity)

**Resource Defaults:**
- Default CPU and memory allocations
- Maximum resource limits
- Queue configuration
- Priority settings

### Database Configuration

**Database Settings:**
- Connection parameters
- Performance optimization
- Backup configuration
- Maintenance schedules

**Monitoring:**
- Connection pool status
- Query performance
- Storage usage
- Index optimization

---

## Templates and UI Customization

### Page Templates

Access: **Admin Panel → Templates → Page Templates**

**Available Templates:**
- **Home Page**: Welcome content and navigation
- **Footer**: Site footer with links and information
- **About Page**: Organization and project information
- **Help Page**: User documentation and support
- **Terms of Service**: Legal terms and conditions
- **Privacy Policy**: Data handling and privacy information

### Email Templates

**System Emails:**
- **Welcome Email**: New user account creation
- **Activation Email**: Account activation instructions
- **Password Reset**: Password reset instructions
- **Job Notification**: Job completion/failure notifications
- **System Alerts**: Administrative notifications

**Template Variables:**
- `{{user.username}}`: User's username
- `{{user.full_name}}`: User's full name
- `{{user.email}}`: User's email address
- `{{job.name}}`: Job name
- `{{job.status}}`: Job status
- `{{server.name}}`: Server name
- `{{server.url}}`: Server URL

### Template Editor

**Features:**
- Rich text editor with HTML support
- Syntax highlighting
- Live preview
- Template variable assistance
- Version history

**Example Home Page Template:**
```html
<div class="hero-section">
  <h1>Welcome to {{server.name}}</h1>
  <p>Execute bioinformatics workflows with ease</p>
  
  <div class="features">
    <h3>Available Tools</h3>
    <ul>
      <li>Quality Control Analysis</li>
      <li>RNA-Seq Pipeline</li>
      <li>Variant Calling</li>
      <li>Differential Expression</li>
    </ul>
  </div>
  
  <a href="/workflows" class="btn btn-primary">Browse Workflows</a>
</div>
```

### Navigation Customization

**Navigation Bar Items:**
- Add custom menu items
- Reorder navigation elements
- Set visibility by user group
- Configure external links

**Example Navigation Configuration:**
```
Home: / (Order: 1, Visible: All)
Workflows: /workflows (Order: 2, Visible: All)
Jobs: /jobs (Order: 3, Visible: Authenticated)
Documentation: /docs (Order: 4, Visible: All)
Admin: /admin (Order: 5, Visible: Admin Only)
```

### CSS and Styling

**Custom Styles:**
- Upload custom CSS files
- Override default theme colors
- Customize layout and fonts
- Add organization branding

**Example Custom CSS:**
```css
/* Custom header styling */
.site-header {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    border-bottom: 3px solid #1e3c72;
}

/* Workflow card styling */
.workflow-card {
    border: 1px solid #e1e5e9;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: transform 0.2s ease;
}

.workflow-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}
```

---

## System Monitoring

### Real-time Monitoring

Access: **Admin Panel → Monitoring → System Status**

**System Metrics:**
- CPU usage and load average
- Memory utilization
- Disk space usage
- Network I/O
- Active processes

**Service Status:**
- Django application server
- Database connection
- Redis/Celery workers
- Nextflow execution
- Background tasks

### Log Management

**System Logs:**
- Application logs (Django)
- Job execution logs
- Error logs
- Security events
- Performance metrics

**Log Levels:**
- `DEBUG`: Detailed debugging information
- `INFO`: General information messages
- `WARNING`: Warning messages
- `ERROR`: Error conditions
- `CRITICAL`: Critical system failures

**Log Filtering and Search:**
- Filter by date range
- Search by component or user
- Filter by log level
- Export logs for analysis

### Alerts and Notifications

**Alert Configuration:**
- Set thresholds for system metrics
- Configure notification recipients
- Define alert escalation rules
- Set maintenance windows

**Alert Types:**
- High CPU or memory usage
- Disk space running low
- Job queue backing up
- System errors or failures
- Security events

**Notification Methods:**
- Email notifications
- Slack integration
- SMS alerts (with third-party service)
- Dashboard notifications

### Performance Analytics

**Usage Statistics:**
- User activity patterns
- Popular workflows
- Resource utilization trends
- Peak usage times

**Performance Metrics:**
- Average job execution times
- System response times
- Database query performance
- File I/O patterns

**Reporting:**
- Generate monthly usage reports
- Export statistics for analysis
- Create custom dashboards
- Schedule automated reports

---

## Queue Management

### Queue Configuration

Access: **Admin Panel → Jobs → Queue Configuration**

**Basic Queue Settings:**
- Maximum concurrent jobs
- Queue size limits
- Job timeout settings
- Priority calculation rules

**Resource Management:**
- CPU and memory allocation
- Disk space management
- Network bandwidth limits
- Temporary file cleanup

### Priority Management

**Priority Levels:**
- **High (100)**: Admin users and critical jobs
- **Medium (50)**: Premium users and important jobs
- **Low (10)**: Standard users and regular jobs

**Priority Factors:**
- User type (admin, premium, standard)
- Workflow complexity and duration
- Resource requirements
- Job submission time
- User's historical resource usage

### Queue Monitoring

**Real-time Queue Status:**
- Jobs currently running
- Jobs pending in queue
- Average wait time
- Resource utilization

**Queue Health Metrics:**
- Queue throughput
- Average job duration
- Success/failure rates
- Resource efficiency

### Queue Operations

**Manual Queue Management:**
- Pause/resume job processing
- Reorder pending jobs
- Cancel jobs in queue
- Force job execution

**Automated Policies:**
- Job timeout handling
- Failed job retry logic
- Queue cleanup procedures
- Resource balancing

---

## Email Configuration

### SMTP Settings

Access: **Admin Panel → Settings → Email Configuration**

**Basic SMTP Configuration:**
- SMTP server hostname
- Port number (587 for TLS, 465 for SSL)
- Username and password
- Encryption method (TLS/SSL)

**Provider-Specific Settings:**

**Gmail:**
```
SMTP Host: smtp.gmail.com
SMTP Port: 587
Use TLS: Yes
Username: your-email@gmail.com
Password: [App-specific password]
```

**Office 365:**
```
SMTP Host: smtp.office365.com
SMTP Port: 587
Use TLS: Yes
Username: your-email@company.com
Password: [Your password]
```

### Email Templates

**System Email Types:**
- Account activation
- Password reset
- Job completion notifications
- System alerts
- Welcome messages

**Template Customization:**
- Modify email subject lines
- Customize email content
- Add organization branding
- Include dynamic content

### Email Testing

**Test Configuration:**
1. Go to **Settings → Email → Test**
2. Enter test recipient email
3. Select test email type
4. Send test email
5. Verify delivery and formatting

**Troubleshooting Email Issues:**
- Check SMTP credentials
- Verify firewall settings
- Test with different email providers
- Review email logs for errors

---

## Security Settings

### Authentication Configuration

**Password Policies:**
- Minimum password length
- Character requirements
- Password history
- Expiration settings

**Session Management:**
- Session timeout duration
- Concurrent session limits
- Secure cookie settings
- Session cleanup

**Two-Factor Authentication:**
- Enable 2FA for admin accounts
- Configure TOTP settings
- Backup code generation
- Recovery procedures

### Access Control

**User Permissions:**
- Role-based access control
- Group-based permissions
- Workflow access restrictions
- Administrative privileges

**API Security:**
- API token management
- Rate limiting
- IP address restrictions
- Request logging

### Security Monitoring

**Security Events:**
- Failed login attempts
- Unauthorized access attempts
- Permission escalation attempts
- Suspicious activity patterns

**Audit Logging:**
- User actions and changes
- Administrative operations
- System configuration changes
- Data access patterns

### Data Protection

**Data Encryption:**
- Database encryption at rest
- File system encryption
- SSL/TLS for data in transit
- Secure key management

**Privacy Controls:**
- User data handling
- Data retention policies
- Export/deletion procedures
- Compliance reporting

---

## Backup and Maintenance

### Backup Configuration

**Database Backups:**
- Automated daily backups
- Backup retention policies
- Backup verification
- Disaster recovery procedures

**File System Backups:**
- User data and workflow files
- System configuration files
- Log files and histories
- Application code backups

### Maintenance Tasks

**Regular Maintenance:**
- Database optimization
- Log file rotation
- Temporary file cleanup
- Index rebuilding

**System Updates:**
- Django framework updates
- Security patch management
- Dependency updates
- System monitoring

### System Health Checks

**Automated Checks:**
- Database connectivity
- File system integrity
- Service availability
- Resource utilization

**Health Monitoring:**
- System performance metrics
- Error rate monitoring
- Response time tracking
- Resource usage trends

---

## API Management

### API Configuration

Access: **Admin Panel → Settings → API**

**API Settings:**
- Enable/disable API access
- Rate limiting configuration
- Authentication methods
- API versioning

### API Token Management

**Token Administration:**
- View all active API tokens
- Revoke user tokens
- Set token expiration
- Monitor token usage

**Token Permissions:**
- Read-only access
- Job submission privileges
- Administrative operations
- Workflow management

### API Monitoring

**Usage Statistics:**
- API calls per user
- Popular API endpoints
- Error rates and types
- Performance metrics

**Rate Limiting:**
- Configure API rate limits
- Monitor limit violations
- Set user-specific limits
- Handle rate limit exceeded

---

## Troubleshooting

### Common Issues

**1. Users Cannot Log In**
- Check user account status (active/inactive)
- Verify password requirements
- Review failed login logs
- Check group memberships

**2. Jobs Stuck in Queue**
- Verify Celery workers are running
- Check Redis connectivity
- Review job queue configuration
- Monitor system resources

**3. Workflows Not Loading**
- Validate YAML syntax
- Check file permissions
- Review workflow configuration
- Verify required parameters

**4. Email Not Sending**
- Test SMTP configuration
- Check email template settings
- Review email logs
- Verify firewall settings

### Diagnostic Tools

**System Information:**
- View system status dashboard
- Check service connectivity
- Monitor resource usage
- Review error logs

**Configuration Validation:**
- Validate workflow YAML files
- Test email configuration
- Verify database settings
- Check file permissions

### Getting Help

**Documentation:**
- Admin configuration guide
- Workflow YAML reference
- API documentation
- Best practices guide

**Support Resources:**
- System logs and diagnostics
- Error reporting
- Community forums
- Professional support options

---

This comprehensive admin panel guide covers all aspects of managing your Cloudgene Django server. For detailed configuration options, refer to the [Admin Configuration Guide](ADMIN_CONFIGURATION.md) and [Workflow YAML Reference](WORKFLOW_YAML_REFERENCE.md).