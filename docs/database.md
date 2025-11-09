# 设计文档：AgentCard L1/L2 扩展字段模型

## 1. 目标

本文档旨在为标准 `AgentCard`  (L1 - Level 1) 协议设计一个健壮的、可扩展的**自定义字段模型 (L2 - Level 2)**。

注意：关于AgentCard：
 - (原始协议)[https://a2a-protocol.org/latest/specification/#55-agentcard-object-structure]
 - (实现版本)[https://nacos.io/docs/latest/manual/user/ai/agent-registry/?spm=5238cd80.7976cd82.0.0.79926171nZhPNj]
 - (注册方案1-HTTP API)[https://nacos.io/docs/latest/manual/admin/admin-api/?spm=5238cd80.7976cd82.0.0.79926171nZhPNj#5-a2a%E6%B3%A8%E5%86%8C%E4%B8%AD%E5%BF%83]
 - (注册方案2-gRPC SDK)[https://nacos.io/docs/latest/manual/user/java-sdk/usage/?spm=5238cd80.7976cd82.0.0.79926171nZhPNj#7-a2a-%E6%B3%A8%E5%86%8C%E4%B8%AD%E5%BF%83]


核心目标是允许团队为特定领域（如“实验室器械数字孪生”）添加自定义元数据（如 `locationId`, `physicalAssetId`），同时必须满足以下要求：

1.  **兼容性 (Compatibility):** 决不能破坏与标准 L1 `AgentCard` 解析器的兼容性。一个不理解我们 L2 字段的“标准”Agent 客户端必须能够安全地忽略它们并继续工作。
2.  **可扩展性 (Extensibility):** 该模型必须能够支持未来**任何类型**的 Agent（如“LLM Agent”、“计算 Agent”），而无需修改基础 `AgentCard` 结构。
3.  **鲁棒性 (Robustness):** 必须避免“命名空间污染”。不同领域（如“物理资产”和“财务合规”）的 L2 字段如果同名（例如 `status`），不得发生冲突。

## 2. 核心设计：命名空间扩展 (Namespaced Extensions)

我们**拒绝**了将 L2 字段“扁平化”到 `AgentCard` 顶层的设计（例如：直接在 `AgentCard` 上添加 `locationId`）。这种设计会导致严重的命名冲突和可维护性问题。

我们采用的方案是**“命名空间扩展”**模型。

我们在 `AgentCard` 基础结构上**只添加一个**新的 L2 字段，名为：`domainExtensions`。

* **类型：** `Map<String, Object>` (在 JSON 中表现为一个对象)
* **Key (键):** 一个**Schema URI**（字符串）。这是一个全球唯一的名称，用于声明“这是一份什么样的数据”。
* **Value (值):** 一个**JSON 对象**。这个对象包含了该 Schema URI 所定义的所有 L2 字段。

---

## 3. 详细设计

### 3.1. `domainExtensions` 字段

`domainExtensions` 是所有 L2 数据的唯一入口。

**JSON 结构示例：**

```json
{
  "protocolVersion": "0.3.0",
  "name": "HPLC-001 (Loc1)",
  "url": "...",
  "skills": [ ... ],
  
  "domainExtensions": {
    
    "[https://my-org.com/schemas/physicalAsset/v1](https://my-org.com/schemas/physicalAsset/v1)": {
      "physicalAssetId": "HPLC-001",
      "locationId": "Loc1-RackB",
      "status": "OPERATIONAL"
    },
    
    "[https://my-org.com/schemas/instrument/hplc/v1.2](https://my-org.com/schemas/instrument/hplc/v1.2)": {
      "instrumentModel": "Agilent 1260",
      "lastCalibrationDate": "2025-10-20T10:00:00Z"
    }
  }
}

### 3.2. Schema URI (L2 命名空间)

Schema URI 是本设计的核心。它是一个**标识符**，而不是一个（必须可访问的）地址。

1.  **唯一性：** 它使用**域名**（例如 `my-org.com`）来保证其全球唯一性，避免与其他组织创建的 L2 Schema 冲突。
2.  **一致性：** 它通过嵌入**版本号**（例如 `/v1`, `/v1.2`）来确保数据结构的一致性。`v1` 一旦发布，其结构**永远不变**。任何修改都必须发布为 `v2`。
3.  **（最佳实践）可访问性：** 尽管不是强制要求，但最佳实践是让这个 URI **可以被访问** (HTTP GET)，并返回一个 **JSON Schema** 文件。这个文件定义了其 Value 对象的合法数据结构（例如，`locationId` 是一个必填的字符串），这使得自动化验证成为可能。

### 3.3. 设计优势分析

  * **解决了“命名冲突” (鲁棒性):**
    一个“物理资产”的状态和“财务 Bot”的状态可以安全共存，因为它们位于不同的命名空间下：

      * `domainExtensions -> "https/../physicalAsset/v1" -> "status": "OPERATIONAL"`
      * `domainExtensions -> "https/../financeBot/v1" -> "status": "APPROVED"`

  * **解决了“无限扩展” (可扩展性):**

      * **新领域：** 当需要“物流 Agent”时，只需定义一个新的 Schema URI (`https/../logisticsBot/v1`) 并开始使用，**无需**修改任何现有代码或数据。
      * **组合 (Composition):** 如上例所示，一个 Agent 可以同时实现**多个** L2 Profile。我们的 `HPLC-001` *既是*一个 `physicalAsset`，*也是*一个 `hplc`。
