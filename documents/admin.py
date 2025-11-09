"""
Django Admin 配置
提供友好的可视化界面管理 AgentCard、Schema 和字段定义
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import reverse
import json

from .models import Namespace, SchemaRegistry, SchemaField, AgentCard, AgentExtension


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
        count = obj.agent_extensions.count()

        if count > 0:
            url = reverse('admin:documents_agentextension_changelist') + f'?schema__id__exact={obj.id}'
            return format_html('<a href="{}" title="查看使用此Schema的扩展">{} 个扩展</a>', url, count)
        return '0'
    usage_count.short_description = '使用情况'

    def json_schema_preview(self, obj):
        """显示自动生成的 JSON Schema"""
        if obj.pk:
            schema = obj.generate_json_schema()
            json_str = json.dumps(schema, indent=2, ensure_ascii=False)
            return format_html('<pre style="background:#f5f5f5;padding:10px;border-radius:5px;">{}</pre>', json_str)
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
    extra = 0

    # 字段顺序：核心字段在前，辅助字段在后
    fields = ['uri', 'params', 'description', 'required', 'schema', 'order']
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
        """预览完整的 AgentCard JSON（符合 A2A 规范）"""
        if obj.pk:
            card_json = obj.to_agentcard_json(include_metadata=True)
            json_str = json.dumps(card_json, indent=2, ensure_ascii=False)
            return format_html(
                '<pre style="background:#f5f5f5;padding:10px;border-radius:5px;max-height:400px;overflow:auto;">{}</pre>',
                json_str
            )
        return "保存后生成"
    agentcard_json_preview.short_description = 'AgentCard JSON 预览'

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
# Admin 站点定制
# ========================================

admin.site.site_header = 'AgentCard 管理系统'
admin.site.site_title = 'AgentCard Admin'
admin.site.index_title = '欢迎使用 AgentCard 管理系统'
