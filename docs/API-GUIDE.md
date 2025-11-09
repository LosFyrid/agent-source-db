# AgentCard REST API 使用指南

## 🚀 快速开始

### API 根路径

**可浏览 API**：http://localhost:8000/api/
**API 根**：返回所有可用的端点列表

```bash
curl http://localhost:8000/api/
```

```json
{
  "namespaces": "http://localhost:8000/api/namespaces/",
  "schemas": "http://localhost:8000/api/schemas/",
  "agentcards": "http://localhost:8000/api/agentcards/"
}
```

---

## 📚 API 端点

### 1. Namespaces API

**基础路径**：`/api/namespaces/`

#### 列表（GET /api/namespaces/）

```bash
curl http://localhost:8000/api/namespaces/
```

**响应**：
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "dev",
      "name": "开发环境",
      "description": "用于开发测试",
      "is_active": true,
      "created_at": "2025-11-08T10:00:00Z",
      "updated_at": "2025-11-08T10:00:00Z",
      "agent_card_count": 5
    }
  ]
}
```

#### 详情（GET /api/namespaces/{id}/）

```bash
curl http://localhost:8000/api/namespaces/dev/
```

#### 创建（POST /api/namespaces/）

```bash
curl -X POST http://localhost:8000/api/namespaces/ \
  -H "Content-Type: application/json" \
  -u admin:password \
  -d '{
    "id": "prod",
    "name": "生产环境",
    "description": "生产环境的 AgentCard",
    "is_active": true
  }'
```

#### 更新（PUT /api/namespaces/{id}/）

```bash
curl -X PUT http://localhost:8000/api/namespaces/prod/ \
  -H "Content-Type: application/json" \
  -u admin:password \
  -d '{
    "id": "prod",
    "name": "生产环境（已更新）",
    "description": "生产环境的 AgentCard",
    "is_active": true
  }'
```

#### 部分更新（PATCH /api/namespaces/{id}/）

```bash
curl -X PATCH http://localhost:8000/api/namespaces/prod/ \
  -H "Content-Type: application/json" \
  -u admin:password \
  -d '{
    "description": "新的描述"
  }'
```

#### 删除（DELETE /api/namespaces/{id}/）

```bash
curl -X DELETE http://localhost:8000/api/namespaces/prod/ \
  -u admin:password
```

**注意**：如果命名空间下有 AgentCard，删除会被阻止。

---

### 2. Schemas API

**基础路径**：`/api/schemas/`

#### 列表（GET /api/schemas/）

```bash
curl http://localhost:8000/api/schemas/
```

**响应（精简版）**：
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "schema_uri": "https://my-org.com/schemas/physicalAsset/v1",
      "schema_type": "physicalAsset",
      "version": "v1",
      "description": "物理资产基础信息",
      "is_active": true,
      "field_count": 3,
      "usage_count": 5,
      "created_at": "2025-11-08T10:00:00Z",
      "updated_at": "2025-11-08T10:00:00Z"
    }
  ]
}
```

#### 详情（GET /api/schemas/{id}/）

```bash
curl http://localhost:8000/api/schemas/1/
```

**响应（完整版，包含字段定义和 JSON Schema）**：
```json
{
  "id": 1,
  "schema_uri": "https://my-org.com/schemas/physicalAsset/v1",
  "schema_type": "physicalAsset",
  "version": "v1",
  "description": "物理资产基础信息",
  "example_data": {
    "physicalAssetId": "HPLC-001",
    "locationId": "Lab-A",
    "status": "OPERATIONAL"
  },
  "is_active": true,
  "fields": [
    {
      "id": 1,
      "field_name": "physicalAssetId",
      "field_type": "string",
      "field_type_display": "文本",
      "is_required": true,
      "description": "物理资产编号",
      "default_value": null,
      "min_length": 3,
      "max_length": 64,
      "constraints": {
        "minLength": 3,
        "maxLength": 64
      }
    }
  ],
  "field_definitions": [
    {
      "name": "physicalAssetId",
      "type": "string",
      "required": true,
      "description": "物理资产编号",
      "constraints": {
        "minLength": 3,
        "maxLength": 64
      }
    }
  ],
  "json_schema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "physicalAsset v1",
    "description": "物理资产基础信息",
    "properties": {
      "physicalAssetId": {
        "type": "string",
        "description": "物理资产编号",
        "minLength": 3,
        "maxLength": 64
      }
    },
    "required": ["physicalAssetId"]
  },
  "usage_count": 5
}
```

