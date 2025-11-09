"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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

# 健康检查端点
from documents.health import health_liveness, health_readiness, health_database

# Admin 监控视图
from documents.admin_views import system_status

urlpatterns = [
    # Admin 监控面板（必须放在 admin/ 之前，否则会被 admin.site.urls 捕获）
    path('admin/system-status/', system_status, name='admin-system-status'),

    # Django Admin
    path('admin/', admin.site.urls),

    # API 路由
    path('api/', include('documents.urls')),

    # DRF 可浏览 API 的登录/登出界面
    path('api-auth/', include('rest_framework.urls')),

    # 健康检查端点
    path('health/', health_liveness, name='health-liveness'),
    path('health/ready/', health_readiness, name='health-readiness'),
    path('health/db/', health_database, name='health-database'),
]
