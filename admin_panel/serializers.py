"""
Serializers for admin panel API endpoints
"""
from rest_framework import serializers
from .models import ServerSettings, Template, NavbarItem, SystemLog, Counter


class ServerSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerSettings
        fields = ['id', 'name', 'value', 'description', 'setting_type', 'category']


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ['id', 'name', 'content', 'description', 'template_type', 
                 'created_at', 'updated_at', 'updated_by']
        read_only_fields = ['created_at', 'updated_at']


class NavbarItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = NavbarItem
        fields = ['id', 'title', 'url', 'icon', 'order', 'visible', 
                 'required_groups', 'admin_only']


class SystemLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = SystemLog
        fields = ['id', 'timestamp', 'level', 'message', 'component', 
                 'user_username', 'metadata']
        read_only_fields = fields


class CounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counter
        fields = ['id', 'name', 'value', 'description', 'last_updated']
        read_only_fields = ['id', 'value', 'last_updated']