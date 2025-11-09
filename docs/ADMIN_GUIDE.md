# AgentCard Admin 使用指南

**更新日期**: 2025-11-09
**A2A 协议版本**: 0.3.0

---

## 快速理解：Extensions 是什么？

### A2A Extensions 机制

A2A 协议通过 **Extensions** 机制扩展 AgentCard 的能力和信息，支持 4 种扩展类型：

| 扩展类型 | 用途 | 是否改变协议 |
|---------|------|------------|
| **Data-only Extensions** | 添加结构化信息到 AgentCard | ❌ 否 |
| **Method Extensions** | 添加新的 RPC 方法 | ✅ 是 |
| **Profile Extensions** | 定义附加状态和约束 | ✅ 是 |
| **State Machine Extensions** | 添加新的状态转换 | ✅ 是 |

**你最常用的类型**：**Data-only Extensions** ⭐

---

## Data-only Extensions 详解

### 定义

> "Expose new, structured information in the Agent Card that doesn't impact the request-response flow"

**用途**：在 AgentCard 中携带**业务数据**，不改变通信方式。

### 典型场景

**场景 1：物理资产 Agent**
```json
{
  "name": "HPLC-001",
  "capabilities": {
    "streaming": true,
    "extensions": [
      {
        "uri": "https://lab.com/extensions/physical-asset/v1",
        "description": "物理资产信息",
        "required": false,
        "params": {
          "physicalAssetId": "HPLC-001",
          "geoLocation": {
            "lat": 39.9042,
            "lon": 116.4074
          },
          "status": "OPERATIONAL",
          "locationId": "BuildingA-Lab1-Rack2",
          "calibrationDate": "2025-01-15"
        }
      }
    ]
  }
}
```

**场景 2：GDPR 合规性**（官方示例）
```json
{
  "extensions": [
    {
      "uri": "https://example.com/extensions/gdpr-compliance/v1",
      "params": {
        "dataRetentionDays": 90,
        "allowsDataExport": true,
        "consentRequired": true
      }
    }
  ]
}
```

**场景 3：未来扩展类型**
```json
{
  "extensions": [
    {
      "uri": "https://finance.com/extensions/trading-bot/v1",
      "params": {
        "tradingAccountId": "ACC-12345",
        "riskLevel": "medium",
        "maxTradeAmount": 10000
      }
    }
  ]
}
```

---

## Admin 界面字段说明

### AgentCard 编辑页面结构

```
┌─ 标识
│  └─ namespace, name, version, ...
│
├─ L1 基本信息
│  └─ protocolVersion, description, url, ...
│
├─ AgentCapabilities（协议能力）
│  ├─ capability_streaming ✅ checkbox
│  ├─ capability_push_notifications ✅ checkbox
│  └─ capability_state_transition_history ✅ checkbox
│
├─ 输入输出模式和技能
│  ├─ default_input_modes (JSON 数组)
│  ├─ default_output_modes (JSON 数组)
│  └─ skills (JSON 数组)
│
├─ Agent 扩展（内联表格）★ 重点
│  └─ AgentCapabilities.extensions[] 的管理
│
└─ 高级选项
   └─ provider, security, ...
```

---

### Agent 扩展（AgentCapabilities.extensions）字段

| 字段 | A2A 字段 | 必填 | 说明 |
|------|---------|------|------|
| **URI** | `uri` | ✅ 是 | 扩展的唯一标识，使用持久化 URI |
| **Params** | `params` | ⚪ 否 | JSON 对象：扩展特定数据 |
| **Description** | `description` | ⚪ 否 | 扩展说明 |
| **Required** | `required` | ⚪ 否 | 客户端是否必须支持（通常 false） |
| **Schema** | - | ⚪ 否 | [内部字段] 关联 Schema 用于验证 |
| **Order** | - | ⚪ 否 | [内部字段] 排序顺序 |

---

## 使用流程

### 添加 Data-only Extension（物理资产示例）

**步骤 1：准备 Schema（可选但推荐）**

访问 `/admin/documents/schemaregistry/add/`

```
Schema URI: https://lab.com/extensions/physical-asset/v1
Schema Type: physical-asset
Version: v1
Description: 物理资产信息扩展
```

添加字段（通过 SchemaField inline）：
- `physicalAssetId` (string, 必填)
- `geoLocation` (object, 可选)
- `status` (enum, 必填, ['OPERATIONAL', 'MAINTENANCE', 'OFFLINE'])
- `locationId` (string, 必填)
- `calibrationDate` (date, 可选)

**步骤 2：创建 AgentCard**

访问 `/admin/documents/agentcard/add/`

填写基本信息：
```
Namespace: test-ns
Name: HPLC-001
Version: 1.0.0
```

**步骤 3：添加 Extension**

在 "Agent 扩展" 区域，点击"添加另一个 Agent扩展"

```
URI: https://lab.com/extensions/physical-asset/v1
Schema: physical-asset v1 (从下拉菜单选择)
Params: {
  "physicalAssetId": "HPLC-001",
  "geoLocation": {
    "lat": 39.9042,
    "lon": 116.4074
  },
  "status": "OPERATIONAL",
  "locationId": "BuildingA-Lab1-Rack2",
  "calibrationDate": "2025-01-15"
}
Description: (自动从 schema 填充)
Required: ☐ (不勾选)
Order: 0
```

**步骤 4：保存**

点击"保存"，系统会：
1. 验证 params 数据格式（如果关联了 schema）
2. 生成符合 A2A 标准的 JSON

---

## 常见问题

### Q1: 为什么还要选择 Schema？

**A**: Schema 是**可选的**，仅 Data-only Extensions 推荐使用。

