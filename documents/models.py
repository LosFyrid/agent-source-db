"""
AgentCard 数据模型
实现 A2A 协议 L1 标准字段 + L2 领域扩展

设计原则：
1. L1字段严格遵循 A2A 协议规范
2. L2扩展使用命名空间隔离（domainExtensions）
3. 支持 Nacos 风格的多版本管理
4. PostgreSQL JSONB 用于灵活存储嵌套对象
"""

from django.db import models
from django.core.validators import URLValidator, RegexValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import json


class Namespace(models.Model):
    """
    命名空间隔离

    匹配 Nacos 的 namespace 机制，用于多环境/多团队的资源隔离。
    例如: 'dev', 'test', 'prod', 'lab-instruments', 'finance-bots'
    """

    id = models.CharField(
        max_length=128,
        primary_key=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_-]+$',
                message='命名空间ID只能包含字母、数字、下划线和连字符'
            )
        ],
        help_text="命名空间唯一标识，如 'dev', 'prod', 'lab-instruments'"
    )
    name = models.CharField(
        max_length=255,
        help_text="命名空间显示名称"
    )
    description = models.TextField(
        blank=True,
        help_text="命名空间用途说明"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="是否启用（禁用后该命名空间下的所有AgentCard将不可见）"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'namespaces'
        verbose_name = '命名空间'
        verbose_name_plural = '命名空间'
        ordering = ['id']

    def __str__(self):
        return f"{self.id} ({self.name})"

    def delete(self, *args, **kwargs):
        """
        删除前检查：如果有关联的 AgentCard，禁止删除
        """
        card_count = self.agent_cards.count()
        if card_count > 0:
            raise ValidationError(
                f"无法删除命名空间 '{self.id}'：该命名空间下有 {card_count} 个 AgentCard。"
                f"请先删除或移动所有 AgentCard。"
            )
        super().delete(*args, **kwargs)


class SchemaRegistry(models.Model):
    """
    L2 Schema URI 注册表

    简化的 Schema 管理，通过 SchemaField 可视化定义字段。
    适合小团队快速迭代，无需手写 JSON Schema。

    示例 Schema URI:
    - https://my-org.com/schemas/physicalAsset/v1
    - https://my-org.com/schemas/instrument/hplc/v1.2
    """

    schema_uri = models.URLField(
        max_length=512,
        unique=True,
        help_text="Schema URI（全球唯一标识符），如 https://my-org.com/schemas/physicalAsset/v1"
    )
    schema_type = models.CharField(
        max_length=128,
        db_index=True,
        help_text="Schema 类型简称，如 'physicalAsset', 'hplc', 'financeBot'"
    )
    version = models.CharField(
        max_length=32,
        help_text="Schema 版本号，如 'v1', 'v1.2', 'v2.0'"
    )
    description = models.TextField(
        blank=True,
        help_text="Schema 用途说明（用于文档和 API）"
    )
    example_data = models.JSONField(
        null=True,
        blank=True,
        help_text="示例数据（可选，帮助开发者理解）"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="是否启用"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'schema_registry'
        verbose_name = 'Schema定义'
        verbose_name_plural = 'Schema定义'
        unique_together = [('schema_type', 'version')]
        indexes = [
            models.Index(fields=['schema_type', 'version']),
            models.Index(fields=['is_active']),
        ]
        ordering = ['schema_type', '-version']

    def __str__(self):
        status = "" if self.is_active else " [未启用]"
        return f"{self.schema_type} {self.version}{status}"

    def generate_json_schema(self) -> dict:
        """
        从 SchemaField 自动生成 JSON Schema（draft-07 格式）

        Returns:
            标准的 JSON Schema 对象
        """
        properties = {}
        required_fields = []

        for field in self.fields.all():
            field_schema = field.to_json_schema_property()
            properties[field.field_name] = field_schema

            if field.is_required:
                required_fields.append(field.field_name)

        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": f"{self.schema_type} {self.version}",
            "description": self.description or f"{self.schema_type} schema",
            "properties": properties,
        }

        if required_fields:
            schema["required"] = required_fields

        return schema

    def validate_extension_data(self, data: dict) -> tuple[bool, str]:
        """
        验证扩展数据（简化版，基于 SchemaField 定义）

        Returns:
            (is_valid, error_message)
        """
        errors = []

        # 检查必填字段
        for field in self.fields.filter(is_required=True):
            if field.field_name not in data:
                errors.append(f"缺少必填字段：{field.field_name}")

        # 类型检查（简单版本）
        for field_name, value in data.items():
            try:
                field = self.fields.get(field_name=field_name)
                is_valid, error = field.validate_value(value)
                if not is_valid:
                    errors.append(f"字段 '{field_name}': {error}")
            except SchemaField.DoesNotExist:
                # 允许额外字段（宽松模式）
                pass

        if errors:
            return False, "\n".join(errors)
        return True, ""

    def get_field_definitions(self) -> list[dict]:
        """
        获取字段定义列表（用于 API 响应）

        Returns:
            字段定义数组，格式友好
        """
        return [
            {
                'name': field.field_name,
                'type': field.field_type,
                'required': field.is_required,
                'description': field.description,
                'default': field.default_value,
                'constraints': field.get_constraints(),
            }
            for field in self.fields.all().order_by('order', 'field_name')
        ]

    def delete(self, *args, **kwargs):
        """
        删除前检查：如果有 AgentExtension 正在使用此 Schema，禁止删除
        """
        usage_count = self.agent_extensions.count()

        if usage_count > 0:
            raise ValidationError(
                f"无法删除 Schema '{self.schema_type} {self.version}'："
                f"有 {usage_count} 个 AgentExtension 正在使用此 Schema。"
                f"请先更新或删除这些扩展。"
            )

        super().delete(*args, **kwargs)


class SchemaField(models.Model):
    """
    Schema 字段定义

    可视化定义 Schema 的每个字段，通过 Django Admin 管理。
    自动生成 JSON Schema 和验证逻辑。
    """

    FIELD_TYPES = [
        ('string', '文本'),
        ('integer', '整数'),
        ('number', '数字（含小数）'),
        ('boolean', '布尔值'),
        ('array', '数组'),
        ('object', '对象'),
        ('datetime', '日期时间'),
        ('date', '日期'),
        ('enum', '枚举（单选）'),
    ]

    schema = models.ForeignKey(
        SchemaRegistry,
        on_delete=models.CASCADE,
        related_name='fields',
        help_text="所属 Schema"
    )
    field_name = models.CharField(
        max_length=128,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z][a-zA-Z0-9_]*$',
                message='字段名必须以字母开头，只能包含字母、数字和下划线'
            )
        ],
        help_text="字段名称（建议使用 camelCase，如 'physicalAssetId'）"
    )
    field_type = models.CharField(
        max_length=32,
        choices=FIELD_TYPES,
        default='string',
        help_text="字段数据类型"
    )
    is_required = models.BooleanField(
        default=False,
        help_text="是否必填"
    )
    description = models.TextField(
        blank=True,
        help_text="字段说明（会显示在文档和 API 中）"
    )
    default_value = models.JSONField(
        null=True,
        blank=True,
        help_text="默认值（JSON 格式）"
    )

    # 约束条件（可选）
    min_length = models.IntegerField(
        null=True,
        blank=True,
        help_text="最小长度（仅 string 类型）"
    )
    max_length = models.IntegerField(
        null=True,
        blank=True,
        help_text="最大长度（仅 string 类型）"
    )
    min_value = models.FloatField(
        null=True,
        blank=True,
        help_text="最小值（仅 integer/number 类型）"
    )
    max_value = models.FloatField(
        null=True,
        blank=True,
        help_text="最大值（仅 integer/number 类型）"
    )
    enum_choices = models.JSONField(
        null=True,
        blank=True,
        help_text="枚举值列表（仅 enum 类型），如 ['OPERATIONAL', 'MAINTENANCE', 'OFFLINE']"
    )
    pattern = models.CharField(
        max_length=512,
        blank=True,
        help_text="正则表达式模式（仅 string 类型），如 '^[A-Z]{2,4}-\\d{3}$'"
    )

    # 显示顺序
    order = models.IntegerField(
        default=0,
        help_text="显示顺序（越小越靠前）"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'schema_fields'
        verbose_name = 'Schema字段'
        verbose_name_plural = 'Schema字段'
        unique_together = [('schema', 'field_name')]
        ordering = ['schema', 'order', 'field_name']

    def __str__(self):
        required_marker = "*" if self.is_required else ""
        return f"{self.field_name}{required_marker}: {self.get_field_type_display()}"

    def clean(self):
        """
        验证约束与字段类型的匹配性
        """
        super().clean()

        # 验证1：数值类型不能设置长度或正则约束
        if self.field_type in ['integer', 'number']:
            if self.min_length is not None or self.max_length is not None:
                raise ValidationError({
                    'min_length': f"{self.get_field_type_display()}类型不能设置最小/最大长度，请使用最小/最大值。"
                })
            if self.pattern:
                raise ValidationError({
                    'pattern': f"{self.get_field_type_display()}类型不能设置正则表达式。"
                })
            if self.enum_choices:
                raise ValidationError({
                    'enum_choices': f"{self.get_field_type_display()}类型不能设置枚举值。"
                })

        # 验证2：字符串类型不能设置数值范围约束
        if self.field_type == 'string':
            if self.min_value is not None or self.max_value is not None:
                raise ValidationError({
                    'min_value': "文本类型不能设置最小/最大值，请使用最小/最大长度。"
                })
            if self.enum_choices:
                raise ValidationError({
                    'enum_choices': "文本类型不能设置枚举值，请使用 enum 类型。"
                })

        # 验证3：枚举类型必须设置 enum_choices
        if self.field_type == 'enum':
            if not self.enum_choices:
                raise ValidationError({
                    'enum_choices': "枚举类型必须设置枚举值列表。"
                })
            if not isinstance(self.enum_choices, list) or len(self.enum_choices) == 0:
                raise ValidationError({
                    'enum_choices': "枚举值必须是非空数组，如 [\"OPTION1\", \"OPTION2\"]"
                })
            # 枚举类型不能设置其他约束
            if any([self.min_length, self.max_length, self.min_value, self.max_value, self.pattern]):
                raise ValidationError("枚举类型不能设置其他约束（长度、数值范围、正则）。")

        # 验证4：布尔/数组/对象/日期类型不能设置任何约束
        if self.field_type in ['boolean', 'array', 'object', 'datetime', 'date']:
            if any([
                self.min_length, self.max_length, self.min_value, self.max_value,
                self.pattern, self.enum_choices
            ]):
                raise ValidationError(
                    f"{self.get_field_type_display()}类型不支持设置约束条件。"
                )

    def to_json_schema_property(self) -> dict:
        """
        转换为 JSON Schema property 定义

        Returns:
            JSON Schema property 对象
        """
        prop = {
            "type": self.field_type if self.field_type != 'datetime' else 'string',
            "description": self.description or self.field_name,
        }

        # 日期时间特殊处理
        if self.field_type in ['datetime', 'date']:
            prop["format"] = self.field_type
            prop["type"] = "string"

        # 枚举类型
        if self.field_type == 'enum' and self.enum_choices:
            prop["enum"] = self.enum_choices
            prop["type"] = "string"

        # 字符串约束
        if self.field_type == 'string':
            if self.min_length is not None:
                prop["minLength"] = self.min_length
            if self.max_length is not None:
                prop["maxLength"] = self.max_length
            if self.pattern:
                prop["pattern"] = self.pattern

        # 数值约束
        if self.field_type in ['integer', 'number']:
            if self.min_value is not None:
                prop["minimum"] = self.min_value
            if self.max_value is not None:
                prop["maximum"] = self.max_value

        # 默认值
        if self.default_value is not None:
            prop["default"] = self.default_value

        return prop

    def validate_value(self, value) -> tuple[bool, str]:
        """
        验证字段值（简化版）

        Returns:
            (is_valid, error_message)
        """
        # 类型检查
        type_checks = {
            'string': lambda v: isinstance(v, str),
            'integer': lambda v: isinstance(v, int) and not isinstance(v, bool),
            'number': lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            'boolean': lambda v: isinstance(v, bool),
            'array': lambda v: isinstance(v, list),
            'object': lambda v: isinstance(v, dict),
        }

        if self.field_type in type_checks:
            if not type_checks[self.field_type](value):
                return False, f"类型错误，期望 {self.get_field_type_display()}"

        # 枚举检查
        if self.field_type == 'enum' and self.enum_choices:
            if value not in self.enum_choices:
                return False, f"值必须是以下之一：{', '.join(map(str, self.enum_choices))}"

        # 字符串长度检查
        if self.field_type == 'string' and isinstance(value, str):
            if self.min_length and len(value) < self.min_length:
                return False, f"长度不能小于 {self.min_length}"
            if self.max_length and len(value) > self.max_length:
                return False, f"长度不能大于 {self.max_length}"

        # 数值范围检查
        if self.field_type in ['integer', 'number'] and isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                return False, f"值不能小于 {self.min_value}"
            if self.max_value is not None and value > self.max_value:
                return False, f"值不能大于 {self.max_value}"

        return True, ""

    def get_constraints(self) -> dict:
        """
        获取约束条件（用于 API 响应）
        """
        constraints = {}

        if self.field_type == 'enum' and self.enum_choices:
            constraints['enum'] = self.enum_choices
        if self.min_length is not None:
            constraints['minLength'] = self.min_length
        if self.max_length is not None:
            constraints['maxLength'] = self.max_length
        if self.min_value is not None:
            constraints['minValue'] = self.min_value
        if self.max_value is not None:
            constraints['maxValue'] = self.max_value
        if self.pattern:
            constraints['pattern'] = self.pattern

        return constraints


class AgentCard(models.Model):
    """
    AgentCard 主模型

    实现 A2A 协议的 AgentCard 规范，包含：
    - L1 标准字段（protocolVersion, name, url, skills 等）
    - L2 领域扩展（domainExtensions）
    - Nacos 兼容特性（namespace, 多版本管理）

    唯一性约束：(namespace, name, version) 三元组
    """

    # ========================================
    # 唯一标识（Nacos 风格）
    # ========================================

    namespace = models.ForeignKey(
        Namespace,
        on_delete=models.CASCADE,
        related_name='agent_cards',
        help_text="所属命名空间（用于环境/团队隔离）"
    )
    name = models.CharField(
        max_length=64,
        validators=[
            RegexValidator(
                regex=r'^[\x20-\x7E]+$',
                message='名称只能包含 ASCII 可打印字符（码位 32-126）'
            )
        ],
        help_text="Agent 名称（在同一 namespace 内，name + version 唯一）"
    )
    version = models.CharField(
        max_length=32,
        help_text="Agent 版本号，建议使用语义化版本，如 '1.0.0', '2.1.3-beta'"
    )
    is_default_version = models.BooleanField(
        default=False,
        db_index=True,
        help_text="是否为默认发布版本（每个 namespace::name 只能有一个默认版本）"
    )

    # ========================================
    # L1 必需字段（A2A 协议）
    # ========================================

    protocol_version = models.CharField(
        max_length=16,
        default='0.3.0',
        help_text="A2A 协议版本号"
    )
    description = models.TextField(
        help_text="Agent 用途和领域说明（清晰描述其功能）"
    )
    url = models.URLField(
        max_length=512,
        help_text="主要端点 URL（必须使用 HTTPS）"
    )
    preferred_transport = models.CharField(
        max_length=32,
        choices=[
            ('JSONRPC', 'JSON-RPC'),
            ('GRPC', 'gRPC'),
            ('HTTP+JSON', 'HTTP+JSON'),
        ],
        default='JSONRPC',
        help_text=(
            "首选传输协议（A2A 协议 5.6.1 - 必填字段）\n"
            "• JSONRPC: JSON-RPC 2.0 over HTTP(S)\n"
            "• GRPC: gRPC protocol\n"
            "• HTTP+JSON: RESTful HTTP with JSON"
        )
    )

    # ========================================
    # L1 嵌套对象（使用 JSONField 存储）
    # ========================================

    # AgentCapabilities - 拆分为独立字段
    capability_streaming = models.BooleanField(
        default=False,
        help_text="是否支持 SSE 流式响应（A2A 协议 5.5.2）"
    )
    capability_push_notifications = models.BooleanField(
        default=False,
        help_text="是否支持推送通知"
    )
    capability_state_transition_history = models.BooleanField(
        default=False,
        help_text="是否提供状态转换历史"
    )

    # 保留旧字段作为备份（迁移后将删除）
    capabilities = models.JSONField(
        default=dict,
        blank=True,
        help_text="[已废弃] 旧的 capabilities 字段，数据已迁移到 capability_* 字段和 AgentExtension 模型"
    )
    default_input_modes = models.JSONField(
        default=list,
        blank=True,
        help_text="支持的输入 MIME 类型数组，如 ['text/plain', 'application/json', 'image/png']（A2A 必填，但数据库层允许暂时为空以支持渐进式录入）"
    )
    default_output_modes = models.JSONField(
        default=list,
        blank=True,
        help_text="支持的输出 MIME 类型数组，如 ['text/plain', 'application/json']（A2A 必填，但数据库层允许暂时为空以支持渐进式录入）"
    )
    skills = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "AgentSkill 数组，每个 skill 包含: "
            "{name, description, inputModes?, outputModes?, parameters?}（A2A 必填，但数据库层允许暂时为空以支持渐进式录入）"
        )
    )

    # ========================================
    # L1 可选字段
    # ========================================

    provider = models.JSONField(
        null=True,
        blank=True,
        help_text="AgentProvider 对象，如 {name: 'My Organization', url: 'https://my-org.com', email: 'contact@my-org.com'}"
    )
    icon_url = models.URLField(
        max_length=512,
        null=True,
        blank=True,
        help_text="Agent 图标 URL（建议使用 PNG/SVG，尺寸 256x256）"
    )
    documentation_url = models.URLField(
        max_length=512,
        null=True,
        blank=True,
        help_text="详细文档链接"
    )
    additional_interfaces = models.JSONField(
        default=list,
        blank=True,
        help_text="AgentInterface 数组（备选传输方式），如 [{transport: 'grpc', url: 'grpc://...'}]"
    )
    security_schemes = models.JSONField(
        default=dict,
        blank=True,
        help_text="认证方案定义（OpenAPI 风格），如 {apiKey: {type: 'apiKey', in: 'header', name: 'X-API-Key'}}"
    )
    security = models.JSONField(
        default=list,
        blank=True,
        help_text="安全要求数组（OR/AND 逻辑），如 [{apiKey: []}] 或 [{oauth: ['read', 'write']}]"
    )
    supports_authenticated_extended_card = models.BooleanField(
        default=False,
        help_text="是否支持认证后返回扩展卡（包含敏感信息）"
    )
    signatures = models.JSONField(
        default=list,
        blank=True,
        help_text="JWS 签名数组（用于 AgentCard 完整性验证）"
    )

    # ========================================
    # L2 扩展字段（已废弃，改用 AgentExtension 模型）
    # ========================================

    domain_extensions = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "[已废弃] 旧的 domainExtensions 字段，数据已迁移到 AgentExtension 模型。\n"
            "新设计符合 A2A 协议标准，使用 AgentCapabilities.extensions[] 存储。"
        )
    )

    # ========================================
    # 元数据与审计
    # ========================================

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="是否激活（用于软删除或临时禁用）"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_agent_cards',
        help_text="创建者"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_agent_cards',
        help_text="最后更新者"
    )

    class Meta:
        db_table = 'agent_cards'
        verbose_name = 'AgentCard'
        verbose_name_plural = 'AgentCards'
        unique_together = [
            ('namespace', 'name', 'version')  # Nacos 的唯一性约束
        ]
        indexes = [
            models.Index(fields=['namespace', 'name', 'is_default_version']),
            models.Index(fields=['namespace', 'is_active']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            # PostgreSQL GIN 索引用于 JSONB 查询（需在迁移中手动添加）
            # CREATE INDEX idx_domain_extensions_gin ON agent_cards USING GIN (domain_extensions jsonb_path_ops);
        ]
        ordering = ['namespace', 'name', '-version']

    def __str__(self):
        default_marker = " [默认]" if self.is_default_version else ""
        return f"{self.namespace.id}::{self.name}@{self.version}{default_marker}"

    def clean(self):
        """
        模型级别的数据验证（A2A 协议严格模式）
        """
        super().clean()

        # 验证1：每个 namespace::name 只能有一个默认版本
        if self.is_default_version:
            existing_default = AgentCard.objects.filter(
                namespace=self.namespace,
                name=self.name,
                is_default_version=True
            ).exclude(pk=self.pk)

            if existing_default.exists():
                raise ValidationError({
                    'is_default_version': (
                        f"Agent '{self.name}' 在命名空间 '{self.namespace.id}' "
                        f"已存在默认版本 '{existing_default.first().version}'。"
                        f"请先取消原默认版本。"
                    )
                })

        # 验证2：生产环境必须使用 HTTPS（符合 A2A 协议 Section 4.1）
        from django.conf import settings
        if not settings.DEBUG:  # 仅在生产环境（DEBUG=False）检查
            if not self.url.startswith('https://'):
                raise ValidationError({
                    'url': "生产环境的 Agent URL 必须使用 HTTPS（符合 A2A 协议 Section 4.1 要求）"
                })

        # 验证3：domain_extensions 中的 schema_uri 是否已注册（可选检查）
        for schema_uri in self.domain_extensions.keys():
            try:
                schema = SchemaRegistry.objects.get(
                    schema_uri=schema_uri,
                    is_active=True
                )

                # 可选：验证数据是否符合 Schema 定义
                extension_data = self.domain_extensions[schema_uri]
                is_valid, error_msg = schema.validate_extension_data(extension_data)
                if not is_valid:
                    raise ValidationError({
                        'domain_extensions': (
                            f"扩展数据不符合 Schema '{schema_uri}' 的定义:\n{error_msg}"
                        )
                    })
            except SchemaRegistry.DoesNotExist:
                # 选项A：严格模式 - 要求所有 schema_uri 必须注册
                # raise ValidationError({
                #     'domain_extensions': f"未注册的 Schema URI: {schema_uri}"
                # })
                # 选项B：宽松模式 - 允许未注册的 schema_uri（当前采用）
                pass

        # ========================================
        # A2A 协议字段格式验证（宽松模式 - 允许渐进式录入）
        # ========================================
        # 策略：
        # - 数据库层：只验证格式，不强制必填（方便分步录入）
        # - 输出层：to_agentcard_json() 严格验证必填字段
        # ========================================

        # 验证4：defaultInputModes（格式验证，允许为空）
        if not isinstance(self.default_input_modes, list):
            raise ValidationError({
                'default_input_modes': "defaultInputModes 必须是一个数组"
            })

        # 如果有值，验证格式
        if self.default_input_modes:
            for mode in self.default_input_modes:
                if not isinstance(mode, str):
                    raise ValidationError({
                        'default_input_modes': f"defaultInputModes 中的每个元素必须是字符串（MIME 类型），发现: {type(mode).__name__}"
                    })
                # 简单的 MIME 类型格式检查
                if '/' not in mode:
                    raise ValidationError({
                        'default_input_modes': f"'{mode}' 不是有效的 MIME 类型格式（应为 'type/subtype'）"
                    })

        # 验证5：defaultOutputModes（格式验证，允许为空）
        if not isinstance(self.default_output_modes, list):
            raise ValidationError({
                'default_output_modes': "defaultOutputModes 必须是一个数组"
            })

        # 如果有值，验证格式
        if self.default_output_modes:
            for mode in self.default_output_modes:
                if not isinstance(mode, str):
                    raise ValidationError({
                        'default_output_modes': f"defaultOutputModes 中的每个元素必须是字符串（MIME 类型），发现: {type(mode).__name__}"
                    })
                if '/' not in mode:
                    raise ValidationError({
                        'default_output_modes': f"'{mode}' 不是有效的 MIME 类型格式（应为 'type/subtype'）"
                    })

        # 验证6：skills（格式验证，允许为空）
        if not isinstance(self.skills, list):
            raise ValidationError({
                'skills': "skills 必须是一个数组"
            })

        # 如果有 skills，验证结构
        if self.skills:
            for idx, skill in enumerate(self.skills):
                if not isinstance(skill, dict):
                    raise ValidationError({
                        'skills': f"skills[{idx}] 必须是一个对象，发现: {type(skill).__name__}"
                    })

                # 必填字段检查（根据 A2A 协议，AgentSkill 的必填字段）
                # 注意：examples 是可选的，不在必填列表中
                required_skill_fields = ['id', 'name', 'description', 'tags']
                for field in required_skill_fields:
                    if field not in skill:
                        raise ValidationError({
                            'skills': f"skills[{idx}] 缺少必填字段 '{field}'（A2A 协议要求）"
                        })

                # 字段类型检查
                if not isinstance(skill.get('id'), str):
                    raise ValidationError({
                        'skills': f"skills[{idx}].id 必须是字符串"
                    })

                if not isinstance(skill.get('name'), str):
                    raise ValidationError({
                        'skills': f"skills[{idx}].name 必须是字符串"
                    })

                if not isinstance(skill.get('description'), str):
                    raise ValidationError({
                        'skills': f"skills[{idx}].description 必须是字符串"
                    })

                if not isinstance(skill.get('tags'), list):
                    raise ValidationError({
                        'skills': f"skills[{idx}].tags 必须是字符串数组"
                    })

                for tag in skill.get('tags', []):
                    if not isinstance(tag, str):
                        raise ValidationError({
                            'skills': f"skills[{idx}].tags 中的每个元素必须是字符串"
                        })

                # 可选字段验证（如果存在）
                if 'examples' in skill:
                    if not isinstance(skill['examples'], list):
                        raise ValidationError({
                            'skills': f"skills[{idx}].examples 必须是数组"
                        })
                    for example in skill['examples']:
                        if not isinstance(example, str):
                            raise ValidationError({
                                'skills': f"skills[{idx}].examples 中的每个元素必须是字符串"
                            })
                if 'inputModes' in skill:
                    if not isinstance(skill['inputModes'], list):
                        raise ValidationError({
                            'skills': f"skills[{idx}].inputModes 必须是字符串数组"
                        })
                    for mode in skill['inputModes']:
                        if not isinstance(mode, str) or '/' not in mode:
                            raise ValidationError({
                                'skills': f"skills[{idx}].inputModes 包含无效的 MIME 类型: {mode}"
                            })

                if 'outputModes' in skill:
                    if not isinstance(skill['outputModes'], list):
                        raise ValidationError({
                            'skills': f"skills[{idx}].outputModes 必须是字符串数组"
                        })
                    for mode in skill['outputModes']:
                        if not isinstance(mode, str) or '/' not in mode:
                            raise ValidationError({
                                'skills': f"skills[{idx}].outputModes 包含无效的 MIME 类型: {mode}"
                            })

        # 验证7：provider（可选，但如果存在必须符合 AgentProvider 结构）
        if self.provider:
            if not isinstance(self.provider, dict):
                raise ValidationError({
                    'provider': "provider 必须是一个对象"
                })

            if 'organization' not in self.provider:
                raise ValidationError({
                    'provider': "provider 必须包含 'organization' 字段"
                })

            if 'url' not in self.provider:
                raise ValidationError({
                    'provider': "provider 必须包含 'url' 字段"
                })

            if not isinstance(self.provider['organization'], str):
                raise ValidationError({
                    'provider': "provider.organization 必须是字符串"
                })

            if not isinstance(self.provider['url'], str):
                raise ValidationError({
                    'provider': "provider.url 必须是字符串"
                })

        # 验证8：additionalInterfaces（可选，AgentInterface 对象数组）
        if self.additional_interfaces:
            if not isinstance(self.additional_interfaces, list):
                raise ValidationError({
                    'additional_interfaces': "additionalInterfaces 必须是一个数组"
                })

            for idx, interface in enumerate(self.additional_interfaces):
                if not isinstance(interface, dict):
                    raise ValidationError({
                        'additional_interfaces': f"additionalInterfaces[{idx}] 必须是一个对象"
                    })

                if 'url' not in interface:
                    raise ValidationError({
                        'additional_interfaces': f"additionalInterfaces[{idx}] 必须包含 'url' 字段"
                    })

                if 'transport' not in interface:
                    raise ValidationError({
                        'additional_interfaces': f"additionalInterfaces[{idx}] 必须包含 'transport' 字段"
                    })

                # transport 必须是有效值
                valid_transports = ['JSONRPC', 'GRPC', 'HTTP+JSON']
                if interface['transport'] not in valid_transports:
                    raise ValidationError({
                        'additional_interfaces': (
                            f"additionalInterfaces[{idx}].transport 必须是以下值之一: "
                            f"{', '.join(valid_transports)}"
                        )
                    })

        # 验证9：securitySchemes（可选，但如果存在必须是对象）
        if self.security_schemes:
            if not isinstance(self.security_schemes, dict):
                raise ValidationError({
                    'security_schemes': "securitySchemes 必须是一个对象"
                })

            # 每个 scheme 应该有 type 字段
            valid_security_types = ['APIKey', 'HTTPAuth', 'OAuth2', 'OpenIdConnect', 'MutualTLS']
            for scheme_name, scheme_def in self.security_schemes.items():
                if not isinstance(scheme_def, dict):
                    raise ValidationError({
                        'security_schemes': f"securitySchemes['{scheme_name}'] 必须是一个对象"
                    })

                if 'type' not in scheme_def:
                    raise ValidationError({
                        'security_schemes': f"securitySchemes['{scheme_name}'] 必须包含 'type' 字段"
                    })

                if scheme_def['type'] not in valid_security_types:
                    raise ValidationError({
                        'security_schemes': (
                            f"securitySchemes['{scheme_name}'].type 必须是以下值之一: "
                            f"{', '.join(valid_security_types)}"
                        )
                    })

        # 验证10：security（可选，但如果存在必须是数组）
        if self.security:
            if not isinstance(self.security, list):
                raise ValidationError({
                    'security': "security 必须是一个数组"
                })

            for idx, requirement in enumerate(self.security):
                if not isinstance(requirement, dict):
                    raise ValidationError({
                        'security': f"security[{idx}] 必须是一个对象"
                    })

    def save(self, *args, **kwargs):
        """
        保存前的处理逻辑
        """
        # 完整验证
        self.full_clean()
        super().save(*args, **kwargs)

    # ========================================
    # 业务方法
    # ========================================

    def get_extension(self, schema_uri: str) -> dict:
        """
        安全获取指定 schema 的 L2 扩展数据

        Args:
            schema_uri: Schema URI

        Returns:
            扩展数据字典，如果不存在则返回空字典
        """
        return self.domain_extensions.get(schema_uri, {})

    def set_extension(self, schema_uri: str, data: dict, validate: bool = True):
        """
        设置 L2 扩展数据

        Args:
            schema_uri: Schema URI
            data: 扩展数据
            validate: 是否验证数据（默认 True）

        Raises:
            ValidationError: 当 validate=True 且数据不符合 schema 时
        """
        if validate:
            try:
                schema = SchemaRegistry.objects.get(
                    schema_uri=schema_uri,
                    is_active=True
                )
                is_valid, error_msg = schema.validate_extension_data(data)
                if not is_valid:
                    raise ValidationError(
                        f"数据不符合 Schema '{schema_uri}':\n{error_msg}"
                    )
            except SchemaRegistry.DoesNotExist:
                # 允许设置未注册的 schema（宽松模式）
                pass

        self.domain_extensions[schema_uri] = data
        self.save(update_fields=['domain_extensions', 'updated_at'])

    def remove_extension(self, schema_uri: str):
        """
        移除指定的 L2 扩展
        """
        if schema_uri in self.domain_extensions:
            del self.domain_extensions[schema_uri]
            self.save(update_fields=['domain_extensions', 'updated_at'])

    def to_dict_raw(self, include_metadata: bool = False) -> dict:
        """
        导出原始数据（不做 A2A 协议验证）

        用途：
        - 导出草稿数据（未完成的 AgentCard）
        - 数据备份和迁移
        - 调试和检查

        与 to_agentcard_json() 的区别：
        - to_dict_raw(): 数据库有什么就导出什么，不验证 A2A 协议
        - to_agentcard_json(): 严格验证 A2A 协议，只导出完整的 AgentCard

        Args:
            include_metadata: 是否包含内部元数据（namespace, created_at 等）

        Returns:
            包含所有数据库字段的字典（可能不完整，不保证符合 A2A 协议）
        """
        # 基本字段（按照 A2A 协议结构组织，但不验证）
        card = {
            'protocolVersion': self.protocol_version,
            'name': self.name,
            'description': self.description,
            'url': self.url,
            'preferredTransport': self.preferred_transport,
            'version': self.version,
            'defaultInputModes': self.default_input_modes,
            'defaultOutputModes': self.default_output_modes,
            'skills': self.skills,
        }

        # 组装 capabilities 对象
        capabilities = {}

        # 布尔能力
        if self.capability_streaming:
            capabilities['streaming'] = True
        if self.capability_push_notifications:
            capabilities['pushNotifications'] = True
        if self.capability_state_transition_history:
            capabilities['stateTransitionHistory'] = True

        # extensions 数组
        extensions = []
        for ext in self.extensions.order_by('order', 'uri'):
            ext_dict = {'uri': ext.uri}
            if ext.description:
                ext_dict['description'] = ext.description
            if ext.required:
                ext_dict['required'] = True
            if ext.params:
                ext_dict['params'] = ext.params
            extensions.append(ext_dict)

        if extensions:
            capabilities['extensions'] = extensions

        # capabilities（即使为空也输出）
        card['capabilities'] = capabilities

        # 可选字段（仅在有值时添加）
        if self.provider:
            card['provider'] = self.provider
        if self.icon_url:
            card['iconUrl'] = self.icon_url
        if self.documentation_url:
            card['documentationUrl'] = self.documentation_url
        if self.additional_interfaces:
            card['additionalInterfaces'] = self.additional_interfaces
        if self.security_schemes:
            card['securitySchemes'] = self.security_schemes
        if self.security:
            card['security'] = self.security
        if self.supports_authenticated_extended_card:
            card['supportsAuthenticatedExtendedCard'] = True
        if self.signatures:
            card['signatures'] = self.signatures

        # 可选：添加内部元数据
        if include_metadata:
            card['_metadata'] = {
                'namespace': self.namespace.id,
                'isDefaultVersion': self.is_default_version,
                'isActive': self.is_active,
                'createdAt': self.created_at.isoformat() if self.created_at else None,
                'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
                'createdBy': self.created_by.username if self.created_by else None,
                'updatedBy': self.updated_by.username if self.updated_by else None,
            }

        return card

    def to_agentcard_json(self, include_metadata: bool = False, validate: bool = False) -> dict:
        """
        导出为标准 AgentCard JSON 格式（用于 API 响应和预览）

        Args:
            include_metadata: 是否包含内部元数据（namespace, created_at 等）
            validate: 是否严格验证 A2A 协议必填字段
                     - False（默认）：预览模式，允许不完整数据
                     - True：导出模式，严格验证所有必填字段

        Returns:
            符合 A2A 协议的 AgentCard JSON 对象（validate=False 时可能不完整）

        Raises:
            ValidationError: 如果 validate=True 且 AgentCard 不符合 A2A 协议必填字段要求
        """
        # ========================================
        # 严格 A2A 协议验证（仅在 validate=True 时）
        # ========================================
        # 策略：
        # - 数据库层（clean）：允许渐进式录入，只验证格式
        # - 预览层（validate=False）：显示当前数据状态，允许不完整
        # - 导出层（validate=True）：严格验证必填字段，确保符合 A2A 协议

        if validate:
            errors = {}

            # 1. 基本字段（字符串类型，不能为空）
            if not self.name or not self.name.strip():
                errors['name'] = "name 是 A2A 协议必填字段，不能为空"
            if not self.description or not self.description.strip():
                errors['description'] = "description 是 A2A 协议必填字段，不能为空"
            if not self.url or not self.url.strip():
                errors['url'] = "url 是 A2A 协议必填字段，不能为空"

            # 2. defaultInputModes（必填，不能为空数组）
            if not self.default_input_modes or len(self.default_input_modes) == 0:
                errors['defaultInputModes'] = "defaultInputModes 是 A2A 协议必填字段，不能为空数组"

            # 3. defaultOutputModes（必填，不能为空数组）
            if not self.default_output_modes or len(self.default_output_modes) == 0:
                errors['defaultOutputModes'] = "defaultOutputModes 是 A2A 协议必填字段，不能为空数组"

            # 4. skills（必填，不能为空数组）
            if not self.skills or len(self.skills) == 0:
                errors['skills'] = "skills 是 A2A 协议必填字段，不能为空数组"

            # 如果有错误，抛出异常
            if errors:
                error_msg = "AgentCard 不符合 A2A 协议要求，无法导出：\n"
                for field, msg in errors.items():
                    error_msg += f"  - {field}: {msg}\n"
                error_msg += "\n请先在 Django Admin 中补充完整所有必填字段。"
                raise ValidationError(error_msg)

        # ========================================
        # 构建 AgentCard JSON
        # ========================================
        card = {
            'protocolVersion': self.protocol_version,
            'name': self.name,
            'description': self.description,
            'url': self.url,
            'preferredTransport': self.preferred_transport,
            'version': self.version,
            'defaultInputModes': self.default_input_modes,
            'defaultOutputModes': self.default_output_modes,
            'skills': self.skills,
        }

        # 组装 capabilities 对象（使用新字段结构）
        capabilities = {}

        # 布尔能力
        if self.capability_streaming:
            capabilities['streaming'] = True
        if self.capability_push_notifications:
            capabilities['pushNotifications'] = True
        if self.capability_state_transition_history:
            capabilities['stateTransitionHistory'] = True

        # extensions 数组
        extensions = []
        for ext in self.extensions.order_by('order', 'uri'):
            ext_dict = {'uri': ext.uri}
            if ext.description:
                ext_dict['description'] = ext.description
            if ext.required:
                ext_dict['required'] = True
            if ext.params:
                ext_dict['params'] = ext.params
            extensions.append(ext_dict)

        if extensions:
            capabilities['extensions'] = extensions

        # capabilities 是 A2A 协议必填字段，必须始终输出（即使为空对象）
        card['capabilities'] = capabilities

        # 添加可选字段（仅在有值时添加）
        if self.provider:
            card['provider'] = self.provider
        if self.icon_url:
            card['iconUrl'] = self.icon_url
        if self.documentation_url:
            card['documentationUrl'] = self.documentation_url
        if self.additional_interfaces:
            card['additionalInterfaces'] = self.additional_interfaces
        if self.security_schemes:
            card['securitySchemes'] = self.security_schemes
        if self.security:
            card['security'] = self.security
        if self.supports_authenticated_extended_card:
            card['supportsAuthenticatedExtendedCard'] = True
        if self.signatures:
            card['signatures'] = self.signatures

        # 可选：添加内部元数据（非 A2A 标准，用于内部系统）
        if include_metadata:
            card['_metadata'] = {
                'namespace': self.namespace.id,
                'isDefaultVersion': self.is_default_version,
                'isActive': self.is_active,
                'createdAt': self.created_at.isoformat(),
                'updatedAt': self.updated_at.isoformat(),
            }

        return card

    @classmethod
    def from_agentcard_json(cls, data: dict, namespace_id: str, created_by=None):
        """
        从 AgentCard JSON 创建模型实例（用于数据导入）

        Args:
            data: AgentCard JSON 数据
            namespace_id: 目标命名空间
            created_by: 创建者

        Returns:
            AgentCard 实例（未保存）
        """
        namespace = Namespace.objects.get(id=namespace_id)

        # 提取 L2 扩展（如果存在）
        domain_extensions = data.pop('domainExtensions', {})

        # 字段名映射（JSON camelCase -> Django snake_case）
        field_mapping = {
            'protocolVersion': 'protocol_version',
            'preferredTransport': 'preferred_transport',
            'defaultInputModes': 'default_input_modes',
            'defaultOutputModes': 'default_output_modes',
            'iconUrl': 'icon_url',
            'documentationUrl': 'documentation_url',
            'additionalInterfaces': 'additional_interfaces',
            'securitySchemes': 'security_schemes',
            'supportsAuthenticatedExtendedCard': 'supports_authenticated_extended_card',
        }

        # 转换字段名
        kwargs = {}
        for json_key, model_key in field_mapping.items():
            if json_key in data:
                kwargs[model_key] = data[json_key]

        # 直接映射的字段
        for key in ['name', 'version', 'description', 'url', 'capabilities',
                    'skills', 'provider', 'security', 'signatures']:
            if key in data:
                kwargs[key] = data[key]

        # 创建实例
        instance = cls(
            namespace=namespace,
            domain_extensions=domain_extensions,
            created_by=created_by,
            **kwargs
        )

        return instance


class AgentExtension(models.Model):
    """
    AgentCapabilities.extensions 成员（A2A 协议 5.5.2.1）

    A2A 协议支持通过 Extensions 扩展 AgentCard 的能力和信息。

    常见扩展类型：
    1. Data-only Extensions - 添加结构化信息（不影响请求-响应流程）
       示例：物理资产信息、GDPR 合规性数据
       URI: https://your-org.com/extensions/physical-asset/v1
       params: {"assetId": "HPLC-001", "location": {...}, "status": "OPERATIONAL"}

    2. Method Extensions - 添加新的 RPC 方法
       示例：任务搜索功能 (tasks/search)
       URI: https://a2a.org/extensions/task-history/v1

    3. Profile Extensions - 定义附加状态和约束
       示例：图像生成的子状态 (generating-image)

    参考文档：https://a2a-protocol.org/latest/topics/extensions/
    """

    agent_card = models.ForeignKey(
        AgentCard,
        on_delete=models.CASCADE,
        related_name='extensions',
        help_text="所属 AgentCard"
    )

    uri = models.URLField(
        max_length=512,
        help_text=(
            "扩展的唯一标识 URI（A2A 协议要求）。\n"
            "示例：\n"
            "• Data-only: https://your-org.com/extensions/physical-asset/v1\n"
            "• Method: https://a2a.org/extensions/task-history/v1\n"
            "• Profile: https://your-org.com/extensions/image-generation/v1"
        )
    )

    description = models.TextField(
        blank=True,
        help_text=(
            "扩展说明（可选，A2A 协议字段）。\n"
            "可从 SchemaRegistry 自动填充，或手动定制。"
        )
    )

    required = models.BooleanField(
        default=False,
        help_text=(
            "客户端是否必须理解此扩展（A2A 协议字段）。\n"
            "通常为 false，仅关键扩展设为 true。"
        )
    )

    params = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "扩展特定的配置参数（A2A 协议字段）。\n"
            "• Data-only 扩展：结构化业务数据\n"
            "• Method 扩展：方法配置参数\n"
            "示例：{\"assetId\": \"HPLC-001\", \"status\": \"OPERATIONAL\"}"
        )
    )

    order = models.IntegerField(
        default=0,
        help_text="[可选] 显示顺序（非 A2A 协议字段，仅用于 Admin 界面排序）"
    )

    schema = models.ForeignKey(
        SchemaRegistry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agent_extensions',
        help_text=(
            "[可选] 关联的 Schema 定义（非 A2A 协议字段，内部使用）。\n"
            "用于验证 params 数据结构和自动填充 description。\n"
            "• Data-only 扩展：推荐关联 schema\n"
            "• 其他扩展：可留空"
        )
    )

    class Meta:
        db_table = 'agent_extensions'
        verbose_name = 'Agent扩展'
        verbose_name_plural = 'Agent扩展'
        unique_together = [('agent_card', 'uri')]
        ordering = ['agent_card', 'order', 'uri']
        indexes = [
            models.Index(fields=['agent_card', 'uri']),
        ]

    def __str__(self):
        schema_info = f" ({self.schema.schema_type} {self.schema.version})" if self.schema else ""
        required_marker = " [必需]" if self.required else ""
        return f"{self.uri}{schema_info}{required_marker}"

    def clean(self):
        super().clean()

        # 如果关联了 schema，验证 params 数据
        if self.schema:
            is_valid, error_msg = self.schema.validate_extension_data(self.params)
            if not is_valid:
                raise ValidationError({
                    'params': f"数据不符合 Schema '{self.schema}' 的定义:\n{error_msg}"
                })

            # 自动同步 uri（确保一致性）
            if self.uri != self.schema.schema_uri:
                raise ValidationError({
                    'uri': f"URI 不匹配：字段值为 '{self.uri}'，但关联的 Schema URI 为 '{self.schema.schema_uri}'"
                })

    def save(self, *args, **kwargs):
        # 自动从 schema 填充 uri（如果为空）
        if self.schema and not self.uri:
            self.uri = self.schema.schema_uri

        # 自动从 schema 填充 description（如果为空）
        if self.schema and not self.description:
            self.description = self.schema.description or f"{self.schema.schema_type} {self.schema.version}"

        self.full_clean()
        super().save(*args, **kwargs)
