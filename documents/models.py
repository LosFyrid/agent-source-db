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
        删除前检查：如果有 AgentCard 正在使用此 Schema，禁止删除
        """
        # 需要导入 AgentCard（避免循环导入）
        from .models import AgentCard

        usage_count = AgentCard.objects.filter(
            domain_extensions__has_key=self.schema_uri
        ).count()

        if usage_count > 0:
            raise ValidationError(
                f"无法删除 Schema '{self.schema_type} {self.version}'："
                f"有 {usage_count} 个 AgentCard 正在使用此 Schema。"
                f"请先更新或删除这些 AgentCard。"
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
            ('http', 'HTTP/REST'),
            ('grpc', 'gRPC'),
            ('websocket', 'WebSocket'),
        ],
        default='http',
        help_text="首选传输协议"
    )

    # ========================================
    # L1 嵌套对象（使用 JSONField 存储）
    # ========================================

    capabilities = models.JSONField(
        default=dict,
        blank=True,
        help_text="AgentCapabilities 对象，如 {'streaming': true, 'tools': true, 'responseFormats': ['text', 'json']}"
    )
    default_input_modes = models.JSONField(
        default=list,
        help_text="支持的输入 MIME 类型数组，如 ['text/plain', 'application/json', 'image/png']"
    )
    default_output_modes = models.JSONField(
        default=list,
        help_text="支持的输出 MIME 类型数组，如 ['text/plain', 'application/json']"
    )
    skills = models.JSONField(
        default=list,
        help_text=(
            "AgentSkill 数组，每个 skill 包含: "
            "{name, description, inputModes?, outputModes?, parameters?}"
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
    # L2 扩展字段（核心设计）
    # ========================================

    domain_extensions = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "L2 领域扩展数据，使用 Schema URI 作为命名空间。\n"
            "格式: {schema_uri: {field: value, ...}, ...}\n"
            "示例: {'https://my-org.com/schemas/physicalAsset/v1': "
            "{'physicalAssetId': 'HPLC-001', 'locationId': 'Lab-A', 'status': 'OPERATIONAL'}}"
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
        模型级别的数据验证
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

        # 验证2：URL 必须使用 HTTPS（除非是开发环境的 localhost）
        if not self.url.startswith('https://') and not self.url.startswith('http://localhost'):
            raise ValidationError({
                'url': "生产环境的 Agent URL 必须使用 HTTPS"
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

        # 验证4：skills 数组格式
        if not isinstance(self.skills, list):
            raise ValidationError({
                'skills': "skills 必须是一个数组"
            })

        for skill in self.skills:
            if not isinstance(skill, dict) or 'name' not in skill:
                raise ValidationError({
                    'skills': "每个 skill 必须是包含 'name' 字段的对象"
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

    def to_agentcard_json(self, include_metadata: bool = False) -> dict:
        """
        导出为标准 AgentCard JSON 格式（用于 API 响应）

        Args:
            include_metadata: 是否包含内部元数据（namespace, created_at 等）

        Returns:
            符合 A2A 协议的 AgentCard JSON 对象
        """
        card = {
            'protocolVersion': self.protocol_version,
            'name': self.name,
            'description': self.description,
            'url': self.url,
            'preferredTransport': self.preferred_transport,
            'version': self.version,
            'capabilities': self.capabilities,
            'defaultInputModes': self.default_input_modes,
            'defaultOutputModes': self.default_output_modes,
            'skills': self.skills,
        }

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

        # 添加 L2 扩展（仅在有数据时添加）
        if self.domain_extensions:
            card['domainExtensions'] = self.domain_extensions

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
