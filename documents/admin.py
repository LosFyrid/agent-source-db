"""
Django Admin 配置
提供友好的可视化界面管理 AgentCard、Schema 和字段定义
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import reverse
from django import forms
import json

from .models import Namespace, SchemaRegistry, SchemaField, AgentCard, AgentExtension, AgentCase


# ========================================
# Namespace Admin
# ========================================

@admin.register(Namespace)
class NamespaceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_active', 'agent_card_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['id', 'name', 'description']
    ordering = ['id']

    fieldsets = [
        ('基本信息', {
            'fields': ['id', 'name', 'description', 'is_active']
        }),
        ('统计信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    readonly_fields = ['created_at', 'updated_at']

    def agent_card_count(self, obj):
        count = obj.agent_cards.count()
        if count > 0:
            url = reverse('admin:documents_agentcard_changelist') + f'?namespace__id__exact={obj.id}'
            return format_html('<a href="{}">{} 个 AgentCard</a>', url, count)
        return '0'
    agent_card_count.short_description = 'AgentCard 数量'


# ========================================
# Schema Admin（带内联字段编辑）
# ========================================

class SchemaFieldInline(admin.TabularInline):
    """
    内联编辑 Schema 字段
    允许在 Schema 编辑页面直接管理字段
    """
    model = SchemaField
    extra = 1  # 默认显示1个空行用于添加新字段
    fields = [
        'order', 'field_name', 'field_type', 'is_required',
        'description', 'default_value', 'enum_choices',
        'min_length', 'max_length', 'min_value', 'max_value', 'pattern'
    ]
    ordering = ['order', 'field_name']

    # 根据字段类型显示不同的约束字段
    def get_fieldsets(self, request, obj=None):
        return [
            (None, {
                'fields': [
                    'order', 'field_name', 'field_type', 'is_required', 'description'
                ]
            }),
            ('约束条件', {
                'fields': [
                    'default_value', 'enum_choices',
                    ('min_length', 'max_length'),
                    ('min_value', 'max_value'),
                    'pattern'
                ],
                'classes': ['collapse']
            }),
        ]


@admin.register(SchemaRegistry)
class SchemaRegistryAdmin(admin.ModelAdmin):
    list_display = [
        'schema_type', 'version', 'is_active',
        'field_count', 'usage_count', 'created_at'
    ]
    list_filter = ['is_active', 'schema_type', 'created_at']
    search_fields = ['schema_uri', 'schema_type', 'description']
    ordering = ['schema_type', '-version']

    fieldsets = [
        ('基本信息', {
            'fields': ['schema_uri', 'schema_type', 'version', 'description', 'is_active']
        }),
        ('示例数据', {
            'fields': ['example_data'],
            'classes': ['collapse'],
            'description': '可选：提供一个示例数据对象，帮助开发者理解如何使用'
        }),
        ('预览', {
            'fields': ['json_schema_preview', 'field_list_preview'],
            'classes': ['collapse'],
        }),
        ('时间戳', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    readonly_fields = ['created_at', 'updated_at', 'json_schema_preview', 'field_list_preview']

    inlines = [SchemaFieldInline]

    def field_count(self, obj):
        count = obj.fields.count()
        return f'{count} 个字段'
    field_count.short_description = '字段数量'

    def usage_count(self, obj):
        """显示有多少个 AgentCard 使用了此 Schema"""
        count = obj.agent_extensions.count()

        if count > 0:
            # 获取使用此 schema 的 AgentCard ID 列表
            agentcard_ids = obj.agent_extensions.values_list('agent_card_id', flat=True).distinct()
            agentcard_count = agentcard_ids.count()

            # 链接到使用此 schema 的 AgentCard 列表
            if agentcard_count > 0:
                # 构建过滤 URL，显示包含使用此 schema 的扩展的 AgentCard
                url = reverse('admin:documents_agentcard_changelist')
                return format_html(
                    '<a href="{}" title="被 {} 个 AgentCard 使用（共 {} 次）">{} 个 AgentCard 使用</a>',
                    url, agentcard_count, count, agentcard_count
                )
            return f'{count} 个扩展'
        return '0'
    usage_count.short_description = '使用情况'

    def json_schema_preview(self, obj):
        """显示自动生成的 JSON Schema"""
        if obj.pk:
            try:
                schema = obj.generate_json_schema()
                json_str = json.dumps(schema, indent=2, ensure_ascii=False)
                return format_html('<pre style="background:#f5f5f5;padding:10px;border-radius:5px;">{}</pre>', json_str)
            except Exception as e:
                return format_html('<div style="color:red;padding:10px;background:#ffe0e0;border-radius:5px;">生成失败：{}</div>', str(e))
        return "保存后生成"
    json_schema_preview.short_description = '自动生成的 JSON Schema'

    def field_list_preview(self, obj):
        """显示字段列表（易读格式）"""
        if obj.pk:
            fields = obj.get_field_definitions()
            if not fields:
                return format_html('<p style="color:#999;">尚未定义字段</p>')

            html = '<table style="width:100%; border-collapse:collapse;">'
            html += '<tr style="background:#f0f0f0;"><th style="padding:8px;text-align:left;">字段名</th><th style="padding:8px;text-align:left;">类型</th><th style="padding:8px;text-align:left;">必填</th><th style="padding:8px;text-align:left;">说明</th></tr>'

            for field in fields:
                required_badge = '<span style="color:red;">*</span>' if field['required'] else ''
                html += f'<tr><td style="padding:8px;border-top:1px solid #ddd;"><code>{field["name"]}</code> {required_badge}</td>'
                html += f'<td style="padding:8px;border-top:1px solid #ddd;">{field["type"]}</td>'
                html += f'<td style="padding:8px;border-top:1px solid #ddd;">{"是" if field["required"] else "否"}</td>'
                html += f'<td style="padding:8px;border-top:1px solid #ddd;">{field["description"] or "-"}</td></tr>'

            html += '</table>'
            return format_html(html)
        return "保存后显示"
    field_list_preview.short_description = '字段列表'

    def save_model(self, request, obj, form, change):
        """保存时的提示"""
        super().save_model(request, obj, form, change)
        if not change:  # 新建
            self.message_user(request, f'Schema "{obj.schema_type} {obj.version}" 已创建。现在可以添加字段了。')


# SchemaField 不单独注册到 Admin，只通过 SchemaRegistry 的 inline 编辑
# 这样可以简化侧边栏，避免导航混乱
#
# 如果需要独立管理 SchemaField，取消下面的注释：
#
# @admin.register(SchemaField)
# class SchemaFieldAdmin(admin.ModelAdmin):
#     """
#     独立的 SchemaField 管理（备用）
#     通常通过 SchemaRegistry 的内联编辑来管理
#     """
#     list_display = ['schema', 'field_name', 'field_type', 'is_required', 'order']
#     list_filter = ['field_type', 'is_required', 'schema__schema_type']
#     search_fields = ['field_name', 'description', 'schema__schema_type']
#     ordering = ['schema', 'order', 'field_name']
#
#     fieldsets = [
#         ('基本信息', {
#             'fields': ['schema', 'field_name', 'field_type', 'is_required', 'description', 'order']
#         }),
#         ('默认值', {
#             'fields': ['default_value'],
#         }),
#         ('约束条件（根据类型选填）', {
#             'fields': [
#                 'enum_choices',
#                 ('min_length', 'max_length'),
#                 ('min_value', 'max_value'),
#                 'pattern'
#             ],
#             'classes': ['collapse'],
#             'description': (
#                 '根据字段类型填写相应的约束：<br>'
#                 '- enum: 填写 enum_choices<br>'
#                 '- string: 可设置 min_length, max_length, pattern<br>'
#                 '- integer/number: 可设置 min_value, max_value'
#             )
#         }),
#     ]


