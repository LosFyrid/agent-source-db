# Generated manually for adding database-level constraints

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        # 1. 添加 JSONB GIN 索引（提升 domain_extensions 查询性能）
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS idx_domain_extensions_gin
                ON agent_cards
                USING GIN (domain_extensions jsonb_path_ops);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_domain_extensions_gin;"
        ),

        # 2. 添加部分唯一索引（确保每个 namespace::name 只有一个默认版本）
        # PostgreSQL 部分索引：只在 is_default_version=true 时生效
        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_default_version
                ON agent_cards (namespace_id, name)
                WHERE is_default_version = true;
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_unique_default_version;",
        ),

        # 3. 添加注释（方便后续维护）
        migrations.RunSQL(
            sql="""
                COMMENT ON INDEX idx_domain_extensions_gin IS
                'GIN 索引用于快速查询使用特定 Schema URI 的 AgentCard';

                COMMENT ON INDEX idx_unique_default_version IS
                '部分唯一索引：确保每个 (namespace, name) 只有一个默认版本';
            """,
            reverse_sql="-- 注释会随索引删除而消失",
        ),
    ]
