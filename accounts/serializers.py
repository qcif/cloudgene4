"""
Serializers for account-related API endpoints
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from .models import User, UserToken


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'is_active', 
                 'is_staff', 'date_joined', 'last_login', 'groups']
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'password', 'password_confirm']
    
    def validate(self, data):
        # Validate password
        password_error = User.validate_password(data['password'], data['password_confirm'])
        if password_error:
            raise serializers.ValidationError({'password': password_error})
        
        # Validate username
        username_error = User.validate_username(data['username'])
        if username_error:
            raise serializers.ValidationError({'username': username_error})
        
        # Validate email
        email_error = User.validate_email(data['email'])
        if email_error:
            raise serializers.ValidationError({'email': email_error})
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Generate activation key
        import uuid
        user.activation_key = str(uuid.uuid4())
        user.is_active = False  # Require activation
        user.save()
        
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                data['user'] = user
            else:
                raise serializers.ValidationError('Invalid username or password.')
        else:
            raise serializers.ValidationError('Must include username and password.')
        
        return data


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('No user found with this email address.')
        return value


class UserTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserToken
        fields = ['id', 'name', 'token', 'created_at', 'expires_at', 'last_used']
        read_only_fields = ['id', 'token', 'created_at', 'last_used']