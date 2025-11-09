# 数据库约束说明文档

本文档详细列出所有数据库约束，包括强制约束和验证规则。

---

## 1. Namespace（命名空间）

### 唯一性约束
- ✅ **PRIMARY KEY**: `id` 字段（主键）
  - 保证每个命名空间 ID 唯一

### 字段约束
| 字段 | 约束 | 说明 |
|------|------|------|
| `id` | max_length=128, regex=`^[a-zA-Z0-9_-]+$` | 只能包含字母、数字、下划线和连字符 |
| `name` | max_length=255, NOT NULL | 必填，显示名称 |
| `description` | TEXT, nullable | 可选 |
| `is_active` | BOOLEAN, default=True | 软删除标记 |

### 索引
- ✅ 自动索引：`id`（主键自带）
- ✅ `ordering = ['id']`（查询时默认排序）

### 业务规则
- ❌ 无级联删除保护（删除 Namespace 会级联删除所有 AgentCard）
  - **潜在风险**：误删除 namespace 会导致数据丢失

---

## 2. SchemaRegistry（Schema 定义）

### 唯一性约束
- ✅ **UNIQUE**: `schema_uri`（全局唯一）
  - 防止重复注册相同的 Schema URI
- ✅ **UNIQUE_TOGETHER**: `(schema_type, version)`
  - 同一类型的同一版本只能存在一次
  - 例如：`physicalAsset v1` 只能有一个

### 字段约束
| 字段 | 约束 | 说明 |
|------|------|------|
| `schema_uri` | max_length=512, UNIQUE, URL格式 | 必须是合法的 URL |
| `schema_type` | max_length=128, NOT NULL | 必填 |
| `version` | max_length=32, NOT NULL | 必填 |
| `description` | TEXT, nullable | 可选 |
| `example_data` | JSON, nullable | 可选 |
| `is_active` | BOOLEAN, default=True | 软删除标记 |

### 索引
- ✅ `schema_uri`（UNIQUE 自带索引）
- ✅ `(schema_type, version)`（UNIQUE_TOGETHER 自带索引）
- ✅ `schema_type`（db_index=True）
- ✅ `is_active`（db_index=True）
- ✅ 复合索引：`(schema_type, version)`
- ✅ 复合索引：`(is_active, is_deprecated)` - **已删除**（当前版本无此字段）

### 业务规则
- ✅ 删除 Schema 会级联删除所有关联的 SchemaField（on_delete=CASCADE）
- ❌ 无保护：删除被 AgentCard 使用的 Schema
  - **潜在问题**：Schema 被删除后，AgentCard 的 `domain_extensions` 会包含无效的 Schema URI

---

## 3. SchemaField（Schema 字段定义）

### 唯一性约束
- ✅ **UNIQUE_TOGETHER**: `(schema, field_name)`
  - 同一个 Schema 下，字段名不能重复
  - 例如：`physicalAsset v1` 下只能有一个 `locationId` 字段

### 字段约束
| 字段 | 约束 | 说明 |
|------|------|------|
| `schema` | ForeignKey(SchemaRegistry), NOT NULL | 必须关联到某个 Schema |
| `field_name` | max_length=128, regex=`^[a-zA-Z][a-zA-Z0-9_]*$` | 必须以字母开头，只能包含字母、数字、下划线 |
| `field_type` | max_length=32, choices=[...] | 必须是预定义的 9 种类型之一 |
| `is_required` | BOOLEAN, default=False | 默认非必填 |
| `description` | TEXT, nullable | 可选 |
| `default_value` | JSON, nullable | 可选 |
| `min_length` | INTEGER, nullable | 仅 string 类型有效 |
| `max_length` | INTEGER, nullable | 仅 string 类型有效 |
| `min_value` | FLOAT, nullable | 仅 integer/number 类型有效 |
| `max_value` | FLOAT, nullable | 仅 integer/number 类型有效 |
| `enum_choices` | JSON, nullable | 仅 enum 类型有效 |
| `pattern` | max_length=512, nullable | 正则表达式（仅 string 类型） |
| `order` | INTEGER, default=0 | 显示顺序 |

### 索引
- ✅ `(schema, field_name)`（UNIQUE_TOGETHER 自带索引）
- ✅ `ordering = ['schema', 'order', 'field_name']`

