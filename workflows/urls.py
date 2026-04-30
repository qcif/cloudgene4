from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'workflows', views.WorkflowViewSet, basename='workflow')
router.register(r'categories', views.WorkflowCategoryViewSet, basename='category')

urlpatterns = [
    path('api/', include(router.urls)),
]