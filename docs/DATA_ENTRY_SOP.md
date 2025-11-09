# AgentCard 数据录入操作规范 (SOP)

**版本**: 1.0
**面向**: 数据录入人员
**预计时间**: 首次录入 10-15 分钟

---

## 📋 目录

1. [登录系统](#1-登录系统)
2. [录入新 AgentCard](#2-录入新-agentcard)
3. [编辑已有 AgentCard](#3-编辑已有-agentcard)
4. [查看和导出数据](#4-查看和导出数据)
5. [常见问题](#5-常见问题)

---

## 1. 登录系统

### 1.1 访问地址

```
http://<服务器地址>:8000/admin/
```

### 1.2 登录凭证

- 使用管理员提供的用户名和密码
- 如忘记密码，联系系统管理员

### 1.3 首次登录

登录后会看到主页，显示：
- **命名空间** (Namespaces)
- **AgentCards**
- **Schema定义** (Schema Registries)

---

## 2. 录入新 AgentCard

### 2.1 准备工作（首次录入）

#### 步骤 1: 确认或创建命名空间

1. 点击 **"命名空间"** → **"添加命名空间"**
2. 填写：
   - **ID**: 环境标识
   - **名称**: 显示名称
   - **描述**: 用途说明（可选）
3. 点击 **"保存"**


---

### 2.2 录入 AgentCard（核心流程）

#### 步骤 1: 创建新 AgentCard

1. 点击 **"AgentCards"** → **"添加 AgentCard"**
2. 进入录入表单

#### 步骤 2: 填写基本信息（必填）

| 字段 | 说明 | 示例 |
|------|------|------|
| **命名空间** | 选择环境 | `Instrument` |
| **名称** | Agent 唯一名称 | `HPLC-001` |
| **版本号** | 版本标识 | `1.0.0` |
| **描述** | Agent 功能说明 | "Agilent 1260 高效液相色谱仪" |
| **主要端点 URL** | Agent 访问地址 | `https://lab.example.com/hplc-001` |
| **首选传输协议** | 通信协议 | 选择 `HTTP+JSON` 或 `JSONRPC` |

#### 步骤 3: 填写输入输出模式（必填）

**默认输入 MIME 类型** (Default input modes):
```json
["application/json", "text/plain"]
```

**默认输出 MIME 类型** (Default output modes):
```json
["application/json"]
```

> 💡 **如何填写**: 点击字段右侧的 **🔧** 图标，在 JSON 编辑器中填写数组格式

#### 步骤 4: 填写技能列表（必填）

点击 **"Skills"** 右侧的 **🔧** 图标，填写 JSON 格式：

```json
[
  {
    "id": "run_analysis",
    "name": "运行分析",
    "description": "执行样品分析任务",
    "tags": ["analysis", "hplc"],
    "inputModes": ["application/json"],
    "outputModes": ["application/json"]
  }
]
```

**必填字段**:
- `id`: 技能唯一标识（小写字母+下划线）
- `name`: 技能名称
- `description`: 功能说明
- `tags`: 标签数组（至少一个）

#### 步骤 5: 填写能力（可选）

勾选 Agent 支持的能力：
- ☐ **Streaming** - 支持 SSE 流式响应
- ☐ **Push notifications** - 支持推送通知
- ☐ **State transition history** - 提供状态转换历史

#### 步骤 6: 添加扩展（可选）

如需添加扩展信息（如物理资产信息）：

1. 滚动到页面底部 **"Agent扩展"** 区域
2. 点击 **"添加另一个 Agent扩展"**
3. 填写：
   - **URI**: 扩展标识（如 `https://your-org.com/extensions/physical-asset/v1`）
   - **描述**: 扩展说明
   - **Params**: 扩展数据（JSON 格式）
   - **Schema**: 选择已定义的 Schema（可选）

示例 params:
```json
{
  "assetId": "HPLC-001",
  "location": "实验室 A",
  "status": "OPERATIONAL"
}
```

#### 步骤 7: 保存

选择保存方式：
- **保存并继续编辑** - 保存但停留在当前页面（推荐，可以多次保存）
- **保存并新增另一个** - 保存后创建新 AgentCard
- **保存** - 保存并返回列表

---

### 2.3 渐进式录入（分步保存）

✅ **系统支持草稿功能**，你可以：

1. 先填写必填的基本信息
2. 点击 **"保存并继续编辑"**
3. 稍后再补充可选字段
4. 多次保存，逐步完善

⚠️ **注意**:
- 保存时只验证格式，允许不完整
- 对外输出（接入nacos注册）时会严格验证，不完整的 AgentCard 无法导出

---

## 3. 编辑已有 AgentCard

### 3.1 查找 AgentCard

1. 点击 **"AgentCards"**
2. 使用搜索框搜索名称
3. 或使用右侧过滤器：
   - 按命名空间筛选
   - 按激活状态筛选
   - 按默认版本筛选

### 3.2 编辑

1. 点击要编辑的 AgentCard 名称
2. 修改字段
3. 点击 **"保存并继续编辑"** 或 **"保存"**

### 3.3 复制创建新版本

1. 打开现有 AgentCard
2. 点击右上角 **"保存为新对象"**
3. 修改版本号（如 `1.0.0` → `2.0.0`）
4. 保存

---

## 4. 查看和导出数据

### 4.1 查看列表

在 AgentCards 列表页，显示：
- 命名空间::名称@版本
- 描述
- 是否激活
- 是否默认版本

### 4.2 预览 JSON（查看完整数据）

1. 打开 AgentCard 编辑页
2. 滚动到页面底部
3. 查看 **"JSON 预览"** 区域
4. 显示符合 A2A 协议的完整 JSON

⚠️ **如果显示错误**: 说明数据不完整，需要补充必填字段

### 4.3 通过 API 导出

完整的 AgentCard 可通过 API 获取：

```bash
# 标准 A2A 格式
GET /api/agentcards/{id}/standard_json/

# 原始格式（含草稿）
GET /api/agentcards/{id}/
```

---



## 📋 快速检查清单

录入新 AgentCard 前，确认：

- [ ] 已创建或选择命名空间
- [ ] 名称、版本号在命名空间唯一（不与现有 AgentCard 冲突）
- [ ] URL 使用 HTTPS（或 localhost）
- [ ] 已填写 defaultInputModes（非空数组）
- [ ] 已填写 defaultOutputModes（非空数组）
- [ ] 已填写至少一个 skill
- [ ] JSON 格式正确（使用在线验证器检查）
- [ ] 保存后检查 JSON 预览无错误

---

## 🆘 获取帮助

### 遇到问题时：

1. **查看错误提示** - 页面顶部红色框会显示具体错误
2. **检查 JSON 格式** - 使用 https://jsonlint.com/ 验证
3. **查看监控日志** - 访问 `/admin/system-status/` 查看错误日志
4. **联系管理员** - 提供具体的错误信息截图

### 相关文档：

- **详细操作指南**: [ADMIN_GUIDE.md](ADMIN_GUIDE.md)
- **系统功能说明**: [SYSTEM_FEATURES.md](SYSTEM_FEATURES.md)
- **API 文档**: [API-GUIDE.md](API-GUIDE.md)

---

## 📝 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| 1.0 | 2025-11-09 | 初始版本 |

