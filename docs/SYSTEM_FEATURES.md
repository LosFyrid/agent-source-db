# AgentCard 管理系统 - 功能说明

**系统版本**: 1.0
**Django 版本**: 5.2.8
**A2A 协议版本**: 0.3.0
**最后更新**: 2025-11-09

---

## 系统概述

这是一个**结构化文档管理系统**，专门用于管理符合 A2A 协议的 AgentCard。系统提供：

1. **内部 Admin 后端** - 用于众包式、结构化文档录入和管理
2. **高性能 API 层** - 对外暴露文档给生产服务使用

---

## 核心功能

### 1. 📝 Django Admin 管理界面

**访问地址**: http://localhost:8000/admin/

**功能**:
- ✅ 可视化数据录入和编辑
- ✅ AgentCard 创建和管理
- ✅ Schema 定义管理
- ✅ Namespace 管理
- ✅ AgentExtension 内联编辑（支持 A2A Extensions）
- ✅ 实时数据验证和错误提示
- ✅ JSON 预览功能（查看生成的 AgentCard JSON）
- ✅ 渐进式数据录入（支持保存草稿）

**用户权限**:
- Superuser：所有权限
- Staff：可访问 Admin，需要配置模型级别权限
- 普通用户：无法访问 Admin

---

### 2. 🔌 REST API

**基础 URL**: http://localhost:8000/api/

#### 2.1 Namespace API

**用途**: 管理命名空间（多环境资源隔离）

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/namespaces/ | 列出所有命名空间 |
| GET | /api/namespaces/{id}/ | 获取单个命名空间详情 |
| POST | /api/namespaces/ | 创建新命名空间 |
| PUT | /api/namespaces/{id}/ | 完整更新命名空间 |
| PATCH | /api/namespaces/{id}/ | 部分更新命名空间 |
| DELETE | /api/namespaces/{id}/ | 删除命名空间 |

**示例**:
```bash
# 列出所有命名空间
curl http://localhost:8000/api/namespaces/

# 获取特定命名空间
curl http://localhost:8000/api/namespaces/prod/
```

---

#### 2.2 Schema Registry API

**用途**: 管理扩展数据的 Schema 定义

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/schemas/ | 列出所有 Schema |
| GET | /api/schemas/{id}/ | 获取单个 Schema 详情 |
| POST | /api/schemas/ | 创建新 Schema |
| PUT | /api/schemas/{id}/ | 完整更新 Schema |
| PATCH | /api/schemas/{id}/ | 部分更新 Schema |
| DELETE | /api/schemas/{id}/ | 删除 Schema |
| GET | /api/schemas/catalog/ | **Schema 目录**（发现机制） |

**Schema 目录示例**:
```bash
curl http://localhost:8000/api/schemas/catalog/
```

返回格式：
```json
{
  "catalog": {
    "physicalAsset": [
      {
        "uri": "https://...",
        "version": "v1",
        "description": "...",
        "fields": [...],
        "usage_count": 5
      }
    ]
  },
  "categories": ["physicalAsset", "instrument"],
  "total_schemas": 2
}
```

---

#### 2.3 AgentCard API

**用途**: 管理 AgentCard（A2A 协议）

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/agentcards/ | 列出所有 AgentCard |
| GET | /api/agentcards/{id}/ | 获取单个 AgentCard 详情 |
| POST | /api/agentcards/ | 创建新 AgentCard |
| PUT | /api/agentcards/{id}/ | 完整更新 AgentCard |
| PATCH | /api/agentcards/{id}/ | 部分更新 AgentCard |
| DELETE | /api/agentcards/{id}/ | 删除 AgentCard |
| GET | /api/agentcards/{id}/standard_json/ | **A2A 协议标准格式** |
| GET | /api/agentcards/by-namespace/{ns_id}/ | 按命名空间查询 |

**查询参数**:
- `?namespace=dev` - 按命名空间过滤
- `?name=HPLC` - 按名称搜索（模糊匹配）
- `?is_default_version=true` - 只返回默认版本
- `?is_active=true` - 只返回激活的

**示例**:
```bash
# 获取所有 AgentCard
curl http://localhost:8000/api/agentcards/

# 按命名空间过滤
curl http://localhost:8000/api/agentcards/?namespace=prod&is_active=true

# 获取 A2A 协议标准格式
curl http://localhost:8000/api/agentcards/12/standard_json/

# 获取 A2A 格式（包含内部元数据）
curl http://localhost:8000/api/agentcards/12/standard_json/?include_metadata=true

# 按命名空间查询
curl http://localhost:8000/api/agentcards/by-namespace/prod/
```

**响应示例**（standard_json）:
```json
{
  "protocolVersion": "0.3.0",
  "name": "HPLC-001",
  "description": "Agilent 1260 高效液相色谱仪",
  "url": "https://lab.example.com/instruments/hplc-001",
  "preferredTransport": "HTTP+JSON",
  "version": "1.0.0",
  "defaultInputModes": ["application/json", "text/plain"],
  "defaultOutputModes": ["application/json"],
  "skills": [
    {
      "id": "runanalysis",
      "name": "runAnalysis",
      "description": "运行液相色谱分析",
      "tags": [],
      "inputModes": ["application/json"],
      "outputModes": ["application/json"]
    }
  ],
  "capabilities": {
    "extensions": [...]
  }
}
```

