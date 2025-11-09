# 两层验证策略说明

**实施日期**: 2025-11-09
**目的**: 支持渐进式数据录入，同时确保输出符合 A2A 协议

---

## 架构设计理念

根据实际业务需求，AgentCard 管理系统采用**两层验证策略**：

1. **数据库层（宽松验证）**：允许用户分步骤填写数据，支持保存草稿
2. **输出层（严格验证）**：确保对外输出（API）的数据 100% 符合 A2A 协议

---

## 为什么需要两层验证？

### 业务场景

在实际使用中，用户可能需要：
- 先创建 AgentCard 的基本信息，稍后补充详细配置
- 分批次填写复杂的 skills 和 extensions 数据
- 保存半成品数据作为草稿，避免数据丢失

### 技术需求

同时，系统必须保证：
- 对外输出（API）的数据严格符合 A2A 协议规范
- 不允许将不完整的 AgentCard 暴露给外部系统
- 格式验证始终生效，保证数据质量

---

## 实现方案

### 1. 数据库层验证（models.py: clean()）

**位置**: `AgentCard.clean()` 方法（第 732-1020 行）

**策略**: 宽松验证 - 只验证格式，允许为空

**验证内容**:

| 字段 | 允许为空？ | 格式验证 |
|------|-----------|----------|
| `defaultInputModes` | ✅ 允许空数组 | ✅ MIME 类型格式（type/subtype） |
| `defaultOutputModes` | ✅ 允许空数组 | ✅ MIME 类型格式 |
| `skills` | ✅ 允许空数组 | ✅ AgentSkill 结构和字段类型 |
| `provider` | ✅ 可选字段 | ✅ AgentProvider 结构 |
| `additionalInterfaces` | ✅ 可选字段 | ✅ AdditionalInterface 结构 |
| `securitySchemes` | ✅ 可选字段 | ✅ SecurityScheme 结构 |

**代码示例**:

```python
# 验证4：defaultInputModes（格式验证，允许为空）
if self.default_input_modes:  # ← 只在有值时验证
    for mode in self.default_input_modes:
        if '/' not in mode:
            raise ValidationError({
                'default_input_modes': f"'{mode}' 不是有效的 MIME 类型格式"
            })
```

**结果**:
- ✅ 用户可以保存部分填写的 AgentCard
- ✅ 格式错误仍然会被拦截（如 MIME 类型缺少 `/`）
- ✅ 支持渐进式数据录入

---

### 2. 输出层验证（models.py: to_agentcard_json()）

**位置**: `AgentCard.to_agentcard_json()` 方法（第 1066-1195 行）

**策略**: 严格验证 - 确保所有 A2A 必填字段都已填写

**验证内容**:

| 字段 | 验证要求 |
|------|---------|
| `name` | ❌ 不能为空字符串 |
| `description` | ❌ 不能为空字符串 |
| `url` | ❌ 不能为空字符串 |
| `defaultInputModes` | ❌ 不能为空数组 |
| `defaultOutputModes` | ❌ 不能为空数组 |
| `skills` | ❌ 不能为空数组 |

**代码示例**:

```python
def to_agentcard_json(self, include_metadata: bool = False) -> dict:
    # 严格 A2A 协议验证
    errors = {}

    if not self.default_input_modes or len(self.default_input_modes) == 0:
        errors['defaultInputModes'] = "defaultInputModes 是 A2A 协议必填字段，不能为空数组"

    if errors:
        raise ValidationError("AgentCard 不符合 A2A 协议要求，无法生成 JSON 输出...")

    # 构建 AgentCard JSON
    card = {...}
    return card
```

**结果**:
- ✅ 只有完整的 AgentCard 才能生成 JSON 输出
- ✅ API 对外暴露的数据 100% 符合 A2A 协议
- ✅ 用户会收到清晰的错误提示，知道哪些字段需要补充

---

## 字段配置变更

为支持渐进式录入，以下字段添加了 `blank=True`：

```python
# 第 597-614 行
default_input_modes = models.JSONField(
    default=list,
    blank=True,  # ← 新增：允许为空（数据库层）
    help_text="...（A2A 必填，但数据库层允许暂时为空以支持渐进式录入）"
)

default_output_modes = models.JSONField(
    default=list,
    blank=True,  # ← 新增
    help_text="...（A2A 必填，但数据库层允许暂时为空以支持渐进式录入）"
)

skills = models.JSONField(
    default=list,
    blank=True,  # ← 新增
    help_text="...（A2A 必填，但数据库层允许暂时为空以支持渐进式录入）"
)
```

**迁移文件**: `documents/migrations/0007_allow_progressive_entry.py`

---

## 测试验证

### 测试脚本

`test_two_layer_validation.py` - 完整的两层验证测试

### 测试场景

