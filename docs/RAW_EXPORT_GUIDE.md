# 原始数据导出方法使用指南

**新增方法**: `AgentCard.to_dict_raw()`
**实施日期**: 2025-11-09
**目的**: 支持导出不完整的 AgentCard 数据，用于草稿、备份和调试

---

## 方法对比

系统现在提供两个导出方法：

| 特性 | `to_dict_raw()` | `to_agentcard_json()` |
|------|----------------|----------------------|
| **A2A 协议验证** | ❌ 不验证 | ✅ 严格验证 |
| **导出不完整数据** | ✅ 允许 | ❌ 不允许 |
| **抛出 ValidationError** | ❌ 不抛出 | ✅ 数据不完整时抛出 |
| **输出格式** | A2A 协议结构 | A2A 协议结构 |
| **包含元数据选项** | ✅ 支持 | ✅ 支持 |
| **主要用途** | 草稿/备份/调试 | API 对外输出 |

---

## 方法1: to_dict_raw()

### 方法签名

```python
def to_dict_raw(self, include_metadata: bool = False) -> dict:
    """
    导出原始数据（不做 A2A 协议验证）

    Args:
        include_metadata: 是否包含内部元数据（namespace, created_at 等）

    Returns:
        包含所有数据库字段的字典（可能不完整，不保证符合 A2A 协议）
    """
```

### 特点

- ✅ **数据库有什么就导出什么**
- ✅ **不验证 A2A 协议必填字段**
- ✅ **允许导出空数组**（defaultInputModes、defaultOutputModes、skills）
- ✅ **不会抛出 ValidationError**
- ✅ **按照 A2A 协议结构组织数据**（但不保证完整性）

### 适用场景

#### 1. 导出草稿数据

当 AgentCard 尚未填写完整时，可以导出当前状态：

```python
# 创建不完整的 AgentCard（草稿）
card = AgentCard(
    namespace=namespace,
    name="My Draft Agent",
    version="0.1.0",
    description="工作进行中...",
    url="https://example.com/agent",
    # defaultInputModes, defaultOutputModes, skills 尚未填写
)
card.save()  # ✅ 可以保存

# 导出草稿数据
draft_data = card.to_dict_raw()
print(json.dumps(draft_data, indent=2))
# ✅ 成功导出，即使字段不完整
```

**输出示例**:
```json
{
  "protocolVersion": "0.3.0",
  "name": "My Draft Agent",
  "description": "工作进行中...",
  "url": "https://example.com/agent",
  "preferredTransport": "JSONRPC",
  "version": "0.1.0",
  "defaultInputModes": [],  // ← 空数组也能导出
  "defaultOutputModes": [],  // ← 空数组也能导出
  "skills": [],              // ← 空数组也能导出
  "capabilities": {}
}
```

#### 2. 数据备份和迁移

导出所有 AgentCard 数据（包括不完整的）进行备份：

```python
# 备份所有 AgentCard（包括草稿）
all_cards = AgentCard.objects.all()
backup_data = []

for card in all_cards:
    # 使用 to_dict_raw() 确保所有数据都能导出
    card_data = card.to_dict_raw(include_metadata=True)
    backup_data.append(card_data)

# 保存到文件
with open('agentcard_backup.json', 'w') as f:
    json.dump(backup_data, f, indent=2, ensure_ascii=False)

print(f"✅ 已备份 {len(backup_data)} 个 AgentCard（包括草稿）")
```

#### 3. 调试和检查

在开发过程中查看数据库中的实际数据：

```python
# 调试：查看 AgentCard 的实际数据
card = AgentCard.objects.get(id=123)

# 导出所有字段（包括内部元数据）
debug_data = card.to_dict_raw(include_metadata=True)

print("📊 数据库中的实际数据:")
print(json.dumps(debug_data, indent=2, ensure_ascii=False))

# 输出包含：
# - 所有 A2A 字段（即使为空）
# - _metadata（namespace, isActive, createdAt 等）
```

#### 4. 内部工具和脚本

编写内部工具时，需要访问所有数据：

