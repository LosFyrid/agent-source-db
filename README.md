# AgentCard 数据库管理系统

> 基于 Django 5.2.8 + Django REST Framework 的 A2A 协议 AgentCard 管理系统

[![Django Version](https://img.shields.io/badge/Django-5.2.8-green.svg)](https://www.djangoproject.com/)
[![Python Version](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![A2A Protocol](https://img.shields.io/badge/A2A%20Protocol-0.3.0-orange.svg)](https://a2a-protocol.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-blue.svg)](https://www.postgresql.org/)

---

## ✨ 特性

- ✅ **100% 符合 A2A 协议 0.3.0 规范** - 完整实现 AgentCard L1 标准字段 + L2 扩展机制
- ✅ **Django Admin 可视化管理界面** - 支持渐进式录入、实时验证、JSON 预览
- ✅ **REST API** - 分页、搜索、过滤、排序，支持可浏览 API
- ✅ **Schema Registry + Extensions 机制** - 可视化定义扩展数据结构，自动生成 JSON Schema
- ✅ **两层验证策略** - 数据库层宽松验证（支持草稿），输出层严格验证（确保 A2A 合规）
- ✅ **健康检查 + 日志监控** - 存活性/就绪性检查端点，结构化日志，Admin 监控面板

---

## 🚀 快速开始

### 前置要求

- Docker 和 Docker Compose
- Git

### 开发环境

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd agent-source-db

# 2. 创建环境配置
cp .env.dev.example .env.dev
# 编辑 .env.dev，根据需要修改配置

# 3. 启动服务
docker-compose up -d

# 4. 应用迁移
docker-compose exec web python manage.py migrate

# 5. 创建超级用户
docker-compose exec web python manage.py createsuperuser

# 6. 访问
# - Django Admin: http://localhost:8000/admin/
# - REST API: http://localhost:8000/api/
# - 系统监控: http://localhost:8000/admin/system-status/
# - 健康检查: http://localhost:8000/health/ready/
```

### 生产环境

详见 [部署指南](docs/DEPLOYMENT_GUIDE.md)

---

## 📚 文档

### 用户文档

- **[快速开始](docs/QUICKSTART.md)** - 5 分钟快速上手指南
- **[数据录入操作规范 (SOP)](docs/DATA_ENTRY_SOP.md)** - 数据录入人员操作手册（精简版）
- **[Admin 使用指南](docs/ADMIN_GUIDE.md)** - Django Admin 界面完整操作手册
- **[API 使用指南](docs/API-GUIDE.md)** - REST API 端点和使用示例
- **[系统功能说明](docs/SYSTEM_FEATURES.md)** - 完整功能清单和架构说明

### 运维文档

- **[部署指南](docs/DEPLOYMENT_GUIDE.md)** - 生产环境部署步骤
- **[Docker 环境说明](docs/DOCKER_ENVIRONMENTS.md)** - 开发/测试/生产环境配置
- **[监控方案](docs/MONITORING.md)** - MVP 级别运维监控设计
- **[监控快速指南](docs/MONITORING_QUICKSTART.md)** - 健康检查、日志、监控面板使用
- **[备份策略](docs/BACKUP_STRATEGY.md)** - 数据库备份和恢复方案

### 开发文档

- **[两层验证设计](docs/TWO_LAYER_VALIDATION.md)** - 数据验证策略详解
- **[原始数据导出](docs/RAW_EXPORT_GUIDE.md)** - to_dict_raw() vs to_agentcard_json()


---

## 🛠️ 技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| **Django** | 5.2.8 | Web 框架 + Auto-admin |
| **Django REST Framework** | 3.16.1 | REST API |
| **PostgreSQL** | 18 (alpine) | 关系型数据库 |
| **Gunicorn** | 23.0.0 | WSGI 服务器（生产） |
| **Python** | 3.11-slim | 运行时环境 |
| **Docker** | - | 容器化部署 |

---

## 📊 项目结构

```
agent-source-db/
├── core/                           # Django 核心配置
│   ├── settings.py                 # 配置文件（支持多环境）
│   ├── urls.py                     # 路由配置
│   └── wsgi.py                     # WSGI 入口
├── documents/                      # 主应用（AgentCard 管理）
│   ├── models.py                   # 数据模型（Namespace, AgentCard, SchemaRegistry）
│   ├── admin.py                    # Django Admin 配置
│   ├── views.py                    # DRF ViewSet
│   ├── serializers.py              # DRF 序列化器
│   ├── health.py                   # 健康检查端点
│   ├── admin_views.py              # Admin 监控面板
│   └── migrations/                 # 数据库迁移文件
├── docs/                           # 文档目录
├── logs/                           # 日志目录（自动轮转）
├── scripts/                        # 运维脚本
│   ├── deploy.sh                   # 一键部署脚本
│   ├── backup_database.sh          # 数据库备份
│   └── show_api_info.py            # 系统信息工具
├── docker-compose.yml              # 开发环境配置
├── docker-compose.prod.yml         # 生产环境配置
├── docker-compose.test.yml         # 测试环境配置
├── requirements.txt                # Python 依赖（uv根据.in自动生成）
├── requirements.in                 # Python 依赖（手动录入）
└── README.md                       # 项目说明（本文件）
```

---

## 🔌 API 端点

### 健康检查

| 端点 | 说明 |
|------|------|
| `GET /health/` | 存活性检查（Liveness） |
| `GET /health/ready/` | 就绪性检查（Readiness，含数据库检查） |
| `GET /health/db/` | 数据库详细状态 |

### REST API

| 端点 | 说明 |
|------|------|
| `GET /api/namespaces/` | 命名空间列表 |
| `GET /api/schemas/` | Schema 定义列表 |
| `GET /api/schemas/catalog/` | Schema 目录（发现机制） |
| `GET /api/agentcards/` | AgentCard 列表 |
| `GET /api/agentcards/{id}/standard_json/` | A2A 协议标准格式输出 |

完整 API 文档：[docs/API-GUIDE.md](docs/API-GUIDE.md)

---

## 🎯 核心概念

### Schema Registry

可视化定义 AgentCard 扩展数据结构：

- 支持 string, integer, number, boolean, object, array, enum, datetime 类型
- 自动生成 JSON Schema (draft-07)
- 自动验证扩展数据
- Schema 目录 API 用于服务发现

### 两层验证

- **数据库层**：宽松验证，允许渐进式录入（保存草稿）
- **输出层**：严格验证，确保 100% 符合 A2A 协议

详见：[docs/TWO_LAYER_VALIDATION.md](docs/TWO_LAYER_VALIDATION.md)

### Namespace

目前文档对namespace的描述集中于dev/prod/test，用作环境隔离，这是开发时的测试行为。具体namespace的定义遵循nacos文档所述。应当面向场景具体设计。

---

## 🔧 常用命令

```bash
# 查看日志
tail -f logs/django.log

# 进入 Django shell
docker-compose exec web python manage.py shell

# 创建迁移
docker-compose exec web python manage.py makemigrations

# 应用迁移
docker-compose exec web python manage.py migrate

# 收集静态文件
docker-compose exec web python manage.py collectstatic --noinput

# 查看系统信息
docker-compose exec web python scripts/show_api_info.py

# 备份数据库
./scripts/backup_database.sh
```

---

## 🐛 故障排查

### 健康检查返回 503

```bash
# 1. 检查数据库连接
docker-compose exec web python manage.py dbshell

# 2. 检查迁移状态
docker-compose exec web python manage.py showmigrations

# 3. 查看日志
docker-compose logs web
tail -f logs/error.log
```

### 无法访问 Admin

```bash
# 确认用户权限
docker-compose exec web python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='your_username')
>>> user.is_staff = True
>>> user.is_superuser = True
>>> user.save()
```

更多故障排查：[docs/MONITORING_QUICKSTART.md](docs/MONITORING_QUICKSTART.md#故障排查)

---

## 📈 监控

系统提供三层监控：

1. **健康检查端点** - 供 Kubernetes/负载均衡器使用
   - `/health/` - Liveness probe
   - `/health/ready/` - Readiness probe

2. **结构化日志** - 自动轮转，便于分析
   - `logs/django.log` - 所有日志
   - `logs/error.log` - 错误和警告
   - `logs/access.log` - HTTP 请求
   - `logs/db.log` - 慢查询

3. **Admin 监控面板** - 实时系统状态
   - http://localhost:8000/admin/system-status/
   - 数据库状态、响应时间
   - 数据统计、最近错误

详见：[docs/MONITORING.md](docs/MONITORING.md)

---

## 🔗 相关链接

- **A2A 协议规范**: https://a2a-protocol.org/
- **Django 文档**: https://docs.djangoproject.com/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **PostgreSQL 文档**: https://www.postgresql.org/docs/

---
