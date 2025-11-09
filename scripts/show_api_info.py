#!/usr/bin/env python
"""
显示系统 API 端点和功能概览

使用方法：
    docker-compose exec web python show_api_info.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from documents.models import Namespace, SchemaRegistry, AgentCard


def print_section(title, char="="):
    """打印分隔线"""
    print("\n" + char * 70)
    print(f"  {title}")
    print(char * 70 + "\n")


def show_api_endpoints():
    """显示所有 API 端点"""
    print_section("REST API 端点", "=")

    print("🌐 基础 URL: http://localhost:8000/api/\n")

    # Namespace API
    print("📁 1. Namespace API")
    print("   用途：管理命名空间（多环境资源隔离）\n")
    print("   端点：")
    print("   GET    /api/namespaces/          - 列出所有命名空间")
    print("   GET    /api/namespaces/{id}/     - 获取单个命名空间详情")
    print("   POST   /api/namespaces/          - 创建新命名空间")
    print("   PUT    /api/namespaces/{id}/     - 完整更新命名空间")
    print("   PATCH  /api/namespaces/{id}/     - 部分更新命名空间")
    print("   DELETE /api/namespaces/{id}/     - 删除命名空间")
    print()

    # Schema Registry API
    print("📋 2. Schema Registry API")
    print("   用途：管理扩展数据的 Schema 定义\n")
    print("   端点：")
    print("   GET    /api/schemas/             - 列出所有 Schema")
    print("   GET    /api/schemas/{id}/        - 获取单个 Schema 详情")
    print("   POST   /api/schemas/             - 创建新 Schema")
    print("   PUT    /api/schemas/{id}/        - 完整更新 Schema")
    print("   PATCH  /api/schemas/{id}/        - 部分更新 Schema")
    print("   DELETE /api/schemas/{id}/        - 删除 Schema")
    print("   GET    /api/schemas/catalog/     - Schema 目录（发现机制）")
    print()

    # AgentCard API
    print("🤖 3. AgentCard API")
    print("   用途：管理 AgentCard（A2A 协议）\n")
    print("   端点：")
    print("   GET    /api/agentcards/                         - 列出所有 AgentCard")
    print("   GET    /api/agentcards/{id}/                    - 获取单个 AgentCard 详情")
    print("   POST   /api/agentcards/                         - 创建新 AgentCard")
    print("   PUT    /api/agentcards/{id}/                    - 完整更新 AgentCard")
    print("   PATCH  /api/agentcards/{id}/                    - 部分更新 AgentCard")
    print("   DELETE /api/agentcards/{id}/                    - 删除 AgentCard")
    print("   GET    /api/agentcards/{id}/standard-json/      - A2A 协议标准格式")
    print("   GET    /api/agentcards/by-namespace/{ns_id}/    - 按命名空间查询")
    print()

    # 查询参数
    print("🔍 AgentCard API 查询参数：")
    print("   ?namespace=dev             - 按命名空间过滤")
    print("   ?name=HPLC                 - 按名称搜索（模糊匹配）")
    print("   ?is_default_version=true   - 只返回默认版本")
    print("   ?is_active=true            - 只返回激活的")
    print()

    # 权限
    print("🔒 权限控制：")
    print("   读取（GET）：所有人可访问（包括未登录用户）")
    print("   写入（POST/PUT/PATCH/DELETE）：需要登录认证")
    print()


def show_admin_interface():
    """显示 Admin 管理界面信息"""
    print_section("Django Admin 管理界面", "=")

    print("🌐 URL: http://localhost:8000/admin/\n")

    print("📊 功能：")
    print("   1. ✅ 可视化数据录入和编辑")
    print("   2. ✅ AgentCard 创建和管理")
    print("   3. ✅ Schema 定义管理")
    print("   4. ✅ Namespace 管理")
    print("   5. ✅ AgentExtension 内联编辑")
    print("   6. ✅ 数据验证和错误提示")
    print("   7. ✅ JSON 预览功能")
    print()

    print("👥 用户权限：")
    print("   - Superuser：所有权限")
    print("   - Staff：可访问 Admin，但需要配置模型权限")
    print("   - 普通用户：不能访问 Admin")
    print()


def show_data_export():
    """显示数据导出功能"""
    print_section("数据导出功能", "=")

    print("📤 两种导出方法：\n")

    print("1. to_agentcard_json() - A2A 协议标准格式")
    print("   用途：API 对外输出，生产环境")
    print("   验证：严格验证 A2A 协议必填字段")
    print("   使用：")
    print("   ```python")
    print("   card = AgentCard.objects.get(id=1)")
    print("   json_data = card.to_agentcard_json(include_metadata=False)")
    print("   ```")
    print()

    print("2. to_dict_raw() - 原始数据导出")
    print("   用途：草稿导出、备份、调试")
    print("   验证：不验证，数据库有什么导出什么")
    print("   使用：")
    print("   ```python")
    print("   card = AgentCard.objects.get(id=1)")
    print("   raw_data = card.to_dict_raw(include_metadata=True)")
    print("   ```")
    print()


def show_validation():
    """显示验证功能"""
    print_section("数据验证功能", "=")

    print("🔍 两层验证策略：\n")

    print("1. 数据库层验证（保存时）")
    print("   策略：宽松验证，支持渐进式录入")
    print("   验证内容：")
    print("   - ✅ 字段格式（MIME 类型、URL 格式等）")
    print("   - ✅ 数据结构（AgentSkill、AgentProvider 等）")
    print("   - ⚪ 允许空数组（defaultInputModes、skills 等）")
    print()

    print("2. 输出层验证（导出时）")
    print("   策略：严格验证 A2A 协议")
    print("   验证内容：")
    print("   - ✅ 所有必填字段不能为空")
    print("   - ✅ 数组字段不能为空数组")
    print("   - ✅ 100% 符合 A2A 协议 0.3.0 规范")
    print()


def show_database_stats():
    """显示数据库统计"""
    print_section("当前数据统计", "=")

    namespace_count = Namespace.objects.count()
    schema_count = SchemaRegistry.objects.filter(is_active=True).count()
    agentcard_count = AgentCard.objects.count()
    agentcard_active = AgentCard.objects.filter(is_active=True).count()

    print(f"📊 数据库统计：\n")
    print(f"   Namespace：     {namespace_count} 个")
    print(f"   Schema：        {schema_count} 个（活跃）")
    print(f"   AgentCard：     {agentcard_count} 个（总计）")
    print(f"                   {agentcard_active} 个（活跃）")
    print()

    if agentcard_count > 0:
        print("📋 AgentCard 列表：\n")
        for card in AgentCard.objects.filter(is_active=True)[:5]:
            print(f"   {card.namespace.id}::{card.name}@{card.version}")
            print(f"   └─ URL: {card.url}")

        if agentcard_count > 5:
            print(f"   ... 还有 {agentcard_count - 5} 个")
    print()


def show_key_features():
    """显示关键功能特性"""
    print_section("系统关键特性", "=")

    print("✨ 核心功能：\n")

    print("1. 📝 数据录入")
    print("   - Django Admin 可视化界面")
    print("   - 支持渐进式数据填写（草稿功能）")
    print("   - 实时数据验证和错误提示")
    print()

    print("2. 🔌 REST API")
    print("   - 完整的 CRUD 操作")
    print("   - 查询过滤和搜索")
    print("   - A2A 协议标准格式输出")
    print()

    print("3. 📋 Schema 管理")
    print("   - 自定义扩展 Schema 定义")
    print("   - JSON Schema 自动生成")
    print("   - Schema 目录和发现机制")
    print()

    print("4. 🏷️ 命名空间")
    print("   - 多环境资源隔离（dev/test/prod）")
    print("   - 版本管理（默认版本标记）")
    print()

    print("5. ✅ A2A 协议合规")
    print("   - 100% 符合 A2A 0.3.0 规范")
    print("   - AgentCapabilities 支持")
    print("   - Extensions 机制（Data-only、Method、Profile）")
    print()

    print("6. 🔍 数据验证")
    print("   - 两层验证策略（数据库层 + 输出层）")
    print("   - 详细的错误提示")
    print("   - 自动化验证脚本")
    print()


def show_usage_examples():
    """显示使用示例"""
    print_section("快速开始示例", "=")

    print("📖 1. 访问 API\n")
    print("   # 获取所有 AgentCard")
    print("   curl http://localhost:8000/api/agentcards/\n")
    print("   # 获取单个 AgentCard 的 A2A 标准格式")
    print("   curl http://localhost:8000/api/agentcards/1/standard-json/\n")
    print("   # 按命名空间查询")
    print("   curl http://localhost:8000/api/agentcards/?namespace=prod\n")

    print("📖 2. 使用 Python 代码\n")
    print("   ```python")
    print("   from documents.models import AgentCard")
    print()
    print("   # 获取 AgentCard")
    print("   card = AgentCard.objects.get(")
    print("       namespace__id='prod',")
    print("       name='MyAgent',")
    print("       is_default_version=True")
    print("   )")
    print()
    print("   # 导出 A2A 协议格式")
    print("   json_data = card.to_agentcard_json()")
    print()
    print("   # 或导出原始数据（草稿）")
    print("   raw_data = card.to_dict_raw()")
    print("   ```")
    print()


def main():
    """主函数"""
    print("\n" + "🚀" * 35)
    print("   AgentCard 管理系统 - 功能概览")
    print("🚀" * 35)

    # 数据库统计
    show_database_stats()

    # 关键特性
    show_key_features()

    # API 端点
    show_api_endpoints()

    # Admin 界面
    show_admin_interface()

    # 数据导出
    show_data_export()

    # 数据验证
    show_validation()

    # 使用示例
    show_usage_examples()

    # 总结
    print_section("系统架构总结", "=")
    print("📐 架构设计：\n")
    print("   ┌─────────────────────────────────────┐")
    print("   │  用户界面层                          │")
    print("   │  - Django Admin（数据录入）          │")
    print("   │  - DRF 可浏览 API（开发调试）        │")
    print("   └─────────────────┬───────────────────┘")
    print("                     │")
    print("   ┌─────────────────▼───────────────────┐")
    print("   │  API 层（REST API）                 │")
    print("   │  - Namespace CRUD                   │")
    print("   │  - Schema CRUD + Catalog            │")
    print("   │  - AgentCard CRUD + Standard JSON   │")
    print("   └─────────────────┬───────────────────┘")
    print("                     │")
    print("   ┌─────────────────▼───────────────────┐")
    print("   │  业务逻辑层（Models + Validation）   │")
    print("   │  - 两层验证策略                      │")
    print("   │  - A2A 协议合规检查                  │")
    print("   │  - Schema 验证引擎                   │")
    print("   └─────────────────┬───────────────────┘")
    print("                     │")
    print("   ┌─────────────────▼───────────────────┐")
    print("   │  数据持久化层（PostgreSQL）          │")
    print("   │  - Namespace, SchemaRegistry        │")
    print("   │  - AgentCard, AgentExtension        │")
    print("   └─────────────────────────────────────┘")
    print()

    print("💡 典型使用场景：\n")
    print("   1. 内部人员通过 Django Admin 录入和管理 AgentCard")
    print("   2. 其他系统通过 REST API 读取 AgentCard 数据")
    print("   3. 使用 Schema Registry 验证扩展数据格式")
    print("   4. 导出 A2A 协议标准格式用于外部集成")
    print()

    print("📚 相关文档：\n")
    print("   - TWO_LAYER_VALIDATION.md - 两层验证策略详解")
    print("   - RAW_EXPORT_GUIDE.md - 数据导出方法使用指南")
    print("   - ADMIN_GUIDE.md - Admin 界面使用指南")
    print("   - A2A_VALIDATION.md - A2A 协议验证说明")
    print()


if __name__ == '__main__':
    main()