### 级联删除
- ✅ `schema` ForeignKey: `on_delete=CASCADE`
  - 删除 Schema 时，所有关联字段自动删除

### 业务规则
- ❌ 无约束检查类型和约束的匹配性
  - **潜在问题**：可以为 `integer` 类型设置 `min_length`（应该是 `min_value`）
  - **缓解措施**：Admin 界面的帮助文本提示正确用法

---

## 4. AgentCard（核心模型）

### 唯一性约束
- ✅ **UNIQUE_TOGETHER**: `(namespace, name, version)`
  - Nacos 风格的三元组唯一性
  - 同一命名空间下，相同名称的不同版本可以共存
  - 例如：`dev::HPLC-001@1.0.0` 和 `dev::HPLC-001@2.0.0` 可以共存

### 默认版本约束
- ✅ **模型级验证**：每个 `(namespace, name)` 只能有一个 `is_default_version=True`
  - 实现位置：`AgentCard.clean()` 方法（370-385行）
  - **注意**：这是 **应用层约束**，不是数据库约束
  - **潜在风险**：直接 SQL 操作可以绕过此约束

### 字段约束

#### 标识字段
| 字段 | 约束 | 说明 |
|------|------|------|
| `namespace` | ForeignKey(Namespace), NOT NULL | 必须关联到某个命名空间 |
| `name` | max_length=64, regex=`^[\x20-\x7E]+$` | ASCII 可打印字符（码位 32-126） |
| `version` | max_length=32, NOT NULL | 必填，建议语义化版本 |
| `is_default_version` | BOOLEAN, default=False | 是否为默认版本 |

#### L1 标准字段（A2A 协议）
| 字段 | 约束 | 说明 |
|------|------|------|
| `protocol_version` | max_length=16, default='0.3.0' | A2A 协议版本 |
| `description` | TEXT, NOT NULL | 必填 |
| `url` | max_length=512, NOT NULL, URL 格式 | 必须是合法 URL |
| `preferred_transport` | max_length=32, choices=[...] | 必须是 http/grpc/websocket 之一 |

#### L1 嵌套对象（JSON 字段）
| 字段 | 约束 | 说明 |
|------|------|------|
| `capabilities` | JSON, default={} | 默认空对象 |
| `default_input_modes` | JSON, default=[] | 默认空数组 |
| `default_output_modes` | JSON, default=[] | 默认空数组 |
| `skills` | JSON, default=[] | 默认空数组 |

#### L1 可选字段
| 字段 | 约束 | 说明 |
|------|------|------|
| `provider` | JSON, nullable | 可选 |
| `icon_url` | max_length=512, nullable, URL 格式 | 可选 |
| `documentation_url` | max_length=512, nullable, URL 格式 | 可选 |
| `additional_interfaces` | JSON, default=[] | 可选 |
| `security_schemes` | JSON, default={} | 可选 |
| `security` | JSON, default=[] | 可选 |
| `supports_authenticated_extended_card` | BOOLEAN, default=False | 可选 |
| `signatures` | JSON, default=[] | 可选 |

#### L2 扩展字段
| 字段 | 约束 | 说明 |
|------|------|------|
| `domain_extensions` | JSON, default={} | 格式：{schema_uri: {field: value}} |

#### 元数据字段
| 字段 | 约束 | 说明 |
|------|------|------|
| `is_active` | BOOLEAN, default=True | 软删除标记 |
| `created_by` | ForeignKey(User), nullable, SET_NULL | 创建者（删除用户时保留记录） |
| `updated_by` | ForeignKey(User), nullable, SET_NULL | 更新者（删除用户时保留记录） |
| `created_at` | TIMESTAMP, auto_now_add=True | 自动设置 |
| `updated_at` | TIMESTAMP, auto_now=True | 自动更新 |

### 索引
- ✅ `(namespace, name, version)`（UNIQUE_TOGETHER 自带索引）
- ✅ `(namespace, name, is_default_version)`（复合索引）
- ✅ `(namespace, is_active)`（复合索引）
- ✅ `created_at`（单列索引）
- ✅ `updated_at`（单列索引）
- ✅ `is_default_version`（db_index=True）
- ✅ `is_active`（db_index=True）
- ⚠️  `domain_extensions`（**需要手动添加 GIN 索引**）