#### Schema 目录（GET /api/schemas/catalog/）

**Schema 发现机制**：返回所有 Schema 按类型分组

```bash
curl http://localhost:8000/api/schemas/catalog/
```

**响应**：
```json
{
  "catalog": {
    "physicalAsset": [
      {
        "uri": "https://my-org.com/schemas/physicalAsset/v1",
        "version": "v1",
        "description": "物理资产基础信息",
        "fields": [
          {
            "name": "physicalAssetId",
            "type": "string",
            "required": true,
            "description": "物理资产编号"
          }
        ],
        "usage_count": 5,
        "example_data": {...}
      }
    ],
    "instrument": [...]
  },
  "categories": ["physicalAsset", "instrument"],
  "total_schemas": 2
}
```

---

### 3. AgentCards API

**基础路径**：`/api/agentcards/`

#### 列表（GET /api/agentcards/）

```bash
curl http://localhost:8000/api/agentcards/
```

**查询参数**：
- `namespace`: 按命名空间过滤（如 `?namespace=dev`）
- `name`: 按名称搜索（模糊匹配，如 `?name=HPLC`）
- `is_default_version=true`: 只返回默认版本
- `is_active=true`: 只返回激活的

**示例**：
```bash
# 查询 dev 命名空间下的所有 AgentCard
curl "http://localhost:8000/api/agentcards/?namespace=dev"

# 查询名称包含 "HPLC" 的 AgentCard
curl "http://localhost:8000/api/agentcards/?name=HPLC"

# 只查询默认版本
curl "http://localhost:8000/api/agentcards/?is_default_version=true"

# 组合查询
curl "http://localhost:8000/api/agentcards/?namespace=dev&is_default_version=true"
```

**响应（精简版）**：
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "namespace_id": "dev",
      "namespace_name": "开发环境",
      "name": "HPLC-001",
      "version": "1.0.0",
      "is_default_version": true,
      "is_active": true,
      "protocol_version": "0.3.0",
      "description": "Agilent 1260 高效液相色谱仪",
      "url": "https://lab.my-org.com/hplc-001",
      "preferred_transport": "http",
      "extension_count": 1,
      "created_at": "2025-11-08T10:00:00Z",
      "updated_at": "2025-11-08T10:00:00Z"
    }
  ]
}
```

#### 详情（GET /api/agentcards/{id}/）

```bash
curl http://localhost:8000/api/agentcards/1/
```

**响应（完整版）**：
```json
{
  "id": 1,
  "namespace_id": "dev",
  "namespace_name": "开发环境",
  "name": "HPLC-001",
  "version": "1.0.0",
  "is_default_version": true,
  "is_active": true,
  "protocol_version": "0.3.0",
  "description": "Agilent 1260 高效液相色谱仪",
  "url": "https://lab.my-org.com/hplc-001",
  "preferred_transport": "http",
  "icon_url": null,
  "documentation_url": null,
  "capabilities": {"streaming": false, "tools": true},
  "default_input_modes": ["application/json"],
  "default_output_modes": ["application/json"],
  "skills": [
    {
      "name": "runAnalysis",
      "description": "运行液相色谱分析",
      "inputModes": ["application/json"],
      "outputModes": ["application/json"]
    }
  ],
  "provider": null,
  "additional_interfaces": [],
  "security_schemes": {},
  "security": [],
  "supports_authenticated_extended_card": false,
  "signatures": [],
  "domain_extensions": {
    "https://my-org.com/schemas/physicalAsset/v1": {
      "physicalAssetId": "HPLC-001",
      "locationId": "Lab-A",
      "status": "OPERATIONAL"
    }
  },
  "extension_schemas": [
    {
      "schema_uri": "https://my-org.com/schemas/physicalAsset/v1",
      "schema_type": "physicalAsset",
      "version": "v1",
      "is_active": true
    }
  ],
  "created_at": "2025-11-08T10:00:00Z",
  "updated_at": "2025-11-08T10:00:00Z",
  "created_by_username": "admin",
  "updated_by_username": "admin"
}
```

#### 创建（POST /api/agentcards/）

```bash
curl -X POST http://localhost:8000/api/agentcards/ \
  -H "Content-Type: application/json" \
  -u admin:password \
  -d '{
    "namespace": "dev",
    "name": "HPLC-001",
    "version": "1.0.0",
    "is_default_version": true,
    "is_active": true,
    "protocol_version": "0.3.0",
    "description": "Agilent 1260 高效液相色谱仪",
    "url": "https://lab.my-org.com/hplc-001",
    "preferred_transport": "http",
    "capabilities": {"streaming": false, "tools": true},
    "default_input_modes": ["application/json"],
    "default_output_modes": ["application/json"],
    "skills": [
      {
        "name": "runAnalysis",
        "description": "运行液相色谱分析",
        "inputModes": ["application/json"],
        "outputModes": ["application/json"]
      }
    ],
    "domain_extensions": {
      "https://my-org.com/schemas/physicalAsset/v1": {
        "physicalAssetId": "HPLC-001",
        "locationId": "Lab-A",
        "status": "OPERATIONAL"
      }
    }
  }'
