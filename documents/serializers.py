"""
DRF Serializers for AgentCard Management System

序列化器负责将 Django 模型转换为 JSON 格式（以及反向）
"""

from rest_framework import serializers
from .models import Namespace, SchemaRegistry, SchemaField, AgentCard


# ========================================
# Namespace Serializer
# ========================================

class NamespaceSerializer(serializers.ModelSerializer):
    """
    命名空间序列化器
    """
    agent_card_count = serializers.SerializerMethodField()

    class Meta:
        model = Namespace
        fields = [
            'id', 'name', 'description', 'is_active',
            'created_at', 'updated_at', 'agent_card_count'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_agent_card_count(self, obj):
        """返回该命名空间下的 AgentCard 数量"""
        return obj.agent_cards.count()


# ========================================
# Schema Serializers
# ========================================

class SchemaFieldSerializer(serializers.ModelSerializer):
    """
    Schema 字段序列化器（用于嵌套在 SchemaRegistry 中）
    """
    field_type_display = serializers.CharField(
        source='get_field_type_display',
        read_only=True
    )
    constraints = serializers.SerializerMethodField()

    class Meta:
        model = SchemaField
        fields = [
            'id', 'field_name', 'field_type', 'field_type_display',
            'is_required', 'description', 'default_value',
            'min_length', 'max_length', 'min_value', 'max_value',
            'enum_choices', 'pattern', 'order', 'constraints'
        ]

    def get_constraints(self, obj):
        """返回约束条件（格式化）"""
        return obj.get_constraints()


class SchemaRegistryListSerializer(serializers.ModelSerializer):
    """
    Schema 列表序列化器（精简版）
    """
    field_count = serializers.SerializerMethodField()
    usage_count = serializers.SerializerMethodField()

    class Meta:
        model = SchemaRegistry
        fields = [
            'id', 'schema_uri', 'schema_type', 'version',
            'description', 'is_active', 'field_count', 'usage_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_field_count(self, obj):
        """返回字段数量"""
        return obj.fields.count()

    def get_usage_count(self, obj):
        """返回使用此 Schema 的 AgentCard 数量"""
        return AgentCard.objects.filter(
            domain_extensions__has_key=obj.schema_uri
        ).count()


class SchemaRegistryDetailSerializer(serializers.ModelSerializer):
    """
    Schema 详情序列化器（包含嵌套的 fields）
    """
    fields = SchemaFieldSerializer(many=True, read_only=True)
    field_definitions = serializers.SerializerMethodField()
    json_schema = serializers.SerializerMethodField()
    usage_count = serializers.SerializerMethodField()

    class Meta:
        model = SchemaRegistry
        fields = [
            'id', 'schema_uri', 'schema_type', 'version',
            'description', 'example_data', 'is_active',
            'fields', 'field_definitions', 'json_schema', 'usage_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_field_definitions(self, obj):
        """返回字段定义（易读格式）"""
        return obj.get_field_definitions()

    def get_json_schema(self, obj):
        """返回自动生成的 JSON Schema"""
        return obj.generate_json_schema()

    def get_usage_count(self, obj):
        """返回使用此 Schema 的 AgentCard 数量"""
        return AgentCard.objects.filter(
            domain_extensions__has_key=obj.schema_uri
        ).count()


# ========================================
# AgentCard Serializers
# ========================================

class AgentCardListSerializer(serializers.ModelSerializer):
    """
    AgentCard 列表序列化器（精简版，不包含大字段）
    """
    namespace_id = serializers.CharField(source='namespace.id', read_only=True)
    namespace_name = serializers.CharField(source='namespace.name', read_only=True)
    extension_count = serializers.SerializerMethodField()

    class Meta:
        model = AgentCard
        fields = [
            'id', 'namespace_id', 'namespace_name', 'name', 'version',
            'is_default_version', 'is_active', 'protocol_version',
            'description', 'url', 'preferred_transport',
            'extension_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_extension_count(self, obj):
        """返回 L2 扩展数量"""
        return len(obj.domain_extensions) if obj.domain_extensions else 0


class AgentCardDetailSerializer(serializers.ModelSerializer):
    """
    AgentCard 详情序列化器（完整信息）
    """
    namespace_id = serializers.CharField(source='namespace.id', read_only=True)
    namespace_name = serializers.CharField(source='namespace.name', read_only=True)
    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True,
        allow_null=True
    )
    updated_by_username = serializers.CharField(
        source='updated_by.username',
        read_only=True,
        allow_null=True
    )
    extension_schemas = serializers.SerializerMethodField()

    class Meta:
        model = AgentCard
        fields = [
            # 标识
            'id', 'namespace_id', 'namespace_name', 'name', 'version',
            'is_default_version', 'is_active',
            # L1 基本信息
            'protocol_version', 'description', 'url', 'preferred_transport',
            'icon_url', 'documentation_url',
            # L1 能力配置
            'capabilities', 'default_input_modes', 'default_output_modes', 'skills',
            # L1 高级选项
            'provider', 'additional_interfaces', 'security_schemes',
            'security', 'supports_authenticated_extended_card', 'signatures',
            # L2 扩展
            'domain_extensions', 'extension_schemas',
            # 元数据
            'created_at', 'updated_at', 'created_by_username', 'updated_by_username'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by_username', 'updated_by_username']

    def get_extension_schemas(self, obj):
        """
        返回扩展中使用的 Schema 信息
        """
        if not obj.domain_extensions:
            return []

        schema_infos = []
        for schema_uri in obj.domain_extensions.keys():
            try:
                schema = SchemaRegistry.objects.get(schema_uri=schema_uri)
                schema_infos.append({
                    'schema_uri': schema_uri,
                    'schema_type': schema.schema_type,
                    'version': schema.version,
                    'is_active': schema.is_active,
                })
            except SchemaRegistry.DoesNotExist:
                schema_infos.append({
                    'schema_uri': schema_uri,
                    'schema_type': None,
                    'version': None,
                    'is_active': False,
                    'warning': '未注册的 Schema'
                })

        return schema_infos


class AgentCardCreateUpdateSerializer(serializers.ModelSerializer):
    """
    AgentCard 创建/更新序列化器

    用于 POST/PUT/PATCH，包含字段验证
    """
    namespace = serializers.SlugRelatedField(
        slug_field='id',
        queryset=Namespace.objects.all()
    )

    class Meta:
        model = AgentCard
        fields = [
            'namespace', 'name', 'version', 'is_default_version', 'is_active',
            'protocol_version', 'description', 'url', 'preferred_transport',
            'icon_url', 'documentation_url',
            'capabilities', 'default_input_modes', 'default_output_modes', 'skills',
            'provider', 'additional_interfaces', 'security_schemes',
            'security', 'supports_authenticated_extended_card', 'signatures',
            'domain_extensions'
        ]

    def validate_domain_extensions(self, value):
        """
        验证 domain_extensions 格式
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("domain_extensions 必须是一个对象")

        # 验证每个 Schema URI
        for schema_uri, data in value.items():
            if not isinstance(data, dict):
                raise serializers.ValidationError(
                    f"Schema '{schema_uri}' 的数据必须是一个对象"
                )

        return value


class AgentCardStandardSerializer(serializers.Serializer):
    """
    符合 A2A 协议标准的 AgentCard JSON 序列化器

    用于 /api/agentcards/{id}/standard-json/ 端点
    不基于 ModelSerializer，直接使用 to_agentcard_json() 方法

    注意：此序列化器用于生产环境 API 导出，会进行严格的 A2A 协议验证。
    如果 AgentCard 数据不完整，会返回 400 错误。
    """
    def to_representation(self, instance):
        """
        直接使用模型的 to_agentcard_json() 方法

        使用 validate=True 确保导出的 AgentCard 符合 A2A 协议要求
        """
        include_metadata = self.context.get('include_metadata', False)
        try:
            return instance.to_agentcard_json(include_metadata=include_metadata, validate=True)
        except Exception as e:
            # 将 ValidationError 转换为 serializers.ValidationError
            # 这样 DRF 会返回 400 Bad Request 而不是 500 Internal Server Error
            raise serializers.ValidationError({
                'detail': 'AgentCard 数据不完整，无法导出',
                'errors': str(e)
            })


# ========================================
# Schema Catalog Serializer
# ========================================

class SchemaCatalogSerializer(serializers.Serializer):
    """
    Schema 目录序列化器（用于发现机制）

    返回格式：
    {
      "catalog": {
        "physicalAsset": [
          {uri, version, description, fields, usage_count}
        ]
      },
      "categories": ["physicalAsset", "instrument"],
      "total_schemas": 5
    }
    """
    catalog = serializers.DictField()
    categories = serializers.ListField()
    total_schemas = serializers.IntegerField()