```python
# 统计脚本：查看哪些 AgentCard 尚未完成
incomplete_cards = []

for card in AgentCard.objects.all():
    data = card.to_dict_raw()

    # 检查是否完整
    if (not data['defaultInputModes'] or
        not data['defaultOutputModes'] or
        not data['skills']):
        incomplete_cards.append({
            'id': card.id,
            'name': card.name,
            'missing_fields': []
        })

        if not data['defaultInputModes']:
            incomplete_cards[-1]['missing_fields'].append('defaultInputModes')
        if not data['defaultOutputModes']:
            incomplete_cards[-1]['missing_fields'].append('defaultOutputModes')
        if not data['skills']:
            incomplete_cards[-1]['missing_fields'].append('skills')

# 生成报告
print(f"📋 发现 {len(incomplete_cards)} 个不完整的 AgentCard:")
for card in incomplete_cards:
    print(f"  - {card['name']}: 缺少 {', '.join(card['missing_fields'])}")
```

---

## 方法2: to_agentcard_json()

### 方法签名

```python
def to_agentcard_json(self, include_metadata: bool = False) -> dict:
    """
    导出为标准 AgentCard JSON 格式（用于 API 响应）

    Args:
        include_metadata: 是否包含内部元数据（namespace, created_at 等）

    Returns:
        符合 A2A 协议的 AgentCard JSON 对象

    Raises:
        ValidationError: 如果 AgentCard 不符合 A2A 协议必填字段要求
    """
```

### 特点

- ✅ **严格验证 A2A 协议必填字段**
- ✅ **不允许导出不完整的数据**
- ✅ **抛出 ValidationError（如果数据不完整）**
- ✅ **100% 符合 A2A 协议 0.3.0 规范**

### 适用场景

#### 1. API 对外暴露数据

```python
# API 视图
def get_agentcard(request, namespace, name):
    card = AgentCard.objects.get(
        namespace__id=namespace,
        name=name,
        is_default_version=True
    )

    try:
        # 使用 to_agentcard_json() 确保符合 A2A 协议
        card_json = card.to_agentcard_json()
        return JsonResponse(card_json)
    except ValidationError as e:
        # 不完整的 AgentCard 不会对外暴露
        return JsonResponse({
            'error': 'AgentCard 数据不完整',
            'details': str(e)
        }, status=400)
```

#### 2. 验证数据完整性

```python
# 发布前检查
def check_ready_for_production(card):
    """检查 AgentCard 是否可以发布到生产环境"""
    try:
        # 尝试生成 A2A 协议 JSON
        card.to_agentcard_json()
        return True, "✅ 数据完整，可以发布"
    except ValidationError as e:
        return False, f"❌ 数据不完整: {e}"

# 使用
card = AgentCard.objects.get(id=123)
ready, message = check_ready_for_production(card)
print(message)
```

#### 3. 生产环境数据输出

```python
# 生成 .well-known/agent.json 文件
def generate_agent_json_file(card):
    """生成 A2A 协议标准的 agent.json 文件"""
    try:
        # 严格验证后生成
        agent_json = card.to_agentcard_json()

        with open('.well-known/agent.json', 'w') as f:
            json.dump(agent_json, f, indent=2, ensure_ascii=False)

        print("✅ 已生成 agent.json 文件")
    except ValidationError as e:
        print(f"❌ 无法生成文件，数据不完整: {e}")
```

---

## 使用建议

### 开发流程建议

```
1. 创建 AgentCard
   ↓
2. 分步填写数据（保存草稿）
   ↓ 使用 to_dict_raw() 查看当前状态
3. 补充必填字段
   ↓
4. 验证完整性
   ↓ 使用 to_agentcard_json() 验证
5. 发布到生产环境
   ↓ 只使用 to_agentcard_json() 对外输出
```

### 配合使用示例

```python
# 开发阶段：创建和编辑
card = AgentCard(...)
card.save()  # ✅ 允许保存草稿

# 随时查看当前状态
draft = card.to_dict_raw()
print("当前进度:", draft)

# 补充数据...
card.default_input_modes = ['text/plain']
card.default_output_modes = ['text/plain']
card.skills = [...]
card.save()

# 验证是否完整
try:
    final_json = card.to_agentcard_json()
    print("✅ 数据完整，可以发布！")
except ValidationError as e:
    print(f"❌ 还需要补充: {e}")

# 生产环境：只使用验证过的方法
if settings.ENV == 'production':
    return card.to_agentcard_json()  # ✅ 确保符合协议
else:
    return card.to_dict_raw()  # ⚠️  开发环境可以查看草稿
```

