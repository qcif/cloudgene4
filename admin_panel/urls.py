from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'server-settings', views.ServerSettingsViewSet, basename='server-settings')
router.register(r'templates', views.TemplateViewSet, basename='template')
router.register(r'navbar-items', views.NavbarItemViewSet, basename='navbar-item')
router.register(r'system-logs', views.SystemLogViewSet, basename='system-log')
router.register(r'counters', views.CounterViewSet, basename='counter')

urlpatterns = [
    path('api/admin/', include(router.urls)),
    path('api/admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
]