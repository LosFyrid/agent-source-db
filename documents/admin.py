"""
Django Admin 配置
提供友好的可视化界面管理 AgentCard、Schema 和字段定义
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import reverse
import json

from .models import Namespace, SchemaRegistry, SchemaField, AgentCard


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
        count = AgentCard.objects.filter(
            domain_extensions__has_key=obj.schema_uri
        ).count()

        if count > 0:
            # 注意：这个过滤器在 Admin 中可能不工作，仅作为链接
            url = reverse('admin:documents_agentcard_changelist')
            return format_html('<a href="{}" title="查看使用此Schema的AgentCard">{} 个 AgentCard</a>', url, count)
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


@admin.register(SchemaField)
class SchemaFieldAdmin(admin.ModelAdmin):
    """
    独立的 SchemaField 管理（备用）
    通常通过 SchemaRegistry 的内联编辑来管理
    """
    list_display = ['schema', 'field_name', 'field_type', 'is_required', 'order']
    list_filter = ['field_type', 'is_required', 'schema__schema_type']
    search_fields = ['field_name', 'description', 'schema__schema_type']
    ordering = ['schema', 'order', 'field_name']

    fieldsets = [
        ('基本信息', {
            'fields': ['schema', 'field_name', 'field_type', 'is_required', 'description', 'order']
        }),
        ('默认值', {
            'fields': ['default_value'],
        }),
        ('约束条件（根据类型选填）', {
            'fields': [
                'enum_choices',
                ('min_length', 'max_length'),
                ('min_value', 'max_value'),
                'pattern'
            ],
            'classes': ['collapse'],
            'description': (
                '根据字段类型填写相应的约束：<br>'
                '- enum: 填写 enum_choices<br>'
                '- string: 可设置 min_length, max_length, pattern<br>'
                '- integer/number: 可设置 min_value, max_value'
            )
        }),
    ]


# ========================================
# AgentCard Admin
# ========================================

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
        ('L1 基本信息（A2A 协议）', {
            'fields': [
                'protocol_version', 'description', 'url', 'preferred_transport',
                'icon_url', 'documentation_url'
            ]
        }),
        ('L1 能力配置', {
            'fields': ['capabilities', 'default_input_modes', 'default_output_modes', 'skills'],
            'classes': ['collapse'],
            'description': '这些字段使用 JSON 格式存储'
        }),
        ('L1 高级选项', {
            'fields': [
                'provider', 'additional_interfaces', 'security_schemes',
                'security', 'supports_authenticated_extended_card', 'signatures'
            ],
            'classes': ['collapse']
        }),
        ('L2 领域扩展', {
            'fields': ['domain_extensions', 'extensions_preview'],
            'description': '使用 Schema URI 作为 key 的扩展数据'
        }),
        ('元数据', {
            'fields': ['created_by', 'updated_by', 'created_at', 'updated_at', 'agentcard_json_preview'],
            'classes': ['collapse']
        }),
    ]

    readonly_fields = ['created_at', 'updated_at', 'extensions_preview', 'agentcard_json_preview']

    def extension_count(self, obj):
        count = len(obj.domain_extensions) if obj.domain_extensions else 0
        if count > 0:
            schema_uris = list(obj.domain_extensions.keys())
            tooltip = '<br>'.join(schema_uris[:3])
            if len(schema_uris) > 3:
                tooltip += f'<br>... 还有 {len(schema_uris) - 3} 个'
            return format_html(
                '<span title="{}">{} 个扩展</span>',
                tooltip, count
            )
        return '0'
    extension_count.short_description = 'L2 扩展数量'

    def extensions_preview(self, obj):
        """预览 L2 扩展（带 Schema 信息）"""
        if not obj.domain_extensions:
            return format_html('<p style="color:#999;">未使用任何扩展</p>')

        html = '<div style="background:#f9f9f9;padding:10px;border-radius:5px;">'

        for schema_uri, data in obj.domain_extensions.items():
            # 尝试获取 Schema 信息
            try:
                schema = SchemaRegistry.objects.get(schema_uri=schema_uri)
                schema_info = f'<strong>{schema.schema_type} {schema.version}</strong>'
                if not schema.is_active:
                    schema_info += ' <span style="color:orange;">[未启用]</span>'
            except SchemaRegistry.DoesNotExist:
                schema_info = f'<span style="color:red;">未注册的 Schema</span>'

            html += f'<div style="margin-bottom:15px;"><p style="margin:5px 0;">{schema_info}</p>'
            html += f'<p style="margin:5px 0;font-size:11px;color:#666;"><code>{schema_uri}</code></p>'
            html += '<div style="background:#fff;padding:8px;border-radius:3px;font-family:monospace;font-size:12px;">'
            html += json.dumps(data, indent=2, ensure_ascii=False)
            html += '</div></div>'

        html += '</div>'
        return format_html(html)
    extensions_preview.short_description = 'L2 扩展预览'

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
# Admin 站点定制
# ========================================

admin.site.site_header = 'AgentCard 管理系统'
admin.site.site_title = 'AgentCard Admin'
admin.site.index_title = '欢迎使用 AgentCard 管理系统'