```

#### 标准 JSON（GET /api/agentcards/{id}/standard-json/）

**返回符合 A2A 协议的标准 AgentCard JSON**

```bash
curl http://localhost:8000/api/agentcards/1/standard-json/
```

**查询参数**：
- `include_metadata=true`: 包含内部元数据（namespace, created_at 等）

**响应（符合 A2A 0.3.0 协议）**：
```json
{
  "protocolVersion": "0.3.0",
  "name": "HPLC-001",
  "description": "Agilent 1260 高效液相色谱仪",
  "url": "https://lab.my-org.com/hplc-001",
  "preferredTransport": "http",
  "version": "1.0.0",
  "capabilities": {"streaming": false, "tools": true},
  "defaultInputModes": ["application/json"],
  "defaultOutputModes": ["application/json"],
  "skills": [
    {
      "name": "runAnalysis",
      "description": "运行液相色谱分析",
      "inputModes": ["application/json"],
      "outputModes": ["application/json"]
    }
  ],
  "domainExtensions": {
    "https://my-org.com/schemas/physicalAsset/v1": {
      "physicalAssetId": "HPLC-001",
      "locationId": "Lab-A",
      "status": "OPERATIONAL"
    }
  }
}
```

#### 按命名空间查询（GET /api/agentcards/by-namespace/{namespace_id}/）

```bash
curl http://localhost:8000/api/agentcards/by-namespace/dev/
```

---

## 🔒 权限和认证

### 权限策略

**默认权限**：`IsAuthenticatedOrReadOnly`
- **读取**（GET）：无需认证，公开访问
- **写入**（POST/PUT/PATCH/DELETE）：需要认证

### 认证方式

#### 1. Session 认证（可浏览 API）

访问 http://localhost:8000/api/ 在右上角登录

#### 2. HTTP Basic 认证（API 请求）

```bash
curl -u username:password http://localhost:8000/api/agentcards/
```

#### 3. Token 认证（未来可添加）

可以添加 DRF Token 认证或 JWT 认证。

---

## 📄 分页

**默认分页**：每页 20 条

**响应格式**：
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/agentcards/?page=2",
  "previous": null,
  "results": [...]
}
```

**查询参数**：
- `page`: 页码（如 `?page=2`）
- `page_size`: 每页数量（如 `?page_size=50`，最大 100）