### 级联删除规则
| 关联字段 | on_delete | 影响 |
|----------|-----------|------|
| `namespace` | CASCADE | 删除 Namespace 会删除所有 AgentCard |
| `created_by` | SET_NULL | 删除用户不影响 AgentCard（字段变为 NULL） |
| `updated_by` | SET_NULL | 删除用户不影响 AgentCard（字段变为 NULL） |

### 模型级验证（AgentCard.clean()）

#### 验证1：默认版本唯一性（370-385行）
```python
if self.is_default_version:
    # 检查是否已存在默认版本
    existing_default = AgentCard.objects.filter(
        namespace=self.namespace,
        name=self.name,
        is_default_version=True
    ).exclude(pk=self.pk)

    if existing_default.exists():
        raise ValidationError(...)
```
- **约束级别**：应用层（Python）
- **绕过方式**：直接 SQL 操作

#### 验证2：URL 必须使用 HTTPS（387-391行）
```python
if not self.url.startswith('https://') and not self.url.startswith('http://localhost'):
    raise ValidationError("生产环境的 Agent URL 必须使用 HTTPS")
```
- **约束级别**：应用层
- **例外**：允许 `http://localhost`（开发环境）

#### 验证3：domain_extensions 中的 Schema URI 验证（393-421行）
```python
for schema_uri in self.domain_extensions.keys():
    try:
        schema = SchemaRegistry.objects.get(schema_uri=schema_uri, is_active=True)
        # 验证数据是否符合 Schema 定义
        is_valid, error_msg = schema.validate_extension_data(extension_data)
        if not is_valid:
            raise ValidationError(...)
    except SchemaRegistry.DoesNotExist:
        # 宽松模式：允许未注册的 schema_uri
        pass
```
- **约束级别**：应用层
- **模式**：宽松（允许未注册的 Schema URI）
- **验证内容**：
  - 必填字段检查
  - 类型检查
  - 枚举值检查
  - 字符串长度/数值范围检查

#### 验证4：skills 数组格式（423-433行）
```python
if not isinstance(self.skills, list):
    raise ValidationError("skills 必须是一个数组")

for skill in self.skills:
    if not isinstance(skill, dict) or 'name' not in skill:
        raise ValidationError("每个 skill 必须是包含 'name' 字段的对象")
```
- **约束级别**：应用层

---

## 5. 缺失的约束（潜在问题）

### 高风险

#### 1. 默认版本约束未在数据库层实现
**问题**：
```sql
-- 可以绕过 Django 的验证，直接插入多个默认版本
INSERT INTO agent_cards (namespace_id, name, version, is_default_version, ...)
VALUES ('dev', 'HPLC-001', '1.0.0', true, ...);

INSERT INTO agent_cards (namespace_id, name, version, is_default_version, ...)
VALUES ('dev', 'HPLC-001', '2.0.0', true, ...);  -- 违反业务规则！
```

**解决方案**：
```python
# 方案A：添加数据库约束（PostgreSQL）
class Migration:
    operations = [
        migrations.RunSQL("""
            CREATE UNIQUE INDEX idx_unique_default_version
            ON agent_cards (namespace_id, name)
            WHERE is_default_version = true;
        """),
    ]

# 方案B：使用数据库触发器
# 方案C：接受现状（依赖应用层验证）
```

#### 2. Schema 删除保护
**问题**：
```python
# 删除被 AgentCard 使用的 Schema
schema = SchemaRegistry.objects.get(schema_uri='https://my-org.com/schemas/physicalAsset/v1')
schema.delete()  # 成功删除！

# 但 AgentCard 的 domain_extensions 仍然包含这个 URI
agentcard.domain_extensions['https://my-org.com/schemas/physicalAsset/v1']  # 孤儿数据
```

**解决方案**：
```python
# 方案A：阻止删除
class SchemaRegistry(models.Model):
    def delete(self, *args, **kwargs):
        usage_count = AgentCard.objects.filter(
            domain_extensions__has_key=self.schema_uri
        ).count()

        if usage_count > 0:
            raise ValidationError(
                f"无法删除：有 {usage_count} 个 AgentCard 正在使用此 Schema"
            )

        super().delete(*args, **kwargs)

# 方案B：软删除（只标记 is_active=False）
# 方案C：级联清理（删除 Schema 时，从 AgentCard 中移除对应的扩展）
```

