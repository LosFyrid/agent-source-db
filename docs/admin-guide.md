# AgentCard 管理系统使用指南

## 快速开始

### 1. 创建管理员账号（首次使用）

```bash
docker-compose exec web python manage.py createsuperuser
```

按提示输入用户名、邮箱和密码。

### 2. 访问管理后台

启动服务后访问：`http://localhost:8000/admin`

使用刚创建的管理员账号登录。

---

## 使用流程

### 第一步：创建命名空间 (Namespace)

1. 进入管理后台，点击 **"命名空间"**
2. 点击右上角 **"新增命名空间"**
3. 填写信息：
   - **ID**: `dev` （建议使用：dev, test, prod, lab-instruments 等）
   - **名称**: `开发环境`
   - **描述**: `用于开发测试的 AgentCard`
   - **是否启用**: 勾选
4. 保存

**建议的命名空间**：
- `dev` - 开发环境
- `test` - 测试环境
- `prod` - 生产环境
- `lab-instruments` - 实验室器械（领域专用）

---

### 第二步：定义 Schema（可选，但推荐）

如果你需要使用 L2 扩展字段（如物理资产ID、位置信息等），需要先定义 Schema。

#### 示例：创建 "物理资产" Schema

1. 进入 **"Schema定义"**，点击 **"新增 Schema定义"**

2. 填写基本信息：
   - **Schema URI**: `https://my-org.com/schemas/physicalAsset/v1`
   - **Schema 类型**: `physicalAsset`
   - **版本**: `v1`
   - **描述**: `物理资产基础信息（资产ID、位置、状态等）`
   - **是否启用**: 勾选

3. **保存**（先保存才能添加字段）

4. 在同一页面下方，**添加字段**（内联编辑区域）：

   | 顺序 | 字段名 | 类型 | 必填 | 说明 | 约束 |
   |------|--------|------|------|------|------|
   | 1 | `physicalAssetId` | 文本 | ✓ | 物理资产编号 | 最小长度: 3, 最大长度: 64 |
   | 2 | `locationId` | 文本 | ✓ | 所在位置ID | - |
   | 3 | `status` | 枚举 | ✓ | 运行状态 | enum_choices: `["OPERATIONAL", "MAINTENANCE", "OFFLINE"]` |
   | 4 | `lastMaintenanceDate` | 日期时间 | ✗ | 最后维护时间 | - |

5. 保存后，可以在 **"预览"** 部分查看：
   - 自动生成的 JSON Schema
   - 字段列表（表格形式）

#### 查看生成的 JSON Schema

保存后展开 **"预览"** 区域，可以看到自动生成的 JSON Schema：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "physicalAsset v1",
  "description": "物理资产基础信息（资产ID、位置、状态等）",
  "properties": {
    "physicalAssetId": {
      "type": "string",
      "description": "物理资产编号",
      "minLength": 3,
      "maxLength": 64
    },
    "locationId": {
      "type": "string",
      "description": "所在位置ID"
    },
    "status": {
      "enum": ["OPERATIONAL", "MAINTENANCE", "OFFLINE"],
      "type": "string",
      "description": "运行状态"
    },
    "lastMaintenanceDate": {
      "type": "string",
      "format": "datetime",
      "description": "最后维护时间"
    }
  },
  "required": ["physicalAssetId", "locationId", "status"]
}
```

---

### 第三步：创建 AgentCard

1. 进入 **"AgentCards"**，点击 **"新增 AgentCard"**

2. 填写 **L1 标准字段**（A2A 协议要求）：

   **标识部分**：
   - **命名空间**: 选择 `dev`
   - **名称**: `HPLC-001`
   - **版本**: `1.0.0`
   - **是否默认版本**: 勾选
   - **是否激活**: 勾选

   **L1 基本信息**：
   - **协议版本**: `0.3.0`（默认）
   - **描述**: `Agilent 1260 高效液相色谱仪，位于A栋实验室`
   - **URL**: `https://lab.my-org.com/instruments/hplc-001`
   - **首选传输协议**: 选择 `HTTP/REST`

   **L1 能力配置**（JSON 格式）：
   ```json
   // capabilities
   {
     "streaming": false,
     "tools": true
   }

   // default_input_modes
   ["application/json", "text/plain"]

   // default_output_modes
   ["application/json"]

   // skills
   [
     {
       "name": "runAnalysis",
       "description": "运行液相色谱分析",
       "inputModes": ["application/json"],
       "outputModes": ["application/json"]
     }
   ]
   ```

3. 填写 **L2 领域扩展**（使用刚才定义的 Schema）：

   在 **"L2 领域扩展"** 的 `domain_extensions` 字段中输入：

   ```json
   {
     "https://my-org.com/schemas/physicalAsset/v1": {
       "physicalAssetId": "HPLC-001",
       "locationId": "BuildingA-Lab1-Rack2",
       "status": "OPERATIONAL",
       "lastMaintenanceDate": "2025-10-20T10:00:00Z"
     }
   }
   ```

4. **保存**

5. 保存后，展开 **"L2 领域扩展"** 部分，可以看到：
   - **L2 扩展预览**：显示 Schema 类型、版本和数据
   - 如果 Schema 已注册，会显示 `physicalAsset v1`
   - 如果未注册，会显示 `未注册的 Schema`（红色警告）