---

## 🔍 查询和过滤

### AgentCards 支持的过滤

```bash
# 按命名空间
GET /api/agentcards/?namespace=dev

# 按名称（模糊匹配）
GET /api/agentcards/?name=HPLC

# 只返回默认版本
GET /api/agentcards/?is_default_version=true

# 只返回激活的
GET /api/agentcards/?is_active=true

# 组合过滤
GET /api/agentcards/?namespace=dev&name=HPLC&is_default_version=true
```

---

## 🎯 常见使用场景

### 场景1：获取生产环境的所有 AgentCard

```bash
curl "http://localhost:8000/api/agentcards/?namespace=prod&is_active=true"
```

### 场景2：获取某个 Agent 的默认版本

```bash
curl "http://localhost:8000/api/agentcards/?namespace=prod&name=HPLC-001&is_default_version=true"
```

### 场景3：获取符合 A2A 协议的 AgentCard JSON

```bash
curl http://localhost:8000/api/agentcards/1/standard-json/
```

### 场景4：查看所有可用的 Schema

```bash
curl http://localhost:8000/api/schemas/catalog/
```

### 场景5：批量导入 AgentCard

```bash
# 从文件批量创建
for card in $(cat agentcards.json | jq -c '.[]'); do
  curl -X POST http://localhost:8000/api/agentcards/ \
    -H "Content-Type: application/json" \
    -u admin:password \
    -d "$card"
done
```

---

## 🌐 可浏览 API

**浏览器访问**：http://localhost:8000/api/

DRF 提供了一个**交互式的可浏览 API 界面**，可以：
- 查看所有端点
- 浏览数据
- 直接在界面中创建/更新/删除数据
- 查看请求/响应格式

**特性**：
- 表单填写（自动验证）
- 原始数据切换（JSON 格式）
- 过滤器
- 分页导航

---

## 🐛 错误处理

### 常见错误响应

#### 400 Bad Request（请求格式错误）

```json
{
  "namespace": ["此字段是必填项。"],
  "url": ["请输入有效的 URL。"]
}
```

#### 401 Unauthorized（未认证）

```json
{
  "detail": "身份认证信息未提供。"
}
```

#### 403 Forbidden（无权限）

```json
{
  "detail": "您没有执行该操作的权限。"
}
```

#### 404 Not Found（资源不存在）

```json
{
  "detail": "未找到。"
}
```

#### 409 Conflict（删除保护）

```json
{
  "detail": "无法删除命名空间 'dev'：该命名空间下有 5 个 AgentCard。"
}
```

---

## 📊 性能优化

### 1. 使用查询参数减少数据量

```bash
# 只获取默认版本（减少结果数量）
GET /api/agentcards/?is_default_version=true

# 只获取特定命名空间
GET /api/agentcards/?namespace=prod
```

### 2. 列表 vs 详情

- **列表端点**：返回精简版数据（快速）
- **详情端点**：返回完整数据（慢）

### 3. 分页

使用合适的 `page_size`，避免一次获取太多数据。

---

## 🔗 相关文档

- **Django Admin 指南**：`docs/admin-guide.md`
- **快速启动指南**：`QUICKSTART.md`
- **数据库约束说明**：`docs/database-constraints.md`
- **A2A 协议规范**：https://a2a-protocol.org/

---

## 💡 最佳实践

1. **使用标准 JSON 端点对接外部系统**：
   ```
   GET /api/agentcards/{id}/standard-json/
   ```
   返回完全符合 A2A 协议的 JSON。

2. **使用 Schema Catalog 实现动态发现**：
   ```
   GET /api/schemas/catalog/
   ```
   让客户端知道有哪些扩展字段可用。

3. **读写分离**：
   - 读取：直接访问 API（无需认证）
   - 写入：使用认证凭据

4. **版本管理**：
   - 使用 `?is_default_version=true` 获取默认版本
   - 创建新版本时保留旧版本

---

**API 状态**：🟢 就绪
**最后更新**：2025-11-08