---

### 3. 🔍 数据验证

系统采用**两层验证策略**：

#### 3.1 数据库层验证（保存时）

**策略**: 宽松验证，支持渐进式录入

**验证内容**:
- ✅ 字段格式（MIME 类型必须包含 `/`、URL 必须 HTTPS 等）
- ✅ 数据结构（AgentSkill、AgentProvider、SecurityScheme 等）
- ⚪ **允许空数组**（defaultInputModes、defaultOutputModes、skills）

**用途**: 允许用户分步骤填写 AgentCard，随时保存草稿

#### 3.2 输出层验证（导出时）

**策略**: 严格验证 A2A 协议

**验证内容**:
- ✅ 所有 A2A 必填字段不能为空
- ✅ 数组字段不能为空数组
- ✅ 100% 符合 A2A 协议 0.3.0 规范

**用途**: 确保通过 API 对外输出的数据完全符合 A2A 协议

---

### 4. 📤 数据导出

系统提供两种导出方法：

#### 4.1 to_agentcard_json() - A2A 协议标准格式

**用途**: API 对外输出，生产环境

**特点**:
- ✅ 严格验证 A2A 协议必填字段
- ✅ 不允许导出不完整的数据
- ✅ 抛出 ValidationError（如果数据不完整）
- ✅ 100% 符合 A2A 协议规范

**使用**:
```python
from documents.models import AgentCard

card = AgentCard.objects.get(id=1)

# 导出标准格式
json_data = card.to_agentcard_json()

# 导出包含元数据
json_data = card.to_agentcard_json(include_metadata=True)
```

**API 端点**:
```bash
GET /api/agentcards/{id}/standard_json/
GET /api/agentcards/{id}/standard_json/?include_metadata=true
```

---

#### 4.2 to_dict_raw() - 原始数据导出

**用途**: 草稿导出、备份、调试

**特点**:
- ✅ 不验证 A2A 协议
- ✅ 允许导出不完整的数据
- ✅ 不会抛出 ValidationError
- ✅ 数据库有什么就导出什么

**使用**:
```python
from documents.models import AgentCard

card = AgentCard.objects.get(id=1)

# 导出原始数据
raw_data = card.to_dict_raw()

# 导出包含元数据
raw_data = card.to_dict_raw(include_metadata=True)
```

**适用场景**:
- 导出草稿数据（AgentCard 未完成）
- 数据备份和迁移
- 调试和检查数据库内容
- 内部工具和脚本

---

### 5. 🏷️ 命名空间（Namespace）

**用途**: 多环境资源隔离

**典型使用**:
- `dev` - 开发环境
- `test` - 测试环境
- `staging` - 预发布环境
- `prod` - 生产环境

**优势**:
- ✅ 同一个 AgentCard 可以在不同环境有不同版本
- ✅ 版本管理（每个 namespace::name 可以有多个版本，标记默认版本）
- ✅ 环境隔离（不同环境的数据互不干扰）

**示例**:
```
dev::HPLC-001@1.0.0
dev::HPLC-001@2.0.0  (默认版本)
prod::HPLC-001@1.0.0 (默认版本)
```

---

### 6. 📋 Schema Registry

**用途**: 定义和验证 AgentExtension 的 params 数据结构

**功能**:
- ✅ 自定义 Schema 定义（字段名、类型、约束）
- ✅ JSON Schema 自动生成
- ✅ 数据验证（validate_extension_data）
- ✅ Schema 目录（/api/schemas/catalog/）
- ✅ 使用统计（哪些 AgentCard 使用了此 Schema）

**Schema 字段支持的类型**:
- `string` - 字符串
- `integer` - 整数
- `number` - 数字（浮点数）
- `boolean` - 布尔值
- `object` - 对象
- `array` - 数组
- `enum` - 枚举

**约束条件**:
- 字符串：min_length, max_length, pattern
- 数字：min_value, max_value
- 枚举：enum_choices

**示例**:
```python
from documents.models import SchemaRegistry

# 获取 Schema
schema = SchemaRegistry.objects.get(schema_type='physicalAsset')

# 生成 JSON Schema
json_schema = schema.generate_json_schema()

# 验证数据
is_valid, error_msg = schema.validate_extension_data({
    "assetId": "HPLC-001",
    "location": "Lab A",
    "status": "OPERATIONAL"
})
```

---

### 7. ✅ A2A 协议合规

系统 100% 符合 A2A 协议 0.3.0 规范。

#### 支持的 AgentCard 字段

