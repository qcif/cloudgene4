"""
Admin panel views
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.contrib.auth import get_user_model

from .models import ServerSettings, Template, NavbarItem, SystemLog, Counter
from .serializers import (
    ServerSettingsSerializer, TemplateSerializer, NavbarItemSerializer,
    SystemLogSerializer, CounterSerializer
)
from jobs.models import Job
from workflows.models import Workflow

User = get_user_model()


class IsAdminUser(permissions.BasePermission):
    """
    Permission class that only allows admin users
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin_user()


class ServerSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for server settings management
    """
    queryset = ServerSettings.objects.all()
    serializer_class = ServerSettingsSerializer
    permission_classes = [IsAdminUser]


class TemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for template management
    """
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [IsAdminUser]


class NavbarItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for navbar item management
    """
    queryset = NavbarItem.objects.all()
    serializer_class = NavbarItemSerializer
    permission_classes = [IsAdminUser]


class SystemLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for system log viewing
    """
    queryset = SystemLog.objects.all()
    serializer_class = SystemLogSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = SystemLog.objects.all()
        
        # Filter by level if requested
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        # Filter by component if requested
        component = self.request.query_params.get('component')
        if component:
            queryset = queryset.filter(component=component)
        
        return queryset.order_by('-timestamp')


class CounterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for counter viewing
    """
    queryset = Counter.objects.all()
    serializer_class = CounterSerializer
    permission_classes = [IsAdminUser]


class AdminDashboardView(APIView):
    """
    Admin dashboard with statistics
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Get job statistics
        job_stats = Job.objects.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            running=Count('id', filter=Q(status='running')),
            completed=Count('id', filter=Q(status='completed')),
            failed=Count('id', filter=Q(status='failed')),
            cancelled=Count('id', filter=Q(status='cancelled'))
        )
        
        # Get user statistics
        user_stats = User.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            staff=Count('id', filter=Q(is_staff=True))
        )
        
        # Get workflow statistics
        workflow_stats = Workflow.objects.aggregate(
            total=Count('id'),
            enabled=Count('id', filter=Q(status='enabled')),
            disabled=Count('id', filter=Q(status='disabled'))
        )
        
        # Get recent jobs
        recent_jobs = Job.objects.select_related('workflow', 'user').order_by(
            '-submitted_at'
        )[:10]
        
        from jobs.serializers import JobListSerializer
        recent_jobs_data = JobListSerializer(recent_jobs, many=True).data
        
        # Get system logs
        recent_logs = SystemLog.objects.order_by('-timestamp')[:10]
        recent_logs_data = SystemLogSerializer(recent_logs, many=True).data
        
        return Response({
            'statistics': {
                'jobs': job_stats,
                'users': user_stats,
                'workflows': workflow_stats
            },
            'recent_jobs': recent_jobs_data,
            'recent_logs': recent_logs_data
        })