#### 3. Namespace 删除保护
**问题**：
```python
namespace = Namespace.objects.get(id='prod')
namespace.delete()  # 级联删除所有生产环境的 AgentCard！
```

**解决方案**：
```python
class Namespace(models.Model):
    def delete(self, *args, **kwargs):
        card_count = self.agent_cards.count()
        if card_count > 0:
            raise ValidationError(
                f"无法删除：该命名空间下有 {card_count} 个 AgentCard。"
                f"请先删除或移动所有 AgentCard。"
            )
        super().delete(*args, **kwargs)
```

### 中风险

#### 4. JSON 字段格式验证不足
**问题**：
```python
# skills 字段要求是数组，但可以保存任意 JSON
agentcard.skills = {"wrong": "format"}  # 应该是数组！
agentcard.save()  # 在 clean() 中会被捕获，但直接 update() 可绕过
```

**解决方案**：
- 依赖 `clean()` 方法（已实现）
- 始终使用 `save()` 而非 `update()`
- 或使用自定义的 `JSONField` 子类

#### 5. SchemaField 约束与类型不匹配
**问题**：
```python
# 为 integer 类型设置 min_length（应该是 min_value）
field = SchemaField(
    schema=schema,
    field_name='age',
    field_type='integer',
    min_length=18,  # 错误！integer 应该用 min_value
)
field.save()  # 成功保存，但验证时不会生效
```

**解决方案**：
```python
class SchemaField(models.Model):
    def clean(self):
        super().clean()

        # 验证约束与类型的匹配性
        if self.field_type in ['integer', 'number']:
            if self.min_length or self.max_length or self.pattern:
                raise ValidationError("数值类型不能设置长度或正则约束")

        if self.field_type == 'string':
            if self.min_value or self.max_value:
                raise ValidationError("字符串类型不能设置数值范围约束")

        if self.field_type == 'enum':
            if not self.enum_choices:
                raise ValidationError("枚举类型必须设置 enum_choices")
```

### 低风险

#### 6. domain_extensions 的 JSONB 索引未自动创建
**问题**：
- 代码中注释了 GIN 索引（355-356行）
- 需要手动在迁移中添加

**解决方案**：
```python
# 在迁移文件中添加
migrations.RunSQL(
    "CREATE INDEX idx_domain_extensions_gin ON agent_cards USING GIN (domain_extensions jsonb_path_ops);"
)
```

#### 7. 字段长度限制可能不足
| 字段 | 当前限制 | 风险评估 |
|------|----------|----------|
| `schema_uri` | 512 | ✅ 足够（一般 URL < 256） |
| `url` | 512 | ✅ 足够 |
| `name` | 64 | ⚠️  可能不足（复杂名称） |
| `version` | 32 | ✅ 足够（如 '1.0.0-beta.20250101'） |
| `field_name` | 128 | ✅ 足够 |
| `pattern` | 512 | ⚠️  复杂正则可能不足 |

---

## 6. 性能相关约束

### 已有索引（✅ 已实现）
- `Namespace.id`（主键）
- `SchemaRegistry.schema_uri`（UNIQUE）
- `SchemaRegistry.(schema_type, version)`（UNIQUE_TOGETHER）
- `SchemaRegistry.schema_type`（单列索引）
- `SchemaRegistry.is_active`（单列索引）
- `SchemaField.(schema, field_name)`（UNIQUE_TOGETHER）
- `AgentCard.(namespace, name, version)`（UNIQUE_TOGETHER）
- `AgentCard.(namespace, name, is_default_version)`（复合索引）
- `AgentCard.(namespace, is_active)`（复合索引）
- `AgentCard.created_at`（单列索引）
- `AgentCard.updated_at`（单列索引）

### 推荐添加的索引
```sql
-- 1. domain_extensions JSONB GIN 索引（高优先级）
CREATE INDEX idx_domain_extensions_gin
ON agent_cards
USING GIN (domain_extensions jsonb_path_ops);

-- 2. 获取默认版本的复合索引（已有）
-- CREATE INDEX idx_default_version ON agent_cards (namespace_id, name, is_default_version);

-- 3. 按更新时间查询的索引（已有）
-- CREATE INDEX idx_updated_at ON agent_cards (updated_at);

-- 4. Schema 类型过滤（已有）
-- CREATE INDEX idx_schema_type ON schema_registry (schema_type);
```