**必填字段**:
- `protocolVersion` - 协议版本（默认 "0.3.0"）
- `name` - Agent 名称
- `description` - 描述
- `url` - Agent URL（必须 HTTPS）
- `preferredTransport` - 传输协议（JSONRPC/GRPC/HTTP+JSON）
- `version` - Agent 版本
- `capabilities` - Agent 能力（可以是空对象 `{}`）
- `defaultInputModes` - 默认输入 MIME 类型（非空数组）
- `defaultOutputModes` - 默认输出 MIME 类型（非空数组）
- `skills` - Agent 技能列表（非空数组）

**可选字段**:
- `provider` - 提供者信息
- `iconUrl` - 图标 URL
- `documentationUrl` - 文档 URL
- `additionalInterfaces` - 额外接口
- `securitySchemes` - 安全方案
- `security` - 安全要求
- `supportsAuthenticatedExtendedCard` - 是否支持认证扩展卡
- `signatures` - 签名

#### AgentCapabilities 支持

**布尔能力**:
- `streaming` - SSE 流式响应
- `pushNotifications` - 推送通知
- `stateTransitionHistory` - 状态转换历史

**Extensions 机制**:
- ✅ Data-only Extensions - 添加结构化业务数据
- ✅ Method Extensions - 添加新的 RPC 方法
- ✅ Profile Extensions - 定义附加状态和约束
- ✅ State Machine Extensions - 定义状态机

**Extensions 字段**:
- `uri` - 扩展 URI（必填）
- `description` - 描述（可选）
- `required` - 是否必需（可选）
- `params` - 扩展参数（可选，可关联 Schema 验证）

---

## 系统架构

```
┌─────────────────────────────────────┐
│  用户界面层                          │
│  - Django Admin（数据录入）          │
│  - DRF 可浏览 API（开发调试）        │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  API 层（REST API）                 │
│  - Namespace CRUD                   │
│  - Schema CRUD + Catalog            │
│  - AgentCard CRUD + Standard JSON   │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  业务逻辑层（Models + Validation）   │
│  - 两层验证策略                      │
│  - A2A 协议合规检查                  │
│  - Schema 验证引擎                   │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  数据持久化层（PostgreSQL）          │
│  - Namespace, SchemaRegistry        │
│  - AgentCard, AgentExtension        │
└─────────────────────────────────────┘
```

---

## 典型使用场景

### 场景1: 内部数据管理

1. 内部人员通过 Django Admin 登录
2. 创建或编辑 AgentCard
3. 分步骤填写数据（可保存草稿）
4. 系统实时验证格式错误
5. 完成后保存

### 场景2: 外部系统集成

1. 外部系统通过 API 查询 AgentCard
2. 使用查询参数过滤（namespace、name 等）
3. 获取 A2A 协议标准格式（/standard_json/）
4. 直接使用符合 A2A 协议的数据

### 场景3: Schema 管理

1. 定义 Extension 的 Schema（字段、类型、约束）
2. 在 AgentExtension 中关联 Schema
3. 填写 params 时自动验证格式
4. 通过 /api/schemas/catalog/ 发现可用 Schema

### 场景4: 多环境部署

1. 为不同环境创建 Namespace（dev/test/prod）
2. 同一个 Agent 在不同环境维护不同版本
3. 通过 namespace 查询参数过滤
4. 环境之间数据隔离

---

## 权限控制

**API 权限**:
- 读取（GET）：所有人可访问（包括未登录用户）
- 写入（POST/PUT/PATCH/DELETE）：需要登录认证

**Django Admin 权限**:
- Superuser：所有权限
- Staff + 模型权限：可访问指定模型
- 普通用户：无法访问

**推荐配置**（生产环境）:
- 数据录入人员：Staff 用户 + AgentCard/Schema 的增删改查权限
- API 消费者：通过 API Token 或 Session 认证
- 公开读取：允许未认证用户 GET AgentCard

---

## 当前数据统计

运行以下命令查看当前数据：

```bash
docker-compose exec web python show_api_info.py
```

**示例输出**:
```
📊 数据库统计：
   Namespace：     3 个
   Schema：        1 个（活跃）
   AgentCard：     3 个（总计）
                   3 个（活跃）

📋 AgentCard 列表：
   dev::HPLC-001@2.0.0
   dev::HPLC-001@1.0.0
   prod::LC-MS-001@1.0.0
```

---

## 相关文档

- **TWO_LAYER_VALIDATION.md** - 两层验证策略详解
- **RAW_EXPORT_GUIDE.md** - 数据导出方法使用指南
- **ADMIN_GUIDE.md** - Admin 界面使用指南
- **A2A_VALIDATION.md** - A2A 协议验证说明

---

## 快速开始

### 1. 启动系统

```bash
docker-compose up -d
```

### 2. 访问 Admin

```
URL: http://localhost:8000/admin/
用户: 你的 superuser 账号
```

### 3. 访问 API

```bash
# 列出所有 AgentCard
curl http://localhost:8000/api/agentcards/

# 获取 A2A 标准格式
curl http://localhost:8000/api/agentcards/1/standard_json/
```

### 4. 浏览 API 文档

访问 http://localhost:8000/api/ 查看 DRF 可浏览 API 界面

---

**系统版本**: 1.0
**最后更新**: 2025-11-09