# ========================================
# AgentCard Admin
# ========================================

class AgentExtensionForm(forms.ModelForm):
    """
    自定义表单用于 AgentExtension
    - 触发 params 验证（基于关联的 schema）
    - 自动填充 URI（从 schema.schema_uri）
    """
    class Meta:
        model = AgentExtension
        fields = '__all__'

    def clean(self):
        """自动填充 URI 并验证 params 数据"""
        cleaned_data = super().clean()

        # 自动填充 URI（如果选择了 schema 但 URI 为空）
        schema = cleaned_data.get('schema')
        uri = cleaned_data.get('uri')

        if schema and not uri:
            cleaned_data['uri'] = schema.schema_uri

        # 验证 params 数据（如果关联了 schema）
        if schema:
            params = cleaned_data.get('params', {})
            is_valid, error_msg = schema.validate_extension_data(params)
            if not is_valid:
                raise forms.ValidationError({
                    'params': f"数据不符合 Schema '{schema}' 的定义:\n{error_msg}"
                })

        return cleaned_data


class AgentExtensionInline(admin.TabularInline):
    """
    内联编辑 Agent 扩展（AgentCapabilities.extensions）

    A2A 协议支持通过 Extensions 机制扩展 AgentCard 的能力和信息。

    常见扩展类型：
    1. Data-only Extensions - 添加结构化信息到 AgentCard
       示例：物理资产信息、GDPR 合规性数据
       URI: https://your-org.com/extensions/physical-asset/v1
       params: {"assetId": "HPLC-001", "location": {...}, "status": "OPERATIONAL"}

    2. Method Extensions - 添加新的 RPC 方法
       示例：任务搜索功能
       URI: https://a2a.org/extensions/task-history/v1

    3. Profile Extensions - 定义附加状态和约束
       示例：图像生成的子状态

    参考：https://a2a-protocol.org/latest/topics/extensions/
    """
    model = AgentExtension
    form = AgentExtensionForm  # 使用自定义表单
    extra = 0

    # 字段顺序：核心字段在前，辅助字段在后
    fields = ['schema', 'uri', 'params', 'description', 'required', 'order']
    autocomplete_fields = ['schema']
    ordering = ['order', 'uri']

    verbose_name = "扩展"
    verbose_name_plural = "Agent 扩展（AgentCapabilities.extensions）"


