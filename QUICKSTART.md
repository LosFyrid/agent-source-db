# AgentCard 管理系统 - 快速启动指南

## 🚀 5分钟快速启动

### 1. 启动服务

```bash
# 确保 Docker 正在运行
docker-compose up -d

# 等待服务启动（约10秒）
```

### 2. 创建管理员账号

```bash
docker-compose exec web python manage.py createsuperuser

# 按提示输入：
# - 用户名: admin
# - 邮箱: admin@example.com
# - 密码: ******
```

### 3. 访问管理后台

浏览器打开：**http://localhost:8000/admin**

使用刚创建的账号登录。

---

## 📦 系统功能

### 核心模型

1. **Namespace（命名空间）**：环境隔离（dev、test、prod）
2. **Schema Registry（Schema定义）**：L2扩展字段定义
3. **Schema Field（Schema字段）**：可视化定义字段
4. **AgentCard**：符合 A2A 协议的 Agent 卡片

### 特色功能

✅ **可视化 Schema 管理**：不需要手写 JSON Schema
✅ **自动验证**：字段类型和约束自动验证
✅ **删除保护**：防止误删除重要数据
✅ **高性能查询**：JSONB GIN 索引优化
✅ **完整的 Django Admin**：开箱即用的管理界面

---

## 🎯 推荐工作流程

### 第一步：创建命名空间

1. 进入 **"命名空间"**
2. 添加：
   - `dev` - 开发环境
   - `test` - 测试环境
   - `prod` - 生产环境

### 第二步：定义 Schema（可选）

如果需要 L2 扩展字段：

1. 进入 **"Schema定义"**
2. 创建新 Schema：
   - Schema URI: `https://your-org.com/schemas/physicalAsset/v1`
   - 类型: `physicalAsset`
   - 版本: `v1`
3. **保存后**，在同一页面添加字段（内联编辑）

**示例字段**：
```
| 字段名              | 类型  | 必填 | 说明       |
|--------------------|-------|------|-----------|
| physicalAssetId    | 文本  | ✓    | 资产编号   |
| locationId         | 文本  | ✓    | 位置ID     |
| status             | 枚举  | ✓    | 状态       |
```

枚举值（status）：`["OPERATIONAL", "MAINTENANCE", "OFFLINE"]`

### 第三步：创建 AgentCard

1. 进入 **"AgentCards"**
2. 填写基本信息：
   - 命名空间: `dev`
   - 名称: `HPLC-001`
   - 版本: `1.0.0`
   - URL: `https://lab.your-org.com/hplc-001`
   - 描述: `Agilent 1260 高效液相色谱仪`

3. 填写 L1 能力配置（JSON）：
```json
// capabilities
{"streaming": false, "tools": true}

// default_input_modes
["application/json", "text/plain"]

// default_output_modes
["application/json"]

// skills
[{
  "name": "runAnalysis",
  "description": "运行液相色谱分析",
  "inputModes": ["application/json"],
  "outputModes": ["application/json"]
}]
```

4. 填写 L2 扩展（使用刚才定义的 Schema）：
```json
{
  "https://your-org.com/schemas/physicalAsset/v1": {
    "physicalAssetId": "HPLC-001",
    "locationId": "BuildingA-Lab1-Rack2",
    "status": "OPERATIONAL"
  }
}
```

5. 保存并查看预览

---

## 📚 文档索引

| 文档 | 用途 |
|------|------|
| `docs/admin-guide.md` | Django Admin 详细使用指南 |
| `docs/database-constraints.md` | 完整的数据库约束说明 |
| `docs/constraint-enhancements-report.md` | 约束增强实施报告 |
| `docs/database.md` | 原始设计文档（L1/L2 扩展理论） |
| `CLAUDE.md` | 项目架构和开发环境说明 |

---

## ✅ 系统验证

运行测试验证系统正常：

```bash
docker-compose exec web python test_constraints.py
```

**期望输出**：
```
✓ 默认版本唯一性              ✓ 通过
✓ Namespace删除保护        ✓ 通过
✓ Schema删除保护           ✓ 通过
✓ SchemaField约束验证      ✓ 通过
✓ GIN索引                ✓ 通过

✓ 所有测试通过！约束工作正常。
```

---

## 🔧 常用命令

```bash
# 查看日志
docker-compose logs -f web

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 清理数据库（警告：删除所有数据）
docker-compose down -v
docker-compose up -d
docker-compose exec web python manage.py migrate

# 进入 Django Shell
docker-compose exec web python manage.py shell

# 导出数据
docker-compose exec web python manage.py dumpdata documents --indent 2 > backup.json

# 导入数据
docker-compose exec web python manage.py loaddata backup.json
```

---

## 🛡️ 数据安全保障

系统已实施以下保护机制：

✅ **默认版本唯一性**：数据库级约束，无法绕过
✅ **删除保护**：有 AgentCard 的 Namespace 无法删除
✅ **Schema 保护**：被使用的 Schema 无法删除
✅ **字段验证**：约束与类型自动匹配验证
✅ **性能优化**：JSONB GIN 索引加速查询

---

## 🐛 故障排查

### 问题1：无法创建第二个默认版本

**错误信息**：
```
Agent 'HPLC-001' 在命名空间 'dev' 已存在默认版本 '1.0.0'。
请先取消原默认版本。
```

**解决方案**：
1. 进入现有的默认版本（如 `1.0.0`）
2. 取消勾选 **"是否为默认版本"**
3. 保存
4. 然后将新版本设为默认

### 问题2：无法删除 Namespace

**错误信息**：
```
无法删除命名空间 'dev'：该命名空间下有 5 个 AgentCard。
```

**解决方案**：
1. 先删除或移动所有 AgentCard
2. 然后再删除 Namespace

### 问题3：字段约束设置错误

**错误信息**：
```
整数类型不能设置最小/最大长度，请使用最小/最大值。
```

**解决方案**：
参考 `docs/admin-guide.md` 的字段类型说明，使用正确的约束。

---

## 🎓 下一步学习

1. **基础使用**：阅读 `docs/admin-guide.md`
2. **理解约束**：阅读 `docs/database-constraints.md`
3. **扩展 API**：开发 REST API（使用 Django REST Framework）
4. **集成 Nacos**：从 Nacos 批量导入 AgentCard

---

## 💡 最佳实践

1. **命名规范**：
   - Namespace ID: 小写字母 + 连字符（如 `lab-instruments`）
   - Schema URI: 使用组织域名（如 `https://your-org.com/schemas/...`）
   - 版本号: 使用语义化版本（如 `1.0.0`, `2.1.3-beta`）

2. **Schema 管理**：
   - 先注册 Schema，再使用
   - 一个 Schema 定义不变，修改时创建新版本
   - 使用有意义的字段名（camelCase 风格）

3. **AgentCard 管理**：
   - 开发环境使用 `dev` 命名空间
   - 测试通过后复制到 `prod`
   - 一个 Agent 可以有多个版本，但只能有一个默认版本

---

## 🆘 获取帮助

- **GitHub Issues**：报告 Bug 或提出功能建议
- **文档索引**：查看 `docs/` 目录下的详细文档
- **测试脚本**：运行 `test_constraints.py` 验证系统状态

---

**系统状态**：🟢 生产就绪
**最后更新**：2025-11-08
