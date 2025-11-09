# Docker Compose 环境说明

本项目有 3 个 Docker Compose 配置文件，分别对应不同的使用场景。

---

## 📁 文件列表

| 文件名 | 用途 | 使用场景 | 是否提交 Git |
|--------|------|---------|-------------|
| `docker-compose.yml` | **开发环境** | 本地开发、调试 | ✅ 是 |
| `docker-compose.prod.yml` | **生产环境** | 正式部署 | ✅ 是 |
| `docker-compose.test.yml` | **测试环境** | 预发布测试 | ✅ 是 |

**重要**: 所有 docker-compose 文件都应该提交到 Git，因为它们是基础设施配置，不包含敏感信息。

---

## 🔍 三个环境的区别

### 核心差异对比

| 特性 | 开发环境<br/>`docker-compose.yml` | 测试环境<br/>`docker-compose.test.yml` | 生产环境<br/>`docker-compose.prod.yml` |
|------|----------------------------------|--------------------------------------|--------------------------------------|
| **服务器** | Django dev server | Gunicorn (2 workers) | Gunicorn (4 workers) |
| **端口** | 8000 | 8001 | 8000 |
| **环境文件** | `.env.dev` | `.env.test` | `.env.prod` |
| **源代码挂载** | ✅ 是（实时更新） | ❌ 否（镜像内） | ❌ 否（镜像内） |
| **日志持久化** | ❌ 否（宿主机目录） | ✅ 是（Docker 卷） | ✅ 是（Docker 卷） |
| **静态文件** | ❌ 不收集 | ✅ Docker 卷 | ✅ Docker 卷 |
| **数据库端口** | 5432（暴露） | 不暴露 | 不暴露 |
| **自动重启** | ❌ 否 | ✅ 是 | ✅ 是 |

---

## 🚀 使用方法

### 1. 开发环境（默认）

**用途**: 本地开发、代码热重载、调试

```bash
# 启动（默认使用 docker-compose.yml）
docker-compose up -d

# 查看日志
docker-compose logs -f web

# 停止
docker-compose down

# 重启（代码修改后自动生效）
docker-compose restart web
```

**特点**:
- ✅ 代码实时更新（通过卷挂载）
- ✅ Django dev server 自动重载
- ✅ 数据库端口暴露（方便 GUI 工具连接）
- ✅ 日志直接写入宿主机 `logs/` 目录
- ❌ 性能较低（不适合压力测试）

---

### 2. 测试环境

**用途**: 预发布验证、集成测试、性能测试

```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 查看日志
docker-compose -f docker-compose.test.yml logs -f web

# 停止
docker-compose -f docker-compose.test.yml down

# 查看测试环境日志（Docker 卷内）
docker-compose -f docker-compose.test.yml exec web tail -f /app/logs/django.log
```

**特点**:
- ✅ 使用 Gunicorn（模拟生产环境）
- ✅ 端口 8001（与生产环境隔离）
- ✅ 独立的数据库和日志卷
- ✅ 自动重启（服务崩溃后自动恢复）
- ⚠️ 代码修改需要重新构建镜像

---

### 3. 生产环境

**用途**: 正式部署、对外服务

```bash
# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f web

# 停止
docker-compose -f docker-compose.prod.yml down

# 查看生产日志（Docker 卷内）
docker-compose -f docker-compose.prod.yml exec web tail -f /app/logs/error.log
```

**特点**:
- ✅ 使用 Gunicorn (4 workers) - 高性能
- ✅ 端口 8000
- ✅ 数据库端口不暴露（安全）
- ✅ 自动重启
- ✅ 日志、静态文件持久化
- ⚠️ 代码修改需要重新构建镜像

---

## 📝 环境变量文件说明

每个环境使用独立的环境变量文件：

| 环境 | 环境文件 | 是否提交 Git | 说明 |
|------|---------|-------------|------|
| 开发 | `.env.dev` | ❌ 否 | 本地开发配置（弱密码） |
| 测试 | `.env.test` | ❌ 否 | 测试环境配置 |
| 生产 | `.env.prod` | ❌ 否 | 生产环境配置（强密码） |
| 示例 | `.env.*.example` | ✅ 是 | 配置模板 |

**重要**:
- ✅ **提交**: docker-compose 文件、`.env.*.example` 模板
- ❌ **不提交**: 实际的 `.env.*` 文件（包含密码等敏感信息）

---