| 场景 | 描述 | 结果 |
|------|------|------|
| 场景1 | 保存部分填写的 AgentCard（空数组） | ✅ 允许保存 |
| 场景2 | 对部分填写的 AgentCard 调用 `to_agentcard_json()` | ✅ 抛出 ValidationError |
| 场景3 | 补充完整后调用 `to_agentcard_json()` | ✅ 成功生成 JSON |
| 场景4 | 保存格式错误的数据（MIME 类型缺少 `/`） | ✅ 数据库层拦截 |

### 测试结果

```bash
docker-compose exec web python test_two_layer_validation.py
```

**输出**:
```
✅ 两层验证策略工作正常：
   1. 数据库层：允许渐进式录入，只验证格式
   2. 输出层：严格验证必填字段，确保 A2A 协议合规
```

---

## 使用示例

### 示例1：渐进式录入

```python
from documents.models import Namespace, AgentCard

namespace = Namespace.objects.get(id='my-namespace')

# 步骤1：创建基本信息（保存草稿）
card = AgentCard(
    namespace=namespace,
    name="My Agent",
    version="1.0.0",
    description="An example agent",
    url="https://example.com/agent",
    # defaultInputModes, defaultOutputModes, skills 暂时留空
)
card.save()  # ✅ 允许保存

# 步骤2：尝试生成 JSON（会失败）
try:
    json_output = card.to_agentcard_json()
except ValidationError as e:
    print(e)  # ❌ "defaultInputModes 是 A2A 协议必填字段，不能为空数组"

# 步骤3：补充完整后再生成 JSON
card.default_input_modes = ['text/plain']
card.default_output_modes = ['text/plain']
card.skills = [{
    'id': 'skill-1',
    'name': 'Example Skill',
    'description': 'A test skill',
    'tags': ['test']
}]
card.save()

json_output = card.to_agentcard_json()  # ✅ 成功
```

### 示例2：格式验证

```python
# 格式错误会在数据库层被拦截
card = AgentCard(
    namespace=namespace,
    name="My Agent",
    version="1.0.0",
    description="Test",
    url="https://example.com/agent",
    default_input_modes=['invalid'],  # ❌ 格式错误：缺少 '/'
    default_output_modes=['text/plain'],
    skills=[...]
)

try:
    card.save()
except ValidationError as e:
    print(e)  # ❌ "'invalid' 不是有效的 MIME 类型格式（应为 'type/subtype'）"
```

---

## 用户体验优势

### 对数据录入人员

1. **灵活性**：可以分多次、分步骤填写 AgentCard
2. **容错性**：不会因为某个字段未填写而导致整个数据丢失
3. **清晰反馈**：当尝试输出时，会明确提示哪些字段需要补充

### 对 API 消费者

1. **数据质量保证**：通过 API 获取的 AgentCard 100% 符合 A2A 协议
2. **一致性**：不会收到不完整或格式错误的数据
3. **可靠性**：可以直接使用 API 数据，无需额外验证

---

## 技术总结

### 验证层次对比

| 验证层 | 位置 | 时机 | 策略 | 目的 |
|--------|------|------|------|------|
| 数据库层 | `clean()` | 保存时 | 宽松 | 支持渐进式录入 |
| 输出层 | `to_agentcard_json()` | 导出时 | 严格 | 确保 A2A 合规 |

### 关键实现

1. **字段配置**: `blank=True` 允许保存空数组
2. **数据库验证**: `if self.field:` 只在有值时验证格式
3. **输出验证**: `if not self.field or len(self.field) == 0:` 严格检查
4. **错误提示**: 详细的 ValidationError 消息指导用户

---

## 协议一致性

### A2A 协议必填字段

根据 A2A 协议 0.3.0 规范（Section 5.5），以下字段为必填：

1. ✅ `protocolVersion`: string (default: "0.3.0")
2. ✅ `name`: string
3. ✅ `description`: string
4. ✅ `url`: string (HTTPS)
5. ✅ `preferredTransport`: "JSONRPC" | "GRPC" | "HTTP+JSON"
6. ✅ `version`: string
7. ✅ `capabilities`: AgentCapabilities (can be {})
8. ✅ `defaultInputModes`: string[] (non-empty)
9. ✅ `defaultOutputModes`: string[] (non-empty)
10. ✅ `skills`: AgentSkill[] (non-empty)

**输出层验证确保所有字段都符合要求** ✅

---

## 维护指南

### 添加新的必填字段

如需添加新的 A2A 必填字段：

1. **数据库层**: 添加字段，设置 `blank=True`（如果允许渐进式录入）
2. **clean() 方法**: 添加格式验证（`if self.field:` 条件块）
3. **to_agentcard_json() 方法**: 添加严格验证（检查非空）
4. **测试**: 更新 `test_two_layer_validation.py`

### 修改验证逻辑

- **格式验证**: 修改 `clean()` 方法
- **必填验证**: 修改 `to_agentcard_json()` 方法
- **两层都需要**: 两个方法都修改

---

**最后更新**: 2025-11-09
**测试状态**: ✅ 全部通过
**A2A 协议版本**: 0.3.0
