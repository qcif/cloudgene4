"""
Workflow management views
"""
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from .models import Workflow, WorkflowCategory
from .serializers import WorkflowSerializer, WorkflowCategorySerializer, WorkflowSettingsSerializer


class WorkflowViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing workflows.
    Unauthenticated users see only public workflows.
    Authenticated users also see workflows for their groups.
    Admins see all enabled workflows.
    """
    serializer_class = WorkflowSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = self.request.user
        queryset = Workflow.objects.filter(status='enabled')

        if user is None or not user.is_authenticated:
            queryset = queryset.filter(public=True)
        elif not user.is_admin_user():
            queryset = queryset.filter(
                Q(public=True) |
                Q(allowed_groups__in=user.groups.all())
            ).distinct()

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name=category)

        return queryset.order_by('name')


class WorkflowCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowCategory.objects.all()
    serializer_class = WorkflowCategorySerializer
    permission_classes = [AllowAny]


class WorkflowAdminViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing workflow settings
    """
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSettingsSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['get', 'patch'], url_path='settings')
    def settings(self, request, pk=None):
        """
        Get or update workflow settings including Nextflow configuration
        """
        workflow = self.get_object()
        
        if request.method == 'GET':
            serializer = self.get_serializer(workflow)
            return Response(serializer.data)
        
        elif request.method == 'PATCH':
            serializer = self.get_serializer(workflow, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)
