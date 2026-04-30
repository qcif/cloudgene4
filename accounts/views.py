"""
Authentication and user management views
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from .models import User, UserToken
from .serializers import (
    UserSerializer, UserRegistrationSerializer, GroupSerializer,
    LoginSerializer, PasswordResetSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_admin_user():
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)


class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for group management
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_admin_user():
            return Group.objects.all()
        return Group.objects.none()


class LoginView(APIView):
    """
    User login view
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            return Response({
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            })
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    """
    User logout view
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'})


class RegisterView(APIView):
    """
    User registration view
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'user': UserSerializer(user).data,
                'message': 'Registration successful. Please check your email for activation instructions.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(APIView):
    """
    Account activation view
    """
    permission_classes = [AllowAny]

    def get(self, request, activation_key):
        try:
            user = User.objects.get(activation_key=activation_key, is_active=False)
            user.is_active = True
            user.activation_key = None
            user.save()
            return Response({'message': 'Account activated successfully'})
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid activation key'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetView(APIView):
    """
    Password reset request view
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            # Send password reset email (implementation needed)
            return Response({'message': 'Password reset email sent'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Password reset confirmation view
    """
    permission_classes = [AllowAny]

    def post(self, request, token):
        # Implement password reset confirmation logic
        return Response({'message': 'Password reset successful'})
