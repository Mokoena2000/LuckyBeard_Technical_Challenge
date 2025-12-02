"""todo_list URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from base.api_views import TaskViewSet  # Import our new API view
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configure Swagger Documentation
schema_view = get_schema_view(
   openapi.Info(
      title="LuckyBeard Challenge API",
      default_version='v1',
      description="API Documentation for the Technical Challenge",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# Router for the API
router = DefaultRouter()
router.register(r'api/tasks', TaskViewSet, basename='api-tasks')
router.register(r'api/users', UserViewSet, basename='api-users')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls')), # Existing App URLs
    
    # NEW API URLS
    path('', include(router.urls)),
    
    # Documentation URLs (The Challenge Requirement)
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]