---

## 7. 并发控制

### 当前状态
- ❌ **无乐观锁**（无 version 字段）
- ❌ **无悲观锁**（未使用 `select_for_update()`）
- ⚠️  **Last-Write-Wins**：后保存的覆盖先保存的

### 潜在问题
```python
# 并发场景：两个用户同时编辑同一个 AgentCard
# 用户A
agentcard = AgentCard.objects.get(id=1)
agentcard.description = "用户A的修改"
# ... 长时间操作 ...
agentcard.save()  # 保存

# 用户B（几乎同时）
agentcard = AgentCard.objects.get(id=1)  # 读取旧数据
agentcard.url = "https://new-url.com"
agentcard.save()  # 覆盖了用户A的 description 修改！
```

### 解决方案（可选）
```python
# 方案A：乐观锁
class AgentCard(models.Model):
    version_number = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.pk:
            updated = AgentCard.objects.filter(
                pk=self.pk,
                version_number=self.version_number
            ).update(
                version_number=F('version_number') + 1,
                **{field: getattr(self, field) for field in updated_fields}
            )
            if not updated:
                raise ConcurrentModificationError("数据已被其他用户修改")
        super().save(*args, **kwargs)

# 方案B：使用 Django 的 select_for_update()
with transaction.atomic():
    agentcard = AgentCard.objects.select_for_update().get(id=1)
    agentcard.description = "修改"
    agentcard.save()
```

---

## 8. 约束总结表

| 约束类型 | 数量 | 说明 |
|----------|------|------|
| **主键约束** | 4 | 每个模型一个 |
| **唯一约束** | 3 | schema_uri, (schema_type+version), (namespace+name+version) |
| **外键约束** | 3 | SchemaField→Schema, AgentCard→Namespace, AgentCard→User(x2) |
| **NOT NULL约束** | ~30 | 大部分必填字段 |
| **CHECK约束** | 0 | ⚠️  未使用数据库级 CHECK |
| **正则验证** | 2 | namespace.id, SchemaField.field_name（应用层） |
| **枚举约束** | 2 | preferred_transport, SchemaField.field_type（应用层） |
| **复合索引** | 5 | 提升查询性能 |
| **GIN索引** | 0 | ⚠️  需要手动添加（domain_extensions） |

---

## 9. 建议的约束增强

### 立即实施（高优先级）
```python
# 1. 添加 JSONB GIN 索引
# 在迁移文件中添加

# 2. Schema 删除保护
class SchemaRegistry(models.Model):
    def delete(self, *args, **kwargs):
        usage_count = AgentCard.objects.filter(
            domain_extensions__has_key=self.schema_uri
        ).count()
        if usage_count > 0:
            raise ValidationError(f"无法删除：有 {usage_count} 个 AgentCard 正在使用")
        super().delete(*args, **kwargs)

# 3. Namespace 删除保护
class Namespace(models.Model):
    def delete(self, *args, **kwargs):
        if self.agent_cards.exists():
            raise ValidationError("无法删除：该命名空间下有 AgentCard")
        super().delete(*args, **kwargs)
```

### 可选实施（中优先级）
```python
# 4. SchemaField 约束与类型匹配验证
class SchemaField(models.Model):
    def clean(self):
        # ... 验证逻辑见上文 ...
        pass

# 5. 默认版本的数据库约束
# 在迁移中添加部分唯一索引
```

### 未来考虑（低优先级）
- 乐观锁（并发控制）
- 审计日志（谁改了什么）
- 字段历史版本（时间旅行）

---

## 总结

当前数据库设计：
- ✅ **基础约束完善**：唯一性、外键、NOT NULL、索引
- ✅ **应用层验证健全**：clean() 方法实现业务规则
- ⚠️  **缺少关键保护**：Schema/Namespace 删除保护、默认版本数据库约束
- ⚠️  **性能优化待完成**：JSONB GIN 索引需要手动添加

**建议行动**：
1. 立即实施高优先级的删除保护
2. 添加 JSONB GIN 索引
3. 根据实际使用情况考虑是否需要并发控制
