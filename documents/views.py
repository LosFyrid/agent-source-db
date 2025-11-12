"""
DRF ViewSets for AgentCard Management System

提供 REST API 端点
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Count

from django.db.models import Q

from .models import Namespace, SchemaRegistry, AgentCard, AgentCase
from .serializers import (
    NamespaceSerializer,
    SchemaRegistryListSerializer,
    SchemaRegistryDetailSerializer,
    AgentCardListSerializer,
    AgentCardDetailSerializer,
    AgentCardCreateUpdateSerializer,
    AgentCardStandardSerializer,
    SchemaCatalogSerializer,
    AgentCaseListSerializer,
    AgentCaseDetailSerializer,
    AgentCaseCreateUpdateSerializer,
)


# ========================================
# Namespace ViewSet
# ========================================

class NamespaceViewSet(viewsets.ModelViewSet):
    """
    命名空间 API

    提供命名空间的 CRUD 操作

    list: GET /api/namespaces/
    retrieve: GET /api/namespaces/{id}/
    create: POST /api/namespaces/
    update: PUT /api/namespaces/{id}/
    partial_update: PATCH /api/namespaces/{id}/
    destroy: DELETE /api/namespaces/{id}/
    """
    queryset = Namespace.objects.all().order_by('id')
    serializer_class = NamespaceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# ========================================
# Schema ViewSet
# ========================================

class SchemaRegistryViewSet(viewsets.ModelViewSet):
    """
    Schema 定义 API

    提供 Schema 的 CRUD 操作和目录查询

    list: GET /api/schemas/
    retrieve: GET /api/schemas/{id}/
    create: POST /api/schemas/
    update: PUT /api/schemas/{id}/
    partial_update: PATCH /api/schemas/{id}/
    destroy: DELETE /api/schemas/{id}/

    额外端点：
    catalog: GET /api/schemas/catalog/ - Schema 目录（发现机制）
    """
    queryset = SchemaRegistry.objects.filter(is_active=True).order_by('schema_type', '-version')
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        """
        根据操作类型选择序列化器
        """
        if self.action == 'list':
            return SchemaRegistryListSerializer
        return SchemaRegistryDetailSerializer

    @action(detail=False, methods=['get'])
    def catalog(self, request):
        """
        Schema 目录 API

        GET /api/schemas/catalog/

        返回所有活跃的 Schema，按类型分组

        响应格式：
        {
          "catalog": {
            "physicalAsset": [
              {
                "uri": "https://...",
                "version": "v1",
                "description": "...",
                "fields": [...],
                "usage_count": 5
              }
            ]
          },
          "categories": ["physicalAsset", "instrument"],
          "total_schemas": 2
        }
        """
        schemas = SchemaRegistry.objects.filter(is_active=True).order_by('schema_type', '-version')

        catalog = {}
        for schema in schemas:
            if schema.schema_type not in catalog:
                catalog[schema.schema_type] = []

            # 计算使用数量
            usage_count = AgentCard.objects.filter(
                domain_extensions__has_key=schema.schema_uri
            ).count()

            catalog[schema.schema_type].append({
                'uri': schema.schema_uri,
                'version': schema.version,
                'description': schema.description,
                'fields': schema.get_field_definitions(),
                'usage_count': usage_count,
                'example_data': schema.example_data,
            })

        data = {
            'catalog': catalog,
            'categories': list(catalog.keys()),
            'total_schemas': schemas.count(),
        }

        serializer = SchemaCatalogSerializer(data)
        return Response(serializer.data)


# ========================================
# AgentCard ViewSet
# ========================================

class AgentCardViewSet(viewsets.ModelViewSet):
    """
    AgentCard API

    提供 AgentCard 的 CRUD 操作

    list: GET /api/agentcards/
    retrieve: GET /api/agentcards/{id}/
    create: POST /api/agentcards/
    update: PUT /api/agentcards/{id}/
    partial_update: PATCH /api/agentcards/{id}/
    destroy: DELETE /api/agentcards/{id}/

    额外端点：
    standard_json: GET /api/agentcards/{id}/standard-json/ - 返回符合 A2A 协议的标准格式
    by_namespace: GET /api/agentcards/by-namespace/{namespace_id}/ - 按命名空间查询
    """
    queryset = AgentCard.objects.all().select_related('namespace').order_by(
        'namespace', 'name', '-version'
    )
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        """
        根据操作类型选择序列化器
        """
        if self.action == 'list':
            return AgentCardListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AgentCardCreateUpdateSerializer
        elif self.action == 'standard_json':
            return AgentCardStandardSerializer
        return AgentCardDetailSerializer

    def get_queryset(self):
        """
        支持查询参数过滤

        查询参数：
        - namespace: 按命名空间过滤
        - name: 按名称过滤
        - is_default_version: 只返回默认版本
        - is_active: 只返回激活的
        """
        queryset = super().get_queryset()

        # 按命名空间过滤
        namespace = self.request.query_params.get('namespace')
        if namespace:
            queryset = queryset.filter(namespace__id=namespace)

        # 按名称过滤
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)

        # 只返回默认版本
        is_default = self.request.query_params.get('is_default_version')
        if is_default and is_default.lower() == 'true':
            queryset = queryset.filter(is_default_version=True)

        # 只返回激活的
        is_active = self.request.query_params.get('is_active')
        if is_active and is_active.lower() == 'true':
            queryset = queryset.filter(is_active=True)

        return queryset

    def perform_create(self, serializer):
        """
        创建时自动设置创建者
        """
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user, updated_by=self.request.user)
        else:
            serializer.save()

    def perform_update(self, serializer):
        """
        更新时自动设置更新者
        """
        if self.request.user.is_authenticated:
            serializer.save(updated_by=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=['get'])
    def standard_json(self, request, pk=None):
        """
        返回符合 A2A 协议的标准 AgentCard JSON

        GET /api/agentcards/{id}/standard-json/
        GET /api/agentcards/{id}/standard-json/?include_metadata=true

        查询参数：
        - include_metadata: 是否包含内部元数据（默认 false）

        返回：符合 A2A 0.3.0 协议的 AgentCard JSON
        """
        agentcard = self.get_object()
        include_metadata = request.query_params.get('include_metadata', 'false').lower() == 'true'

        serializer = AgentCardStandardSerializer(
            agentcard,
            context={'include_metadata': include_metadata}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-namespace/(?P<namespace_id>[^/.]+)')
    def by_namespace(self, request, namespace_id=None):
        """
        按命名空间查询 AgentCard

        GET /api/agentcards/by-namespace/{namespace_id}/

        返回指定命名空间下的所有 AgentCard
        """
        queryset = self.get_queryset().filter(namespace__id=namespace_id)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ========================================
# AgentCase ViewSet
# ========================================

class AgentCaseViewSet(viewsets.ModelViewSet):
    """
    AgentCase API

    提供 AgentCase 的 CRUD 操作

    list: GET /api/cases/
    retrieve: GET /api/cases/{id}/
    create: POST /api/cases/
    update: PUT /api/cases/{id}/
    partial_update: PATCH /api/cases/{id}/
    destroy: DELETE /api/cases/{id}/
    """
    queryset = AgentCase.objects.all().select_related(
        'agent_card', 'agent_card__namespace', 'created_by', 'updated_by'
    ).order_by('-created_at')
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        """
        根据操作类型选择序列化器
        """
        if self.action == 'list':
            return AgentCaseListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AgentCaseCreateUpdateSerializer
        return AgentCaseDetailSerializer

    def get_queryset(self):
        """
        支持查询参数过滤

        查询参数：
        - agent_card: 按agent_card ID过滤
        - version: 按agent版本过滤（支持通配符*、latest、具体版本）
        - is_ground_truth: 只返回ground truth cases
        - query_key: 按查询问题标识过滤
        - unassigned: 只返回未分配agent的cases
        """
        queryset = super().get_queryset()

        # 按agent_card过滤
        agent_card_id = self.request.query_params.get('agent_card')
        if agent_card_id:
            queryset = queryset.filter(agent_card_id=agent_card_id)

            # 按版本过滤（支持通配符）
            version = self.request.query_params.get('version')
            if version:
                queryset = queryset.filter(
                    Q(agent_version='') |
                    Q(agent_version='*') |
                    Q(agent_version='latest') |
                    Q(agent_version=version)
                )

        # 只返回ground truth
        is_ground_truth = self.request.query_params.get('is_ground_truth')
        if is_ground_truth and is_ground_truth.lower() == 'true':
            queryset = queryset.filter(is_ground_truth=True)

        # 按查询问题标识过滤
        query_key = self.request.query_params.get('query_key')
        if query_key:
            queryset = queryset.filter(query_key__icontains=query_key)

        # 只返回未分配的cases
        unassigned = self.request.query_params.get('unassigned')
        if unassigned and unassigned.lower() == 'true':
            queryset = queryset.filter(agent_card__isnull=True)

        return queryset

    def perform_create(self, serializer):
        """
        创建时自动设置创建者
        """
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user, updated_by=self.request.user)
        else:
            serializer.save()

    def perform_update(self, serializer):
        """
        更新时自动设置更新者
        """
        if self.request.user.is_authenticated:
            serializer.save(updated_by=self.request.user)
        else:
            serializer.save()
