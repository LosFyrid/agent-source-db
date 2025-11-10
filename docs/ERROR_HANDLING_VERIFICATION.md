# 错误处理功能验证指南

## ✅ 已完成的修改

1. ✅ 创建 `core/templates/500.html` - 友好的500错误页面
2. ✅ 创建 `core/templates/404.html` - 友好的404错误页面
3. ✅ 创建 `core/middleware.py` - 错误追踪中间件
4. ✅ 更新 `core/settings.py` - 配置模板目录和中间件

---

## 🔍 如何在生产环境验证

### 方法1：验证404错误页面

访问一个不存在的页面：
```
https://your-domain.com/this-page-does-not-exist
```

**预期效果：**
- 显示友好的404页面（紫色渐变背景，白色卡片）
- 显示 "404 页面未找到"
- 有"返回管理后台"按钮

---

### 方法2：验证500错误页面

在生产环境(`DEBUG=False`)下，任何未处理的异常都会触发500错误页面。

**常见触发场景：**
1. 删除有外键依赖的对象
2. 提交无效的表单数据（如超出字段长度）
3. 访问需要特殊权限的页面

**预期效果：**
- 显示友好的500错误页面（紫色渐变背景，白色卡片）
- 显示 "⚠️ 系统遇到了一个错误"
- **显示错误追踪ID**（如：ERROR-A1B2C3D4）
- 有"返回管理后台"和"返回上一页"按钮
- 用户可以继续使用系统，不会卡住

---

### 方法3：验证API错误响应

如果有API请求失败（`/api/` 路径），会返回JSON格式的错误：

```bash
curl https://your-domain.com/api/invalid-endpoint/
```

**预期响应：**
```json
{
    "error": "Internal Server Error",
    "message": "服务器内部错误，请稍后重试",
    "error_id": "A1B2C3D4",
    "detail": null
}
```

---

## 📋 验证检查清单

部署到生产环境后，验证以下内容：

- [ ] 访问不存在的页面，显示友好的404页面
- [ ] 触发500错误，显示友好的错误页面（带追踪ID）
- [ ] 错误页面有"返回管理后台"按钮且可以点击
- [ ] 点击"返回上一页"按钮正常工作
- [ ] API错误返回JSON格式（而不是HTML）
- [ ] 错误追踪ID被正确记录到日志文件

---

## 🔍 查看错误日志

### 方法1：在Docker容器中查看
```bash
# 查看错误日志
docker-compose exec web tail -f logs/error.log

# 搜索特定错误ID（假设错误ID是 A1B2C3D4）
docker-compose exec web grep "ERROR-A1B2C3D4" logs/error.log
```

### 方法2：在宿主机查看
```bash
# 进入日志目录
cd /path/to/agent-source-db/logs

# 实时查看错误日志
tail -f error.log

# 查看最近的100行错误
tail -100 error.log

# 搜索特定错误ID
grep "ERROR-A1B2C3D4" error.log
```

---

## 📊 错误日志格式

每个错误都会记录以下信息：

```
ERROR [ERROR-A1B2C3D4] Unhandled exception
Extra data:
  - error_id: A1B2C3D4
  - path: /admin/documents/agentcard/13/change/
  - method: POST
  - user: admin
  - ip: 192.168.1.100
  - exception_type: ValidationError
  - exception_message: 缺少必填字段：testfield1
Stack trace:
  [完整的堆栈追踪信息...]
```

---

## 🚀 部署到生产环境

确保生产环境配置了以下环境变量（`.env.prod`）：

```env
# 必须设置为 False
DJANGO_DEBUG=False

# 设置允许的主机
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# 可选：管理员邮箱（用于接收错误通知）
ADMIN_EMAIL=admin@your-domain.com
```

---

## ⚠️ 重要提示

1. **开发环境** (`DEBUG=True`)：
   - 会显示Django默认的调试错误页面（带完整堆栈追踪）
   - 自定义错误页面**不会**显示
   - 这是正常的！只有生产环境才会使用自定义错误页面

2. **生产环境** (`DEBUG=False`)：
   - 会显示友好的自定义错误页面
   - 不会泄露敏感的堆栈追踪信息
   - 错误详情会记录到日志文件

---

## 📞 如果遇到问题

如果错误页面没有正确显示，检查：

1. `DEBUG=False` 是否正确设置
2. `ALLOWED_HOSTS` 是否包含你的域名
3. 模板文件是否存在：`core/templates/500.html` 和 `404.html`
4. 中间件是否正确配置在 `settings.py` 中
5. Django是否正确重启（`docker-compose restart web`）
