"""
Workflow management views
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Workflow, WorkflowCategory
from .serializers import WorkflowSerializer, WorkflowCategorySerializer


class WorkflowViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing workflows
    """
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Workflow.objects.filter(status='enabled')
        
        # Filter workflows user can access
        if not user.is_admin_user():
            queryset = queryset.filter(
                Q(public=True) | 
                Q(allowed_groups__in=user.groups.all())
            ).distinct()
        
        # Filter by category if requested
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        
        return queryset.order_by('name')


class WorkflowCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for workflow categories
    """
    queryset = WorkflowCategory.objects.all()
    serializer_class = WorkflowCategorySerializer
    permission_classes = [IsAuthenticated]
