"""
API URL Configuration for documents app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建 DRF Router
router = DefaultRouter()

# 注册 ViewSets
router.register(r'namespaces', views.NamespaceViewSet, basename='namespace')
router.register(r'schemas', views.SchemaRegistryViewSet, basename='schema')
router.register(r'agentcards', views.AgentCardViewSet, basename='agentcard')
router.register(r'cases', views.AgentCaseViewSet, basename='agentcase')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]