## 🔒 .gitignore 配置

当前 `.gitignore` 已正确配置：

```gitignore
# Environment variables (IMPORTANT: Never commit these!)
.env
.env.dev
.env.test
.env.prod
*.env
```

这确保了所有环境变量文件都不会被提交到 Git。

---

## 🛠️ 常见使用场景

### 场景 1: 本地开发（日常工作）

```bash
# 1. 启动开发环境
docker-compose up -d

# 2. 修改代码（自动生效）
# ...编辑代码...

# 3. 查看实时日志
tail -f logs/django.log

# 4. 停止
docker-compose down
```

---

### 场景 2: 提交前测试（确保生产环境兼容）

```bash
# 1. 构建并启动测试环境
docker-compose -f docker-compose.test.yml up -d --build

# 2. 运行测试
docker-compose -f docker-compose.test.yml exec web python manage.py test

# 3. 手动测试 API
curl http://localhost:8001/api/agentcards/

# 4. 确认没问题后停止
docker-compose -f docker-compose.test.yml down
```

---

### 场景 3: 生产部署（服务器上）

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 创建生产环境配置（首次）
cp .env.prod.example .env.prod
nano .env.prod  # 配置强密码

# 3. 构建并启动
docker-compose -f docker-compose.prod.yml up -d --build

# 4. 收集静态文件
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 5. 应用迁移
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# 6. 检查健康状态
curl http://localhost:8000/health/ready/
```

---

### 场景 4: 同时运行多个环境（开发 + 测试）

```bash
# 开发环境（端口 8000）
docker-compose up -d

# 测试环境（端口 8001）
docker-compose -f docker-compose.test.yml up -d

# 现在可以同时访问：
# - 开发环境: http://localhost:8000
# - 测试环境: http://localhost:8001
```

---

## 🔄 迁移数据（从开发环境到测试环境）

```bash
# 1. 导出开发环境数据
docker-compose exec web python manage.py dumpdata > dev_data.json

# 2. 复制到测试环境
docker-compose -f docker-compose.test.yml exec -T web python manage.py loaddata dev_data.json
```

---

## 📊 环境变量示例对比

### `.env.dev.example` (开发环境)

```bash
DJANGO_SECRET_KEY=local-dev-key-insecure
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=mydb
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword  # 简单密码（开发用）
POSTGRES_HOST=db
POSTGRES_PORT=5432

DATABASE_URL=postgres://myuser:mypassword@db:5432/mydb
```

### `.env.prod.example` (生产环境)

```bash
DJANGO_SECRET_KEY=生成的强随机密钥  # 使用 openssl rand -base64 32
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,your-ip

POSTGRES_DB=agentcard_prod
POSTGRES_USER=produser
POSTGRES_PASSWORD=超强密码  # 至少 32 位随机字符
POSTGRES_HOST=db
POSTGRES_PORT=5432

DATABASE_URL=postgres://produser:超强密码@db:5432/agentcard_prod
```

---

## ⚠️ 重要提醒

### ✅ 应该提交到 Git

- `docker-compose.yml` - 开发环境配置
- `docker-compose.prod.yml` - 生产环境配置
- `docker-compose.test.yml` - 测试环境配置
- `.env.dev.example` - 开发环境变量模板
- `.env.prod.example` - 生产环境变量模板
- `.env.test.example` - 测试环境变量模板

### ❌ 不应该提交到 Git

- `.env.dev` - 开发环境实际配置（包含密码）
- `.env.prod` - 生产环境实际配置（包含密码）
- `.env.test` - 测试环境实际配置（包含密码）
- `logs/` - 日志文件
- `db.sqlite3` - 开发用 SQLite 数据库

---

## 🎯 总结

| 问题 | 答案 |
|------|------|
| `docker-compose.yml` 有什么用？ | **开发环境**配置，供本地开发使用 |
| 需要 gitignore 吗？ | ❌ **不需要**，应该提交到 Git |
| 什么需要 gitignore？ | `.env.dev`、`.env.prod`、`.env.test` 等环境变量文件 |
| 默认用哪个？ | 运行 `docker-compose up` 时默认用 `docker-compose.yml` |
| 如何切换环境？ | 使用 `-f` 参数：`docker-compose -f docker-compose.prod.yml up` |

---

**下一步**: 确保你的 `.gitignore` 正确配置，然后可以安心提交所有 docker-compose 文件到 Git。