---

## 包含元数据

两个方法都支持 `include_metadata=True` 参数：

```python
# 导出包含内部元数据
data = card.to_dict_raw(include_metadata=True)

# 输出包含 _metadata 字段：
{
  "protocolVersion": "0.3.0",
  "name": "My Agent",
  ...,
  "_metadata": {
    "namespace": "prod",
    "isDefaultVersion": true,
    "isActive": true,
    "createdAt": "2025-11-09T10:00:00Z",
    "updatedAt": "2025-11-09T12:00:00Z",
    "createdBy": "admin",
    "updatedBy": "developer"
  }
}
```

**用途**:
- 数据备份（保留完整的内部状态）
- 数据迁移（跨系统传输）
- 审计和追踪

---

## 测试验证

### 测试脚本

运行 `test_raw_export.py` 来验证两个方法的行为：

```bash
docker-compose exec web python test_raw_export.py
```

### 测试结果

```
✅ 测试1: 完整的 AgentCard
   - to_dict_raw(): ✅ 成功
   - to_agentcard_json(): ✅ 成功

✅ 测试2: 不完整的 AgentCard
   - to_dict_raw(): ✅ 成功（导出草稿）
   - to_agentcard_json(): ✅ 正确拦截

✅ 测试3: 包含元数据
   - to_dict_raw(include_metadata=True): ✅ 成功
```

---

## 常见问题

### Q1: 什么时候用 to_dict_raw()？

**A**: 当你需要导出不完整的数据时：
- 草稿状态的 AgentCard
- 数据备份（包括未完成的）
- 内部调试和检查

### Q2: 什么时候用 to_agentcard_json()？

**A**: 当你需要确保数据符合 A2A 协议时：
- API 对外输出
- 生产环境
- 需要 100% 协议合规的场景

### Q3: to_dict_raw() 是否会验证数据？

**A**: 不会。它直接导出数据库中的所有字段，不做任何验证。即使 defaultInputModes 为空数组，也会原样导出。

### Q4: 两个方法的输出格式有区别吗？

**A**: 输出格式相同（都按照 A2A 协议结构组织），但内容可能不同：
- `to_dict_raw()`: 可能包含空数组
- `to_agentcard_json()`: 保证所有必填字段都有值

### Q5: 可以在生产环境使用 to_dict_raw() 吗？

**A**: 技术上可以，但不建议。生产环境应该只使用 `to_agentcard_json()` 来确保数据质量。`to_dict_raw()` 更适合开发和调试。

---

## 代码实现

### 位置

**文件**: `documents/models.py`
**行号**: 1069-1160

### 核心逻辑

```python
def to_dict_raw(self, include_metadata: bool = False) -> dict:
    # 直接组装数据，不做 A2A 协议验证
    card = {
        'protocolVersion': self.protocol_version,
        'name': self.name,
        'description': self.description,
        'url': self.url,
        'preferredTransport': self.preferred_transport,
        'version': self.version,
        'defaultInputModes': self.default_input_modes,  # ← 允许空数组
        'defaultOutputModes': self.default_output_modes,  # ← 允许空数组
        'skills': self.skills,  # ← 允许空数组
    }

    # 组装 capabilities...
    # 添加可选字段...
    # 添加元数据（如果需要）...

    return card  # ← 不抛出 ValidationError
```

---

## 总结

### 设计优势

1. **灵活性**: 开发时可以导出草稿数据
2. **安全性**: 生产环境仍然有严格验证
3. **可追溯**: 支持导出元数据用于审计
4. **易用性**: 两个方法接口一致，容易切换

### 最佳实践

```python
# ✅ 推荐
if is_development:
    data = card.to_dict_raw()  # 开发环境：查看草稿
else:
    data = card.to_agentcard_json()  # 生产环境：严格验证

# ❌ 不推荐
data = card.to_dict_raw()  # 生产环境不推荐用此方法
return JsonResponse(data)  # 可能返回不完整的数据
```

---

**最后更新**: 2025-11-09
**相关文档**: TWO_LAYER_VALIDATION.md, IMPLEMENTATION_SUMMARY.md