@admin.register(AgentCard)
class AgentCardAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'namespace', 'version', 'is_default_version',
        'is_active', 'extension_count', 'updated_at'
    ]
    list_filter = ['namespace', 'is_default_version', 'is_active', 'preferred_transport', 'created_at']
    search_fields = ['name', 'description', 'url']
    ordering = ['namespace', 'name', '-version']

    fieldsets = [
        ('标识', {
            'fields': ['namespace', 'name', 'version', 'is_default_version', 'is_active']
        }),
        ('L1 基本信息', {
            'fields': [
                'protocol_version', 'description', 'url', 'preferred_transport',
                'icon_url', 'documentation_url'
            ]
        }),
        ('AgentCapabilities（协议能力）', {
            'fields': [
                'capability_streaming',
                'capability_push_notifications',
                'capability_state_transition_history',
            ],
            'description': (
                'AgentCapabilities 对象（A2A 5.5.2）：声明可选的协议特性。\n'
                '• 勾选 Agent 支持的能力\n'
                '• extensions 在下方 "Agent扩展" 区域管理（支持 Data-only、Method、Profile 等扩展类型）'
            )
        }),
        ('输入输出模式和技能', {
            'fields': [
                'default_input_modes',
                'default_output_modes',
                'skills'
            ],
            'description': (
                'AgentCard 顶层字段（非 capabilities）：\n'
                '• defaultInputModes: 支持的输入 MIME 类型\n'
                '• defaultOutputModes: 支持的输出 MIME 类型\n'
                '• skills: Agent 提供的技能列表'
            )
        }),
        ('高级选项', {
            'fields': [
                'provider', 'additional_interfaces', 'security_schemes',
                'security', 'supports_authenticated_extended_card', 'signatures'
            ],
            'classes': ['collapse']
        }),
        ('元数据', {
            'fields': ['created_by', 'updated_by', 'created_at', 'updated_at', 'agentcard_json_preview'],
            'classes': ['collapse']
        }),
    ]

    readonly_fields = ['created_at', 'updated_at', 'agentcard_json_preview']

    inlines = [AgentExtensionInline]

    def extension_count(self, obj):
        count = obj.extensions.count()
        if count > 0:
            extensions = obj.extensions.all()[:3]
            tooltip = '<br>'.join([ext.uri for ext in extensions])
            if count > 3:
                tooltip += f'<br>... 还有 {count - 3} 个'
            return format_html(
                '<span title="{}">{} 个扩展</span>',
                tooltip, count
            )
        return '0'
    extension_count.short_description = '扩展数量'


    def agentcard_json_preview(self, obj):
        """预览完整的 AgentCard JSON（允许不完整数据）"""
        if obj.pk:
            try:
                # 预览模式：validate=False，允许显示不完整的数据
                card_json = obj.to_agentcard_json(include_metadata=True, validate=False)
                json_str = json.dumps(card_json, indent=2, ensure_ascii=False)

                # 检查是否缺少必填字段（提示但不阻止显示）
                warnings = []
                if not obj.name or not obj.name.strip():
                    warnings.append('name')
                if not obj.description or not obj.description.strip():
                    warnings.append('description')
                if not obj.url or not obj.url.strip():
                    warnings.append('url')
                if not obj.default_input_modes or len(obj.default_input_modes) == 0:
                    warnings.append('defaultInputModes')
                if not obj.default_output_modes or len(obj.default_output_modes) == 0:
                    warnings.append('defaultOutputModes')
                if not obj.skills or len(obj.skills) == 0:
                    warnings.append('skills')

                warning_html = ''
                if warnings:
                    warning_html = format_html(
                        '<div style="color:#856404;background:#fff3cd;padding:10px;border-radius:5px;margin-bottom:10px;">'
                        '<strong>⚠️ 预览模式（数据不完整）</strong><br>'
                        '以下 A2A 协议必填字段缺失，导出到生产环境前需要补充：<br>'
                        '• {}'
                        '</div>',
                        '<br>• '.join(warnings)
                    )

                return format_html(
                    '{}<pre style="background:#f5f5f5;padding:10px;border-radius:5px;max-height:400px;overflow:auto;">{}</pre>',
                    warning_html,
                    json_str
                )
            except Exception as e:
                return format_html(
                    '<div style="color:red;padding:10px;background:#ffe0e0;border-radius:5px;">生成预览失败：{}</div>',
                    str(e)
                )
        return "保存后生成"
    agentcard_json_preview.short_description = 'AgentCard JSON 预览（允许不完整）'

    def save_model(self, request, obj, form, change):
        """保存时自动设置创建者/更新者"""
        if not change:  # 新建
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ========================================
# AgentExtension Admin（独立管理）
# ========================================

