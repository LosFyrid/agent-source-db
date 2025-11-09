# AgentCard 系统部署指南

**面向**: 技术运维人员  
**预计时间**: 30 分钟完成首次部署

---

## 系统概述

**AgentCard 数据库管理系统** - 基于 A2A 协议的 Agent 元数据管理平台

- **技术栈**: Django 5.2.8 + PostgreSQL 18 + Django REST Framework
- **架构**: Docker 容器化部署，支持测试/生产环境隔离
- **功能**: Django Admin 后台管理 + REST API 接口

---

## 前置要求

服务器需要安装：
- Git
- Docker & Docker Compose
- 防火墙开放端口: 8000 (生产), 8001 (测试)

---

## 快速部署

### 1. 克隆代码

```bash
git clone https://github.com/YOUR_USERNAME/agent-source-db.git
cd agent-source-db
```

### 2. 配置环境变量

```bash
# 生产环境
cp .env.prod.example .env.prod
nano .env.prod
```

**必须修改的配置**:
```ini
# Django
DJANGO_SECRET_KEY=<运行命令生成: python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=YOUR_SERVER_IP,localhost

# PostgreSQL
POSTGRES_PASSWORD=<强密码>
DATABASE_URL=postgres://produser:<刚才的密码>@db:5432/agentcard_prod
```

**测试环境同理**（复制 `.env.test.example` 为 `.env.test`）

### 3. 部署

```bash
# 方式 1: 使用脚本（推荐）
./scripts/deploy.sh prod  # 生产环境
./scripts/deploy.sh test  # 测试环境

# 方式 2: 手动部署
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 4. 配置自动备份（重要）

```bash
./scripts/setup_cron.sh
```

按提示选择：
- 备份频率: **每天凌晨 3 点**
- 备份环境: **仅生产环境**

---

## 访问系统

| 环境 | 管理后台 | API |
|------|---------|-----|
| 生产 | `http://SERVER_IP:8000/admin/` | `http://SERVER_IP:8000/api/` |
| 测试 | `http://SERVER_IP:8001/admin/` | `http://SERVER_IP:8001/api/` |

---

## 日常运维

### 代码更新

```bash
# 1. 测试环境验证
cd agent-source-db
git pull origin develop
./scripts/deploy.sh test

# 2. 验证通过后部署生产
git checkout main
git pull origin main
./scripts/deploy.sh prod
```

### 服务管理

```bash
# 查看状态
docker-compose -f docker-compose.prod.yml ps

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 停止服务
docker-compose -f docker-compose.prod.yml stop
```

### 数据库管理

```bash
# 手动备份
./scripts/backup_database.sh prod

# 恢复备份
gunzip backups/prod/backup_prod_20250109_030000.sql.gz
cat backups/prod/backup_prod_20250109_030000.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U produser agentcard_prod

# 复制生产数据到测试环境
./scripts/copy_prod_to_test.sh
```

---

## 监控与日志

### 系统日志位置

```
logs/
├── django.log      # Django 应用日志
├── error.log       # 错误和警告日志
├── access.log      # HTTP 访问日志
├── db.log          # 数据库慢查询和错误
└── backup.log      # 备份任务日志
```

### 日志特性
- **自动轮转**: 单文件 50MB，保留 10 个历史文件
- **分级记录**: INFO / WARNING / ERROR
- **结构化格式**: 包含时间戳、模块名、日志级别

### 查看日志

```bash
# 实时查看应用日志
tail -f logs/django.log

# 查看错误日志
tail -100 logs/error.log

# 查看备份日志
tail -f logs/backup.log

# Docker 容器日志
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f db
```

---

## 备份策略

### 自动备份
- **频率**: 每天凌晨 3:00
- **保留**: 最近 7 个备份
- **位置**: `backups/prod/`
- **格式**: SQL dump + gzip 压缩

### 月度检查清单
- [ ] 确认 crontab 正常运行: `crontab -l`
- [ ] 确认备份文件生成: `ls -lh backups/prod/`
- [ ] 确认备份日志无错误: `tail -100 logs/backup.log`
- [ ] 验证备份文件大小合理（不是 0 字节）

### 备份验证（每季度）
```bash
# 恢复到测试环境验证
./scripts/copy_prod_to_test.sh
docker-compose -f docker-compose.test.yml exec web python manage.py shell
>>> from documents.models import AgentCard
>>> AgentCard.objects.count()
```

---


## 常用命令速查

```bash
# === 部署 ===
./scripts/deploy.sh prod              # 部署/更新生产环境
./scripts/deploy.sh test              # 部署/更新测试环境

# === 备份 ===
./scripts/backup_database.sh prod     # 手动备份生产数据库
./scripts/setup_cron.sh               # 配置自动备份

# === 服务管理 ===
docker-compose -f docker-compose.prod.yml ps       # 查看状态
docker-compose -f docker-compose.prod.yml restart  # 重启
docker-compose -f docker-compose.prod.yml logs -f  # 查看日志

# === 数据库 ===
./scripts/copy_prod_to_test.sh        # 生产数据复制到测试环境

# === Django 管理 ===
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
```

---

## 环境架构

| 环境 | Git 分支 | 端口 | 数据库 | 用途 |
|------|---------|------|--------|------|
| 开发 | feature/*, develop | localhost:8000 | 本地测试数据 | 开发者本地开发 |
| 测试 | develop | 8001 | agentcard_test | 验证代码更新 |
| 生产 | main | 8000 | agentcard_prod | 正式使用 |

---

## 数据安全

### 数据持久化
- 数据库数据存储在 Docker Volume 中
- `git pull` 和 `docker-compose restart` **不会**影响数据
- 只有 `docker-compose down -v` 会删除数据（**永远不要用**）

### 敏感文件
以下文件包含密码，**不要**提交到 Git：
- `.env.prod`
- `.env.test`

建议备份到密码管理器或加密存储。

---

## 技术支持

- **详细文档**: `docs/DEPLOYMENT.md`, `docs/BACKUP_STRATEGY.md`
- **脚本说明**: `scripts/README.md`
- **API 文档**: `docs/API-GUIDE.md`

---

## 关键注意事项

⚠️ **首次部署后必须配置自动备份** - 运行 `./scripts/setup_cron.sh`  
⚠️ **每月检查备份日志** - `tail -100 logs/backup.log`  
⚠️ **测试环境先验证** - 代码更新先部署到测试环境  
⚠️ **保护配置文件** - `.env.prod` 泄露等于密码泄露  
⚠️ **定期验证备份** - 每季度恢复一次测试

---

**部署完成后，系统将提供稳定的 Django Admin 后台和 REST API 服务。**