6. 展开 **"元数据"** 部分，可以看到：
   - **AgentCard JSON 预览**：完整的符合 A2A 协议的 JSON（可直接复制用于 API）

---

## 使用技巧

### Schema 管理

#### 查看 Schema 的使用情况

在 **"Schema定义"** 列表页，**"使用情况"** 列会显示有多少个 AgentCard 使用了该 Schema。

#### 复用 Schema

多个 AgentCard 可以使用同一个 Schema。例如：
- `HPLC-001`、`HPLC-002`、`LC-MS-003` 都可以使用 `physicalAsset/v1`

#### 组合多个 Schema

一个 AgentCard 可以同时使用多个 Schema：

```json
{
  "https://my-org.com/schemas/physicalAsset/v1": {
    "physicalAssetId": "HPLC-001",
    "locationId": "Lab-A",
    "status": "OPERATIONAL"
  },
  "https://my-org.com/schemas/instrument/hplc/v1": {
    "instrumentModel": "Agilent 1260",
    "columnType": "C18",
    "flowRate": 1.0
  }
}
```

### 版本管理

#### 为同一个 Agent 创建多个版本

可以为同一个 Agent（相同 namespace + name）创建多个版本：

- `dev::HPLC-001@1.0.0` （默认版本）
- `dev::HPLC-001@1.1.0`
- `dev::HPLC-001@2.0.0-beta`

**注意**：每个 namespace::name 只能有一个默认版本。

#### 升级 Schema 版本

当需要修改 Schema 定义时：

1. **不要修改现有版本**（如 `v1`）- 保持不变性
2. 创建新版本：
   - 复制 `physicalAsset v1`
   - 修改 URI 为 `https://my-org.com/schemas/physicalAsset/v2`
   - 修改版本为 `v2`
   - 添加/修改字段
3. 新的 AgentCard 使用 `v2`，旧的 AgentCard 继续使用 `v1`

### 数据验证

系统会自动验证 L2 扩展数据：

#### 必填字段检查
如果缺少必填字段，保存时会报错：
```
缺少必填字段：physicalAssetId
```

#### 类型检查
如果类型不匹配，会报错：
```
字段 'status': 类型错误，期望 文本
```

#### 枚举值检查
如果枚举值不在允许范围内：
```
字段 'status': 值必须是以下之一：OPERATIONAL, MAINTENANCE, OFFLINE
```

---

## Schema 发现机制

### 方式 1：通过 Django Admin 浏览

1. 进入 **"Schema定义"** 列表页
2. 可以看到所有已定义的 Schema
3. 点击某个 Schema，查看详细的字段定义

### 方式 2：通过 API 查询（TODO）

未来可以提供 REST API：

```
GET /api/schemas/catalog/
```

返回：
```json
{
  "catalog": {
    "physicalAsset": [
      {
        "uri": "https://my-org.com/schemas/physicalAsset/v1",
        "version": "v1",
        "description": "物理资产基础信息",
        "fields": [...]
      }
    ],
    "instrument": [...]
  }
}
```

---

## 常见问题

### Q: 必须先定义 Schema 才能使用 L2 扩展吗？

**A**: 不是必须的。当前配置为 **宽松模式**：
- 可以使用未注册的 Schema URI
- 但**强烈建议**先注册 Schema，这样可以：
  - 自动验证数据
  - 生成文档
  - 团队成员可以发现和复用

### Q: Schema URI 必须是真实可访问的网址吗？

**A**: 不需要。Schema URI 是一个**标识符**，不是必须可访问的 URL。
- 使用你的组织域名（如 `my-org.com`）来保证唯一性
- 建议使用有意义的路径（如 `/schemas/physicalAsset/v1`）

### Q: 如何修改已有的 Schema？

**A**: **不建议修改**已发布的 Schema（保持版本不变性）。
- 如果只是修改描述文字，可以直接修改
- 如果要修改字段定义，应该创建新版本（如 `v2`）

### Q: 可以不使用 L2 扩展吗？

**A**: 可以。L2 扩展（`domain_extensions`）是可选的：
- 只使用 L1 标准字段，完全符合 A2A 协议
- L2 扩展用于存储领域特定的数据（如物理资产ID、位置等）

---

## 下一步

1. **创建 REST API**：提供 `/api/agentcards/` 接口
2. **批量导入**：从 Nacos 或其他注册中心批量导入
3. **Schema 市场**：团队内共享常用 Schema 模板
4. **数据验证增强**：更复杂的约束规则

---

## 附录：字段类型说明

| 类型 | 说明 | 可用约束 | 示例 |
|------|------|----------|------|
| **文本 (string)** | 字符串 | min_length, max_length, pattern | `"HPLC-001"` |
| **整数 (integer)** | 整数 | min_value, max_value | `42` |
| **数字 (number)** | 浮点数 | min_value, max_value | `3.14` |
| **布尔值 (boolean)** | 真/假 | - | `true` |
| **数组 (array)** | 数组 | - | `["a", "b"]` |
| **对象 (object)** | 对象 | - | `{"key": "value"}` |
| **日期时间 (datetime)** | ISO 8601 格式 | - | `"2025-10-20T10:00:00Z"` |
| **日期 (date)** | 日期 | - | `"2025-10-20"` |
| **枚举 (enum)** | 单选 | enum_choices | `"OPERATIONAL"` |

---

**提示**：本指南基于简化的 Schema 治理模式，适合小团队快速迭代。