# AgentExtension 不单独注册到 Admin，只通过 AgentCard 的 inline 编辑
# 这样可以简化侧边栏，避免导航混乱
#
# 如果需要独立管理 AgentExtension，取消下面的注释：
#
# @admin.register(AgentExtension)
# class AgentExtensionAdmin(admin.ModelAdmin):
#     """
#     AgentExtension 独立管理
#     通常通过 AgentCardAdmin 的内联编辑来管理
#     """
#     list_display = ['uri', 'agent_card', 'schema', 'required', 'order']
#     list_filter = ['required', 'schema']
#     search_fields = ['uri', 'description', 'agent_card__name']
#     ordering = ['agent_card', 'order', 'uri']
#     autocomplete_fields = ['agent_card', 'schema']
#
#     fieldsets = [
#         ('基本信息', {
#             'fields': ['agent_card', 'uri', 'schema', 'order']
#         }),
#         ('配置', {
#             'fields': ['description', 'required', 'params']
#         }),
#     ]


# ========================================
# AgentCase Admin
# ========================================

@admin.register(AgentCase)
class AgentCaseAdmin(admin.ModelAdmin):
    """
    AgentCase 管理界面
    """
    list_display = [
        'case_name', 'agent_card_link', 'agent_version_display',
        'is_ground_truth', 'outcome_type', 'case_score',
        'created_by', 'created_at'
    ]
    list_filter = [
        'is_ground_truth', 'outcome_type', 'agent_card',
        'created_at', 'agent_version'
    ]
    search_fields = [
        'case_name', 'query_key', 'query_description',
        'agent_card__name', 'agent_card__namespace__id'
    ]
    ordering = ['-created_at']
    autocomplete_fields = ['agent_card']

    fieldsets = [
        ('基本信息', {
            'fields': ['case_name', 'agent_card', 'agent_version', 'is_ground_truth']
        }),
        ('查询字段', {
            'fields': ['query_key', 'query_description', 'query_value']
        }),
        ('执行结果', {
            'fields': ['outcome_type', 'outcome_data', 'outcome_file', 'outcome_notes']
        }),
        ('路由和评分', {
            'fields': ['route_to', 'case_score']
        }),
        ('审计信息', {
            'fields': ['created_at', 'updated_at', 'created_by', 'updated_by'],
            'classes': ['collapse']
        }),
    ]

    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def agent_card_link(self, obj):
        """显示关联的AgentCard链接"""
        if obj.agent_card:
            url = reverse('admin:documents_agentcard_change', args=[obj.agent_card.id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                f"{obj.agent_card.namespace.id}::{obj.agent_card.name}"
            )
        return '未分配'
    agent_card_link.short_description = 'Agent'

    def agent_version_display(self, obj):
        """显示版本号，特殊值标记颜色"""
        if not obj.agent_version or obj.agent_version == '*':
            return format_html('<span style="color: green;">* (通用)</span>')
        elif obj.agent_version == 'latest':
            return format_html('<span style="color: blue;">latest</span>')
        else:
            return obj.agent_version
    agent_version_display.short_description = '版本'

    def save_model(self, request, obj, form, change):
        """保存时自动设置创建人/更新人"""
        if not change:  # 创建时
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ========================================
# Admin 站点定制
# ========================================

admin.site.site_header = 'AgentCard 管理系统'
admin.site.site_title = 'AgentCard Admin'
admin.site.index_title = '欢迎使用 AgentCard 管理系统'
