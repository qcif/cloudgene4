"""
Authentication and user management views
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

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
    User login — returns a DRF token and the serialized user.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'Login successful',
            })
        errors = serializer.errors.get(
            'non_field_errors', ['Invalid credentials']
        )
        return Response(
            {'message': errors[0]}, status=status.HTTP_400_BAD_REQUEST
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
                'message': (
                    'Registration successful. '
                    'Please check your email for activation instructions.'
                ),
            }, status=status.HTTP_201_CREATED)
        return Response(
            {'message': str(next(iter(serializer.errors.values()))[0])},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ActivateAccountView(APIView):
    """
    Account activation view
    """
    permission_classes = [AllowAny]

    def get(self, request, activation_key):
        try:
            user = User.objects.get(
                activation_key=activation_key, is_active=False
            )
            user.is_active = True
            user.activation_key = None
            user.save()
            return Response({'message': 'Account activated successfully'})
        except User.DoesNotExist:
            return Response(
                {'message': 'Invalid activation key'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        import uuid
        user = User.objects.get(email=serializer.validated_data['email'])
        user.password_reset_token = str(uuid.uuid4())
        user.password_reset_expires = (
            timezone.now() + timezone.timedelta(hours=24)
        )
        user.save()

        reset_url = request.build_absolute_uri(
            f'/recover/{user.password_reset_token}'
        )
        send_mail(
            subject='Reset your Cloudgene password',
            message=(
                f'Hi {user.full_name or user.username},\n\n'
                f'Click the link below to reset your password. '
                f'This link expires in 24 hours.\n\n'
                f'{reset_url}\n\n'
                f'If you did not request a password reset, '
                f'you can ignore this email.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({'message': 'Password reset email sent'})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, token):
        try:
            user = User.objects.get(password_reset_token=token)
        except User.DoesNotExist:
            return Response(
                {'message': 'Invalid or expired reset link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            user.password_reset_expires is None
            or timezone.now() > user.password_reset_expires
        ):
            return Response(
                {'message': 'This reset link has expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        password = request.data.get('password', '')
        error = User.validate_password(password)
        if error:
            return Response(
                {'message': error}, status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(password)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.save()

        return Response({'message': 'Password reset successful'})
