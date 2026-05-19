from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'workflows', views.WorkflowViewSet, basename='workflow')
router.register(r'categories', views.WorkflowCategoryViewSet, basename='category')

admin_router = DefaultRouter()
admin_router.register(r'workflows', views.WorkflowAdminViewSet, basename='admin-workflow')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/admin/', include(admin_router.urls)),
]