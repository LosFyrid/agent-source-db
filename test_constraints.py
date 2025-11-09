#!/usr/bin/env python
"""
测试数据库约束是否正常工作

使用方法：
    docker-compose exec web python test_constraints.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from documents.models import Namespace, SchemaRegistry, SchemaField, AgentCard


def test_unique_default_version():
    """测试：每个 namespace::name 只能有一个默认版本"""
    print("\n=== 测试1：默认版本唯一性约束 ===")

    # 创建测试命名空间
    namespace, _ = Namespace.objects.get_or_create(
        id='test',
        defaults={'name': '测试环境', 'description': '用于约束测试'}
    )

    # 清理旧数据
    AgentCard.objects.filter(namespace=namespace, name='TestAgent').delete()

    try:
        # 创建第一个默认版本
        card1 = AgentCard.objects.create(
            namespace=namespace,
            name='TestAgent',
            version='1.0.0',
            is_default_version=True,
            description='测试Agent v1',
            url='https://test.com/v1',
            protocol_version='0.3.0',
            preferred_transport='http',
            capabilities={},
            default_input_modes=['text/plain'],
            default_output_modes=['text/plain'],
            skills=[{'name': 'test', 'description': 'test skill'}],
        )
        print(f"✓ 创建第一个默认版本成功: {card1}")

        # 尝试创建第二个默认版本（应该失败）
        try:
            card2 = AgentCard(
                namespace=namespace,
                name='TestAgent',
                version='2.0.0',
                is_default_version=True,
                description='测试Agent v2',
                url='https://test.com/v2',
                protocol_version='0.3.0',
                preferred_transport='http',
                capabilities={},
                default_input_modes=['text/plain'],
                default_output_modes=['text/plain'],
                skills=[{'name': 'test', 'description': 'test skill'}],
            )
            card2.save()  # 这里应该抛出异常
            print("✗ 错误：允许创建第二个默认版本（约束未生效）")
            return False

        except (ValidationError, IntegrityError) as e:
            print(f"✓ 正确阻止第二个默认版本: {type(e).__name__}")

        # 清理
        card1.delete()
        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_namespace_delete_protection():
    """测试：有 AgentCard 的 Namespace 无法删除"""
    print("\n=== 测试2：Namespace 删除保护 ===")

    # 创建测试数据
    namespace, _ = Namespace.objects.get_or_create(
        id='test-delete',
        defaults={'name': '删除测试', 'description': '测试删除保护'}
    )

    card, _ = AgentCard.objects.get_or_create(
        namespace=namespace,
        name='TestAgent',
        version='1.0.0',
        defaults={
            'description': '测试Agent',
            'url': 'https://test.com',
            'protocol_version': '0.3.0',
            'preferred_transport': 'http',
            'capabilities': {},
            'default_input_modes': ['text/plain'],
            'default_output_modes': ['text/plain'],
            'skills': [{'name': 'test', 'description': 'test'}],
        }
    )

    try:
        # 尝试删除有 AgentCard 的 Namespace（应该失败）
        namespace.delete()
        print("✗ 错误：允许删除有 AgentCard 的 Namespace（保护未生效）")
        return False

    except ValidationError as e:
        print(f"✓ 正确阻止删除: {e}")

        # 删除 AgentCard 后，应该可以删除 Namespace
        card.delete()
        namespace.delete()
        print("✓ 删除 AgentCard 后，成功删除 Namespace")
        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_schema_delete_protection():
    """测试：被 AgentCard 使用的 Schema 无法删除"""
    print("\n=== 测试3：Schema 删除保护 ===")

    # 创建测试 Schema
    schema, _ = SchemaRegistry.objects.get_or_create(
        schema_uri='https://test.com/schemas/test/v1',
        defaults={
            'schema_type': 'testSchema',
            'version': 'v1',
            'description': '测试Schema',
        }
    )

    # 创建使用该 Schema 的 AgentCard
    namespace, _ = Namespace.objects.get_or_create(
        id='test-schema',
        defaults={'name': 'Schema测试'}
    )

    card, created = AgentCard.objects.get_or_create(
        namespace=namespace,
        name='TestAgent',
        version='1.0.0',
        defaults={
            'description': '测试Agent',
            'url': 'https://test.com',
            'protocol_version': '0.3.0',
            'preferred_transport': 'http',
            'capabilities': {},
            'default_input_modes': ['text/plain'],
            'default_output_modes': ['text/plain'],
            'skills': [{'name': 'test', 'description': 'test'}],
            'domain_extensions': {
                'https://test.com/schemas/test/v1': {
                    'testField': 'testValue'
                }
            }
        }
    )

    if not created:
        # 更新现有记录的 domain_extensions
        card.domain_extensions = {
            'https://test.com/schemas/test/v1': {
                'testField': 'testValue'
            }
        }
        card.save()

    try:
        # 尝试删除被使用的 Schema（应该失败）
        schema.delete()
        print("✗ 错误：允许删除被使用的 Schema（保护未生效）")
        return False

    except ValidationError as e:
        print(f"✓ 正确阻止删除: {e}")

        # 删除 AgentCard 后，应该可以删除 Schema
        card.delete()
        schema.delete()
        namespace.delete()
        print("✓ 删除 AgentCard 后，成功删除 Schema")
        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        # 清理
        try:
            card.delete()
            schema.delete()
            namespace.delete()
        except:
            pass
        return False


def test_schema_field_constraints():
    """测试：SchemaField 约束与类型匹配验证"""
    print("\n=== 测试4：SchemaField 约束验证 ===")

    schema, _ = SchemaRegistry.objects.get_or_create(
        schema_uri='https://test.com/schemas/field-test/v1',
        defaults={
            'schema_type': 'fieldTest',
            'version': 'v1',
            'description': '字段测试Schema',
        }
    )

    # 测试1：integer 类型不能设置 min_length
    print("\n  测试4.1：integer 不能设置 min_length")
    try:
        field = SchemaField(
            schema=schema,
            field_name='age',
            field_type='integer',
            min_length=1,  # 错误！应该用 min_value
        )
        field.clean()  # 只触发 clean() 验证
        print("  ✗ 错误：允许为 integer 设置 min_length")
        success_1 = False
    except ValidationError as e:
        print(f"  ✓ 正确阻止: {e}")
        success_1 = True

    # 测试2：string 类型不能设置 min_value
    print("\n  测试4.2：string 不能设置 min_value")
    try:
        field = SchemaField(
            schema=schema,
            field_name='name',
            field_type='string',
            min_value=10,  # 错误！应该用 min_length
        )
        field.clean()
        print("  ✗ 错误：允许为 string 设置 min_value")
        success_2 = False
    except ValidationError as e:
        print(f"  ✓ 正确阻止: {e}")
        success_2 = True

    # 测试3：enum 类型必须设置 enum_choices
    print("\n  测试4.3：enum 必须设置 enum_choices")
    try:
        field = SchemaField(
            schema=schema,
            field_name='status',
            field_type='enum',
            # 缺少 enum_choices
        )
        field.clean()
        print("  ✗ 错误：允许 enum 类型不设置 enum_choices")
        success_3 = False
    except ValidationError as e:
        print(f"  ✓ 正确阻止: {e}")
        success_3 = True

    # 清理
    schema.delete()

    return success_1 and success_2 and success_3


def test_gin_index_performance():
    """测试：GIN 索引是否存在"""
    print("\n=== 测试5：GIN 索引检查 ===")

    try:
        from django.db import connection

        # 直接查询索引是否存在
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'agent_cards'
                AND indexname IN ('idx_domain_extensions_gin', 'idx_unique_default_version');
            """)
            indexes = cursor.fetchall()

            if len(indexes) >= 2:
                print("✓ 发现约束索引:")
                for idx_name, idx_def in indexes:
                    print(f"  - {idx_name}")
                    if 'gin' in idx_def.lower():
                        print(f"    类型: GIN (用于 JSONB 查询优化)")
                    elif 'where' in idx_def.lower():
                        print(f"    类型: 部分唯一索引 (默认版本约束)")
                return True
            else:
                print(f"⚠ 只找到 {len(indexes)} 个索引（期望2个）")
                return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("数据库约束测试")
    print("=" * 60)

    results = []

    results.append(("默认版本唯一性", test_unique_default_version()))
    results.append(("Namespace删除保护", test_namespace_delete_protection()))
    results.append(("Schema删除保护", test_schema_delete_protection()))
    results.append(("SchemaField约束验证", test_schema_field_constraints()))
    results.append(("GIN索引", test_gin_index_performance()))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{name:20} {status}")

    all_passed = all(success for _, success in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！约束工作正常。")
    else:
        print("✗ 部分测试失败，请检查日志。")
    print("=" * 60)
