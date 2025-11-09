#!/usr/bin/env python
"""
直接测试 API 功能（使用 Django 测试客户端）
"""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from documents.models import Namespace, SchemaRegistry, SchemaField, AgentCard


def test_api():
    print("=" * 60)
    print("AgentCard API 完整功能测试")
    print("=" * 60)
    print()

    # 确保有测试用户
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass')
        user.save()
        print("✓ 创建测试用户: testuser")
    else:
        print("✓ 使用现有测试用户: testuser")
    print()

    # ==========================================
    # 测试 1: 创建测试数据
    # ==========================================
    print("[1] 创建测试数据")
    print("-" * 60)

    # 1.1 创建 Namespace
    print("1.1 创建 Namespace...")
    ns_dev, created = Namespace.objects.get_or_create(
        id='dev',
        defaults={
            'name': '开发环境',
            'description': '用于开发和测试',
            'is_active': True
        }
    )
    print(f"  ✓ Namespace 'dev': {ns_dev}")

    ns_prod, created = Namespace.objects.get_or_create(
        id='prod',
        defaults={
            'name': '生产环境',
            'description': '生产环境',
            'is_active': True
        }
    )
    print(f"  ✓ Namespace 'prod': {ns_prod}")
    print()

    # 1.2 创建 Schema
    print("1.2 创建 Schema...")
    schema, created = SchemaRegistry.objects.get_or_create(
        schema_uri='https://example.com/schemas/physicalAsset/v1',
        defaults={
            'schema_type': 'physicalAsset',
            'version': 'v1',
            'description': '物理资产基础信息',
            'example_data': {
                'physicalAssetId': 'HPLC-001',
                'locationId': 'Lab-A',
                'status': 'OPERATIONAL'
            },
            'is_active': True
        }
    )
    print(f"  ✓ Schema: {schema}")

    # 1.3 为 Schema 添加字段
    if created or schema.fields.count() == 0:
        print("  添加 Schema 字段...")

        SchemaField.objects.get_or_create(
            schema=schema,
            field_name='physicalAssetId',
            defaults={
                'field_type': 'string',
                'is_required': True,
                'description': '物理资产编号',
                'min_length': 3,
                'max_length': 64,
                'order': 1
            }
        )

        SchemaField.objects.get_or_create(
            schema=schema,
            field_name='locationId',
            defaults={
                'field_type': 'string',
                'is_required': True,
                'description': '位置ID',
                'order': 2
            }
        )

        SchemaField.objects.get_or_create(
            schema=schema,
            field_name='status',
            defaults={
                'field_type': 'enum',
                'is_required': True,
                'description': '运行状态',
                'enum_choices': ['OPERATIONAL', 'MAINTENANCE', 'OFFLINE'],
                'order': 3
            }
        )
        print("  ✓ 添加了 3 个字段")
    else:
        print(f"  ✓ Schema 已有 {schema.fields.count()} 个字段")
    print()

    # 1.4 创建 AgentCard
    print("1.3 创建 AgentCard...")

    card1, created = AgentCard.objects.get_or_create(
        namespace=ns_dev,
        name='HPLC-001',
        version='1.0.0',
        defaults={
            'is_default_version': True,
            'is_active': True,
            'protocol_version': '0.3.0',
            'description': 'Agilent 1260 高效液相色谱仪',
            'url': 'https://lab.example.com/instruments/hplc-001',
            'preferred_transport': 'http',
            'capabilities': {'streaming': False, 'tools': True},
            'default_input_modes': ['application/json', 'text/plain'],
            'default_output_modes': ['application/json'],
            'skills': [
                {
                    'name': 'runAnalysis',
                    'description': '运行液相色谱分析',
                    'inputModes': ['application/json'],
                    'outputModes': ['application/json']
                },
                {
                    'name': 'getStatus',
                    'description': '获取仪器状态',
                    'inputModes': ['text/plain'],
                    'outputModes': ['application/json']
                }
            ],
            'domain_extensions': {
                'https://example.com/schemas/physicalAsset/v1': {
                    'physicalAssetId': 'HPLC-001',
                    'locationId': 'BuildingA-Lab1-Rack2',
                    'status': 'OPERATIONAL'
                }
            },
            'created_by': user
        }
    )
    print(f"  ✓ AgentCard 1: {card1}")

    card2, created = AgentCard.objects.get_or_create(
        namespace=ns_dev,
        name='HPLC-001',
        version='2.0.0',
        defaults={
            'is_default_version': False,
            'is_active': True,
            'protocol_version': '0.3.0',
            'description': 'Agilent 1260 高效液相色谱仪（增强版）',
            'url': 'https://lab.example.com/instruments/hplc-001',
            'preferred_transport': 'http',
            'capabilities': {'streaming': True, 'tools': True},
            'default_input_modes': ['application/json'],
            'default_output_modes': ['application/json'],
            'skills': [
                {
                    'name': 'runAnalysis',
                    'description': '运行液相色谱分析',
                    'inputModes': ['application/json'],
                    'outputModes': ['application/json']
                }
            ],
            'domain_extensions': {
                'https://example.com/schemas/physicalAsset/v1': {
                    'physicalAssetId': 'HPLC-001',
                    'locationId': 'BuildingA-Lab1-Rack2',
                    'status': 'OPERATIONAL'
                }
            },
            'created_by': user
        }
    )
    print(f"  ✓ AgentCard 2: {card2}")

    card3, created = AgentCard.objects.get_or_create(
        namespace=ns_prod,
        name='LC-MS-001',
        version='1.0.0',
        defaults={
            'is_default_version': True,
            'is_active': True,
            'protocol_version': '0.3.0',
            'description': '液质联用仪',
            'url': 'https://lab.example.com/instruments/lcms-001',
            'preferred_transport': 'http',
            'capabilities': {'streaming': False, 'tools': True},
            'default_input_modes': ['application/json'],
            'default_output_modes': ['application/json'],
            'skills': [
                {
                    'name': 'runAnalysis',
                    'description': '运行质谱分析',
                    'inputModes': ['application/json'],
                    'outputModes': ['application/json']
                }
            ],
            'domain_extensions': {},
            'created_by': user
        }
    )
    print(f"  ✓ AgentCard 3: {card3}")
    print()

    # ==========================================
    # 测试 2: 查询统计
    # ==========================================
    print("[2] 查询统计")
    print("-" * 60)

    print(f"Namespace 总数: {Namespace.objects.count()}")
    print(f"Schema 总数: {SchemaRegistry.objects.count()}")
    print(f"AgentCard 总数: {AgentCard.objects.count()}")
    print()

    for ns in Namespace.objects.all():
        count = ns.agent_cards.count()
        print(f"  {ns.id}: {count} 个 AgentCard")
    print()

    # ==========================================
    # 测试 3: API 端点测试（使用 curl）
    # ==========================================
    print("[3] API 端点测试")
    print("-" * 60)
    print("访问以下 URL 测试 API：")
    print()

    print("3.1 API 根路径:")
    print("  http://localhost:8000/api/")
    print()

    print("3.2 Namespaces:")
    print("  列表: http://localhost:8000/api/namespaces/")
    print("  详情: http://localhost:8000/api/namespaces/dev/")
    print()

    print("3.3 Schemas:")
    print("  列表: http://localhost:8000/api/schemas/")
    print(f"  详情: http://localhost:8000/api/schemas/{schema.id}/")
    print("  目录: http://localhost:8000/api/schemas/catalog/")
    print()

    print("3.4 AgentCards:")
    print("  列表: http://localhost:8000/api/agentcards/")
    print(f"  详情: http://localhost:8000/api/agentcards/{card1.id}/")
    print(f"  标准JSON: http://localhost:8000/api/agentcards/{card1.id}/standard_json/")
    print("  过滤-命名空间: http://localhost:8000/api/agentcards/?namespace=dev")
    print("  过滤-默认版本: http://localhost:8000/api/agentcards/?is_default_version=true")
    print("  过滤-名称: http://localhost:8000/api/agentcards/?name=HPLC")
    print("  按命名空间: http://localhost:8000/api/agentcards/by-namespace/dev/")
    print()

    # ==========================================
    # 测试 4: 具体功能测试
    # ==========================================
    print("[4] 功能验证")
    print("-" * 60)

    # 4.1 Schema 自动生成 JSON Schema
    print("4.1 Schema 自动生成的 JSON Schema:")
    print(json.dumps(schema.generate_json_schema(), indent=2))
    print()

    # 4.2 AgentCard 导出标准 JSON
    print("4.2 AgentCard 标准 JSON（A2A 协议）:")
    print(json.dumps(card1.to_agentcard_json(), indent=2))
    print()

    # 4.3 验证扩展数据
    print("4.3 验证扩展数据:")
    ext_data = card1.domain_extensions.get('https://example.com/schemas/physicalAsset/v1', {})
    is_valid, error = schema.validate_extension_data(ext_data)
    if is_valid:
        print(f"  ✓ 扩展数据验证通过")
    else:
        print(f"  ✗ 扩展数据验证失败: {error}")
    print()

    # ==========================================
    # 总结
    # ==========================================
    print("=" * 60)
    print("✓ 所有测试数据创建完成！")
    print("=" * 60)
    print()
    print("下一步:")
    print("1. 浏览器访问: http://localhost:8000/api/")
    print("2. 使用可浏览 API 交互界面")
    print("3. 或使用 curl 测试（见上面的 URL 列表）")
    print()


if __name__ == '__main__':
    test_api()