**Schema 的作用**：
1. **自动验证** params 数据格式
2. **自动填充** description
3. **提供文档**：字段定义和约束

**使用建议**：
- ✅ Data-only Extensions：推荐关联 schema（验证业务数据）
- ⚪ Method Extensions：通常不需要 schema
- ⚪ Profile Extensions：通常不需要 schema

---

### Q2: Order 字段是什么？

**A**: Order 不是 A2A 协议字段，是内部排序用的。

**作用**：控制 extensions 数组在 JSON 输出中的顺序
- 数字越小越靠前（0 → 1 → 2 → ...）
- 默认值为 0

**是否必填**：❌ 可以忽略，默认按 URI 字母顺序

---

### Q3: URI 如何命名？

**A**: 推荐使用组织域名 + 扩展类型 + 版本号

**命名规则**：
```
https://{your-domain}/extensions/{extension-name}/{version}
```

**示例**：
```
✅ https://lab.com/extensions/physical-asset/v1
✅ https://finance.com/extensions/trading-bot/v2
✅ https://a2a.org/extensions/task-history/v1

❌ http://lab.com/... (不要用 HTTP)
❌ /physical-asset (缺少域名)
❌ https://lab.com/schemas/... (不要用 schemas，用 extensions)
```

**最佳实践**（A2A 官方建议）：
- 使用持久化 URI（如 `w3id.org`）避免链接失效
- 包含版本号
- 在 URI 提供规范文档

---

### Q4: 如何区分不同扩展类型？

**A**: 无需严格区分，但可以通过 URI 前缀约定

**约定**（非强制）：
```
Data-only:  https://your-org.com/extensions/data-{name}/v1
Method:     https://your-org.com/extensions/method-{name}/v1
Profile:    https://your-org.com/extensions/profile-{name}/v1
```

**实际上**：通过 params 内容就能判断类型
- Data-only：params 包含业务数据
- Method：params 包含方法配置

---

### Q5: params 可以是任意 JSON 吗？

**A**: 可以，但有约束

**A2A 协议约束**：
- ✅ 可以添加任意结构化数据
- ❌ 不能修改核心数据结构定义
- ❌ 不能添加新的枚举值（用 metadata 代替）

**如果关联了 Schema**：
- ✅ 会自动验证 params 数据格式
- ❌ 不符合 schema 的数据会被拒绝

---

### Q6: Required 何时设为 true？

**A**: 仅在客户端**必须理解**此扩展才能正常工作时设为 true。

**示例**：
```
required: false  ← 通常情况（客户端可忽略）
required: true   ← 关键扩展（客户端必须支持）
```

**A2A 官方建议**：
> Restrict `required: true` status to fundamental extensions only

仅在扩展是核心功能时设为 true，否则客户端可能无法连接。

---

## 完整示例

### 物理资产 Agent（完整配置）

```json
{
  "protocolVersion": "0.3.0",
  "name": "HPLC-001",
  "version": "1.0.0",
  "description": "高效液相色谱仪 HPLC-001",
  "url": "https://lab.example.com/agents/hplc-001",
  "preferredTransport": "http",

  "capabilities": {
    "streaming": true,
    "extensions": [
      {
        "uri": "https://lab.com/extensions/physical-asset/v1",
        "description": "物理资产信息",
        "required": false,
        "params": {
          "physicalAssetId": "HPLC-001",
          "geoLocation": {
            "lat": 39.9042,
            "lon": 116.4074,
            "address": "北京市海淀区"
          },
          "status": "OPERATIONAL",
          "locationId": "BuildingA-Lab1-Rack2",
          "calibrationDate": "2025-01-15",
          "maintenanceSchedule": "quarterly"
        }
      },
      {
        "uri": "https://lab.com/extensions/instrument-hplc/v1",
        "description": "HPLC 仪器特定参数",
        "required": false,
        "params": {
          "columnType": "C18",
          "flowRate": 1.0,
          "maxPressure": 400,
          "detectorType": "UV"
        }
      }
    ]
  },

  "defaultInputModes": ["text/plain", "application/json"],
  "defaultOutputModes": ["application/json"],

  "skills": [
    {
      "name": "Sample Analysis",
      "description": "高效液相色谱分析"
    }
  ]
}
```

---

## 验证 JSON 输出

保存 AgentCard 后，在 "元数据" 区域展开 "AgentCard JSON 预览" 查看生成的 JSON：

**检查项**：
- ✅ `capabilities.extensions` 数组存在
- ✅ 每个 extension 包含 `uri` 和 `params`
- ✅ params 数据格式正确（如果关联了 schema）
- ✅ 符合 A2A 协议 5.5.2 规范

---

## 参考资料

- [A2A 协议规范](https://a2a-protocol.org/latest/specification/)
- [A2A Extensions 指南](https://a2a-protocol.org/latest/topics/extensions/)
- [AgentCapabilities 对象定义](https://a2a-protocol.org/latest/specification/#552-agentcapabilities-object)

---

## 总结

**核心理解**：
1. ✅ Extensions 是 A2A 标准的扩展机制
2. ✅ Data-only Extensions 用于携带业务数据（你的主要需求）
3. ✅ Schema 是可选的，用于验证 params 数据
4. ✅ Order 是内部排序字段，非协议要求
5. ✅ 所有扩展类型共用同一个 `capabilities.extensions` 数组

**设计优势**：
- 灵活扩展：无需修改代码，通过 URI 添加新类型
- 标准兼容：100% 符合 A2A 协议
- 数据验证：通过 Schema 保证数据质量

**开始使用**：
访问 http://localhost:8000/admin/documents/agentcard/ 🚀
