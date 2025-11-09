# AgentCard 系统部署指南

本文档详细说明如何在服务器上部署和维护 AgentCard 系统。

---

## 📋 目录

1. [环境架构](#环境架构)
2. [服务器准备](#服务器准备)
3. [首次部署](#首次部署)
4. [日常运维](#日常运维)
5. [数据管理](#数据管理)
6. [故障排查](#故障排查)

---

## 🏗️ 环境架构

### 环境划分

系统分为三个独立环境：

| 环境 | 用途 | 端口 | 数据库 | Git分支 |
|------|------|------|--------|---------|
| **开发环境** | 开发者本地开发 | localhost:8000 | 本地测试数据 | feature/*, develop |
| **测试环境** | 验证代码更新 | 服务器IP:8001 | 独立测试数据 | develop |
| **生产环境** | 正式使用 | 服务器IP:8000 | 生产数据 | main |

### 工作流程

```
开发者本地开发 → Git Push → 测试环境验证 → 生产环境部署
```

---

## 🖥️ 服务器准备

### 1.  Docker

### 2.  Git

### 3. 防火墙配置

```bash
# 开放必要端口
sudo ufw allow 8000/tcp  # 生产环境
sudo ufw allow 8001/tcp  # 测试环境
sudo ufw enable
```

---

## 🚀 首次部署

### 测试环境部署

#### 步骤 1: 克隆代码

```bash
# 在服务器上创建项目目录
mkdir -p ~/projects
cd ~/projects

# 克隆代码仓库（使用 HTTPS 或 SSH）
git clone https://github.com/YOUR_USERNAME/agent-source-db.git
cd agent-source-db

# 切换到 develop 分支（测试环境）
git checkout develop
```

#### 步骤 2: 配置环境变量

```bash
# 复制环境变量模板
cp .env.test.example .env.test

# 编辑配置文件
nano .env.test
```

**必须修改的配置项**:

```ini
# 1. 生成 Django SECRET_KEY
DJANGO_SECRET_KEY=<运行下面的命令生成>

# 2. 设置服务器 IP
DJANGO_ALLOWED_HOSTS=192.168.1.100,localhost,127.0.0.1

# 3. 设置数据库密码
POSTGRES_PASSWORD=<设置强密码>
DATABASE_URL=postgres://testuser:<刚才设置的密码>@db:5432/agentcard_test
```

**生成密钥**:

```bash
# 方法 1: 使用 Python（推荐）
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 方法 2: 使用 OpenSSL
openssl rand -base64 50
```

#### 步骤 3: 启动服务

```bash
# 构建并启动容器
docker-compose -f docker-compose.test.yml up -d --build

# 查看启动日志
docker-compose -f docker-compose.test.yml logs -f
```

等待看到类似信息：
```
web_1  | Listening at: http://0.0.0.0:8000
db_1   | database system is ready to accept connections
```

#### 步骤 4: 初始化数据库

```bash
# 运行数据库迁移
docker-compose -f docker-compose.test.yml exec web python manage.py migrate

# 收集静态文件
docker-compose -f docker-compose.test.yml exec web python manage.py collectstatic --noinput

# 创建管理员账号
docker-compose -f docker-compose.test.yml exec web python manage.py createsuperuser
```

按提示输入：
- 用户名: `admin`
- 邮箱: `admin@example.com`
- 密码: （输入两次，至少8位）

#### 步骤 5: 验证部署

```bash
# 在浏览器访问
http://YOUR_SERVER_IP:8001/admin/
http://YOUR_SERVER_IP:8001/api/
```

如果看到 Django Admin 登录页面，说明部署成功！

---

### 生产环境部署

生产环境部署流程与测试环境**完全相同**，只需替换以下内容：

| 项目 | 测试环境 | 生产环境 |
|------|----------|----------|
| Git 分支 | `develop` | `main` |
| 配置文件 | `.env.test` | `.env.prod` |
| Docker Compose | `docker-compose.test.yml` | `docker-compose.prod.yml` |
| 端口 | 8001 | 8000 |

**部署命令示例**:

```bash
cd ~/projects/agent-source-db
git checkout main
cp .env.prod.example .env.prod
nano .env.prod  # 修改配置

# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## 🔧 日常运维

### 代码更新流程

当开发者修复了 Bug 或添加了新功能后：

#### 1. 测试环境验证（先在测试环境验证）

```bash
cd ~/projects/agent-source-db

# 拉取最新代码
git pull origin develop

# 重新构建并重启（代码更新）
docker-compose -f docker-compose.test.yml up -d --build

# 运行数据库迁移（如果有新字段）
docker-compose -f docker-compose.test.yml exec web python manage.py migrate

# 收集静态文件（如果有前端更新）
docker-compose -f docker-compose.test.yml exec web python manage.py collectstatic --noinput
```

#### 2. 生产环境部署（验证通过后）

```bash
cd ~/projects/agent-source-db
git checkout main
git pull origin main

# 重新构建并重启
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 服务管理命令

```bash
# 查看运行状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志（最近100行）
docker-compose -f docker-compose.prod.yml logs --tail=100 -f

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 停止服务
docker-compose -f docker-compose.prod.yml stop

# 启动服务
docker-compose -f docker-compose.prod.yml start

# 完全停止并删除容器（数据不会丢失）
docker-compose -f docker-compose.prod.yml down
```

⚠️ **危险命令**:
```bash
# ❌ 这会删除所有数据库数据！
docker-compose -f docker-compose.prod.yml down -v
```

---

## 💾 数据管理

### 数据持久化说明

数据库数据存储在 Docker Volume 中

| 操作 | 数据是否保留 | 说明 |
|------|------------|------|
| `git pull` | ✅ 完全保留 | 更新代码不影响数据 |
| `docker-compose restart` | ✅ 完全保留 | 重启服务 |
| `docker-compose down` | ✅ 完全保留 | 停止容器，Volume 还在 |
| `docker-compose up` | ✅ 完全保留 | 重新启动 |
| `docker-compose down -v` | ❌ **全部删除** | 删除 Volume，慎用！ |

### 数据库备份

#### 手动备份

```bash
# 备份生产数据库
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U produser agentcard_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# 备份测试数据库
docker-compose -f docker-compose.test.yml exec -T db pg_dump -U testuser agentcard_test > backup_test_$(date +%Y%m%d_%H%M%S).sql
```

#### 自动备份（推荐）

**⚠️ 重要**: 生产环境必须配置自动备份！

**方法 1: 使用交互式配置脚本（最简单）**

```bash
./scripts/setup_cron.sh
```

按提示选择：
- 备份频率（推荐：每天凌晨 3 点）
- 备份环境（推荐：仅生产环境）

脚本会自动配置 crontab。

**方法 2: 手动配置 crontab**

```bash
# 创建日志目录
mkdir -p ~/projects/agent-source-db/logs

# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 3 点备份生产环境）
0 3 * * * /home/your_username/projects/agent-source-db/scripts/backup_database.sh prod >> /home/your_username/projects/agent-source-db/logs/backup.log 2>&1
```

**验证自动备份**:

```bash
# 查看 crontab 配置
crontab -l

# 查看备份日志
tail -f ~/projects/agent-source-db/logs/backup.log

# 检查 cron 服务状态
systemctl status cron
```

**备份特性**:
- ✅ 自动压缩（gzip）
- ✅ 自动清理旧备份（保留最近 7 个）
- ✅ 备份日志记录
- ✅ 错误自动通知

📖 **详细备份策略**: 参见 `docs/BACKUP_STRATEGY.md`

### 数据库恢复

```bash
# 从备份文件恢复
cat backup_20250109_020000.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U produser agentcard_prod
```

### 从生产环境复制数据到测试环境

```bash
# 1. 备份生产数据
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U produser agentcard_prod > prod_backup.sql

# 2. 恢复到测试环境
cat prod_backup.sql | docker-compose -f docker-compose.test.yml exec -T db psql -U testuser agentcard_test
```

---

## 📚 附录

### 快速命令参考

```bash
# === 测试环境 ===
docker-compose -f docker-compose.test.yml up -d       # 启动
docker-compose -f docker-compose.test.yml logs -f     # 查看日志
docker-compose -f docker-compose.test.yml restart     # 重启

# === 生产环境 ===
docker-compose -f docker-compose.prod.yml up -d       # 启动
docker-compose -f docker-compose.prod.yml logs -f     # 查看日志
docker-compose -f docker-compose.prod.yml restart     # 重启

# === 数据库管理 ===
./scripts/backup_database.sh prod                     # 备份生产数据
./scripts/backup_database.sh test                     # 备份测试数据
```

### 环境变量说明

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DJANGO_SECRET_KEY` | Django 密钥（必须保密） | 随机50字符 |
| `DJANGO_DEBUG` | 调试模式（生产必须False） | `True`/`False` |
| `DJANGO_ALLOWED_HOSTS` | 允许的主机名 | `192.168.1.100,localhost` |
| `POSTGRES_DB` | 数据库名 | `agentcard_prod` |
| `POSTGRES_USER` | 数据库用户 | `produser` |
| `POSTGRES_PASSWORD` | 数据库密码 | 强密码 |
