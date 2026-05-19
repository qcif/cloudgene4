"""
Serializers for workflow-related API endpoints
"""
from rest_framework import serializers
from .models import Workflow, WorkflowCategory, WorkflowParameter


class WorkflowCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowCategory
        fields = ['id', 'name', 'description', 'created_at']


class WorkflowParameterSerializer(serializers.ModelSerializer):
    # Frontend compatibility fields
    id = serializers.CharField(source='parameter_id', read_only=True)
    type = serializers.CharField(source='parameter_type', read_only=True)
    label = serializers.CharField(source='name', read_only=True)
    value = serializers.CharField(source='default_value', read_only=True)
    
    class Meta:
        model = WorkflowParameter
        fields = ['parameter_id', 'name', 'description', 'parameter_type', 
                 'required', 'default_value', 'values', 'is_input', 'is_output', 'order',
                 'id', 'type', 'label', 'value']


class WorkflowSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    parameters = WorkflowParameterSerializer(many=True, read_only=True)
    inputs = serializers.SerializerMethodField()
    outputs = serializers.SerializerMethodField()
    allowed_groups = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Workflow
        fields = ['id', 'name', 'description', 'version', 'website', 'category_name',
                 'status', 'public', 'created_at', 'updated_at', 'parameters', 'inputs', 'outputs', 'allowed_groups',
                 'nextflow_profile', 'working_directory', 'env_vars', 'nextflow_config']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_inputs(self, obj):
        """Get input parameters only"""
        return WorkflowParameterSerializer(
            obj.parameters.filter(is_input=True),
            many=True
        ).data
    
    def get_outputs(self, obj):
        """Get output parameters only"""
        return WorkflowParameterSerializer(
            obj.parameters.filter(is_output=True),
            many=True
        ).data


class WorkflowSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for admin workflow settings, including Nextflow configuration
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    allowed_groups = serializers.StringRelatedField(many=True, read_only=True)
    allowed_group_names = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False,
        help_text="List of group names to assign to this workflow"
    )
    
    class Meta:
        model = Workflow
        fields = ['id', 'name', 'description', 'version', 'website', 'category_name',
                 'status', 'public', 'created_at', 'updated_at', 'allowed_groups', 'allowed_group_names',
                 'nextflow_profile', 'working_directory', 'env_vars', 'nextflow_config']
        read_only_fields = ['id', 'created_at', 'updated_at', 'category_name', 'allowed_groups']
    
    def update(self, instance, validated_data):
        # Handle allowed_group_names separately
        group_names = validated_data.pop('allowed_group_names', None)
        
        # Update other fields
        instance = super().update(instance, validated_data)
        
        # Update group membership if provided
        if group_names is not None:
            from django.contrib.auth.models import Group
            groups = Group.objects.filter(name__in=group_names)
            instance.allowed_groups.set(groups)
        
        return instance