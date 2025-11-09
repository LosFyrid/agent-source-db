# 运维监控方案（MVP）

**版本**: 1.0
**更新日期**: 2025-11-09
**目标**: 提供基础但完整的生产环境监控能力

---

## 设计原则

1. **简单实用** - 只包含关键功能，避免过度设计
2. **渐进式** - 从最基本的功能开始，可逐步扩展
3. **低成本** - 优先使用免费/开源工具
4. **容器友好** - 与 Docker 环境无缝集成
5. **可观测性三支柱** - 日志、指标、追踪（MVP阶段专注前两者）

---

## 监控架构

```
┌─────────────────────────────────────────────────────┐
│                  访问入口                            │
│  Nginx (反向代理 + 静态文件) :80/:443                │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              Django 应用层                           │
│  ┌─────────────────────────────────────────┐        │
│  │  健康检查端点                            │        │
│  │  • /health/        - 存活性检查          │        │
│  │  • /health/ready/  - 就绪性检查          │        │
│  │  • /health/db/     - 数据库连接检查      │        │
│  └─────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────┐        │
│  │  结构化日志 (django-structlog)          │        │
│  │  • 请求日志 (access log)                │        │
│  │  • 应用日志 (app log)                   │        │
│  │  • 错误日志 (error log)                 │        │
│  └─────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────┐        │
│  │  Admin 监控面板                          │        │
│  │  • 系统状态概览                          │        │
│  │  • 近期错误日志                          │        │
│  │  • 数据库统计                            │        │
│  └─────────────────────────────────────────┘        │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
┌────────▼────────┐  ┌───────▼────────┐
│  PostgreSQL     │  │  Sentry (可选)  │
│  健康检查       │  │  错误追踪       │
└─────────────────┘  └────────────────┘

日志文件 → /app/logs/
  ├── django.log          (所有日志)
  ├── access.log          (访问日志)
  ├── error.log           (错误日志)
  └── db.log              (数据库慢查询)
```

---

## 核心组件

### 1. 健康检查端点 (Health Checks)

**目的**: 让负载均衡器、监控系统、k8s 等快速判断服务状态

#### 1.1 `/health/` - 存活性检查 (Liveness)

**用途**: 判断应用是否还活着，是否需要重启

**检查项**:
- Django 进程是否响应
- 基本的内存可用性

**响应**:
```json
{
  "status": "ok",
  "timestamp": "2025-11-09T12:34:56Z",
  "service": "agent-source-db",
  "version": "1.0.0"
}
```

**HTTP 状态码**:
- `200 OK` - 服务正常
- `503 Service Unavailable` - 服务异常

---

#### 1.2 `/health/ready/` - 就绪性检查 (Readiness)

**用途**: 判断应用是否准备好接收流量

**检查项**:
- ✅ 数据库连接正常
- ✅ 必要的外部依赖可用
- ✅ 应用初始化完成

**响应**:
```json
{
  "status": "ready",
  "timestamp": "2025-11-09T12:34:56Z",
  "checks": {
    "database": {
      "status": "ok",
      "latency_ms": 5.2
    },
    "migrations": {
      "status": "ok",
      "unapplied": 0
    }
  }
}
```

**HTTP 状态码**:
- `200 OK` - 准备就绪
- `503 Service Unavailable` - 未就绪（不要发送流量）

---

#### 1.3 `/health/db/` - 数据库健康检查

**用途**: 独立检查数据库连接状态

**检查项**:
- 数据库连接是否正常
- 查询响应时间
- 连接池状态

**响应**:
```json
{
  "status": "ok",
  "database": {
    "vendor": "postgresql",
    "version": "18.0",
    "connection": "ok",
    "latency_ms": 3.8,
    "pool": {
      "active": 2,
      "idle": 3,
      "max": 20
    }
  }
}
```

---

### 2. 结构化日志 (Structured Logging)

**目的**: 便于日志查询、分析和告警

#### 2.1 日志格式

**采用 JSON 格式**，便于机器解析和后续集成 ELK/Loki 等工具：

```json
{
  "timestamp": "2025-11-09T12:34:56.789Z",
  "level": "INFO",
  "logger": "django.request",
  "message": "GET /api/agentcards/ 200",
  "request_id": "abc123",
  "user": "admin",
  "ip": "192.168.1.100",
  "method": "GET",
  "path": "/api/agentcards/",
  "status": 200,
  "duration_ms": 45.2,
  "user_agent": "curl/7.68.0"
}
```

#### 2.2 日志分类

| 日志文件 | 级别 | 内容 | 用途 |
|---------|------|------|------|
| `django.log` | ALL | 所有日志 | 完整记录 |
| `access.log` | INFO | HTTP 请求日志 | 流量分析 |
| `error.log` | WARNING+ | 错误和警告 | 快速定位问题 |
| `db.log` | WARNING+ | 慢查询（>100ms） | 性能优化 |

#### 2.3 日志轮转

使用 Python `logging.handlers.RotatingFileHandler`：
- 单文件最大 50MB
- 保留最近 10 个文件
- 总容量 ~500MB

---

### 3. Admin 监控面板

**目的**: 给运维人员提供快速查看系统状态的界面

#### 3.1 系统状态页面 `/admin/system-status/`

**显示内容**:
- ✅ 服务运行时间 (uptime)
- ✅ 数据库连接状态
- ✅ 数据统计（AgentCard 总数、Namespace 数量等）
- ✅ 最近 50 条错误日志
- ✅ 最近 24 小时请求统计

**示例截图**:
```
┌─────────────────────────────────────────────┐
│  系统状态监控                                │
├─────────────────────────────────────────────┤
│  运行时间: 15 天 3 小时 42 分钟              │
│  数据库: PostgreSQL 18.0 ✓ (3.2ms)          │
│  应用版本: 1.0.0                             │
├─────────────────────────────────────────────┤
│  数据统计:                                   │
│    AgentCard:     127 个 (活跃: 98)         │
│    Namespace:     5 个                       │
│    Schema:        12 个                      │
├─────────────────────────────────────────────┤
│  最近 24 小时:                               │
│    总请求数:      5,234                      │
│    错误请求:      12 (0.2%)                  │
│    平均响应时间:  45ms                       │
├─────────────────────────────────────────────┤
│  最近错误 (点击查看详情):                    │
│  [ERROR] 2025-11-09 12:30 - ValidationError │
│  [WARNING] 2025-11-09 11:45 - Slow query    │
└─────────────────────────────────────────────┘
```

---

### 4. 错误追踪 (可选: Sentry)

**目的**: 自动捕获、聚合、通知错误

**为什么选 Sentry**:
- ✅ 免费层支持 5,000 事件/月（MVP 足够）
- ✅ 集成简单（1 个配置 + 1 行代码）
- ✅ 自动捕获异常、慢查询、性能问题
- ✅ 提供邮件/Slack 通知

**配置成本**: < 10 分钟

---

## 实施步骤

### 步骤 1: 添加健康检查端点

**创建 `documents/health.py`**:

```python
from django.http import JsonResponse
from django.db import connection
from django.core.management import call_command
from django.utils import timezone
import time

def health_liveness(request):
    """存活性检查 - 最简单的检查"""
    return JsonResponse({
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'service': 'agent-source-db',
        'version': '1.0.0'
    })

def health_readiness(request):
    """就绪性检查 - 检查关键依赖"""
    checks = {}
    overall_status = 'ready'

    # 检查数据库
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        latency = (time.time() - start) * 1000

        checks['database'] = {
            'status': 'ok',
            'latency_ms': round(latency, 2)
        }
    except Exception as e:
        checks['database'] = {
            'status': 'error',
            'error': str(e)
        }
        overall_status = 'not_ready'

    # 检查迁移状态
    try:
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

        checks['migrations'] = {
            'status': 'ok',
            'unapplied': len(plan)
        }

        if len(plan) > 0:
            overall_status = 'not_ready'
            checks['migrations']['status'] = 'warning'
    except Exception as e:
        checks['migrations'] = {
            'status': 'error',
            'error': str(e)
        }

    status_code = 200 if overall_status == 'ready' else 503

    return JsonResponse({
        'status': overall_status,
        'timestamp': timezone.now().isoformat(),
        'checks': checks
    }, status=status_code)

def health_database(request):
    """数据库详细检查"""
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
        latency = (time.time() - start) * 1000

        return JsonResponse({
            'status': 'ok',
            'database': {
                'vendor': connection.vendor,
                'version': version,
                'connection': 'ok',
                'latency_ms': round(latency, 2)
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'database': {
                'connection': 'failed',
                'error': str(e)
            }
        }, status=503)
```

**添加 URL 路由** (`core/urls.py`):

```python
from documents.health import health_liveness, health_readiness, health_database

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('documents.urls')),

    # 健康检查端点
    path('health/', health_liveness, name='health-liveness'),
    path('health/ready/', health_readiness, name='health-readiness'),
    path('health/db/', health_database, name='health-database'),
]
```

---

### 步骤 2: 配置结构化日志

**更新 `core/settings.py`**:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 日志目录
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '%(message)s',  # 将在 handler 中处理 JSON 格式
        },
        'simple': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_all': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'file_error': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'error.log',
            'maxBytes': 50 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'json',
        },
        'file_access': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'access.log',
            'maxBytes': 50 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'json',
        },
        'file_db': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'db.log',
            'maxBytes': 50 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_all', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file_access', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['file_db'],
            'level': 'WARNING',  # 只记录慢查询和错误
            'propagate': False,
        },
        'documents': {
            'handlers': ['console', 'file_all', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file_all'],
        'level': 'INFO',
    },
}

# 慢查询阈值（秒）
# 超过此时间的查询会被记录到 db.log
DATABASE_SLOW_QUERY_THRESHOLD = 0.1  # 100ms
```

---

### 步骤 3: 创建 Admin 监控面板

**创建 `documents/admin_views.py`**:

```python
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db import connection
from django.utils import timezone
from datetime import timedelta
import os

from documents.models import AgentCard, Namespace, SchemaRegistry

@staff_member_required
def system_status(request):
    """系统状态监控页面"""

    # 数据库状态
    db_status = check_database_status()

    # 数据统计
    stats = {
        'agentcard_total': AgentCard.objects.count(),
        'agentcard_active': AgentCard.objects.filter(is_active=True).count(),
        'namespace_count': Namespace.objects.count(),
        'schema_count': SchemaRegistry.objects.filter(is_active=True).count(),
    }

    # 读取最近错误日志
    recent_errors = read_recent_errors(limit=50)

    context = {
        'title': '系统状态监控',
        'db_status': db_status,
        'stats': stats,
        'recent_errors': recent_errors,
        'check_time': timezone.now(),
    }

    return render(request, 'admin/system_status.html', context)

def check_database_status():
    """检查数据库状态"""
    import time
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
        latency = (time.time() - start) * 1000

        return {
            'status': 'ok',
            'vendor': connection.vendor,
            'version': version.split(',')[0],  # 简化版本号
            'latency_ms': round(latency, 2)
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def read_recent_errors(limit=50):
    """读取最近的错误日志"""
    errors = []
    error_log_path = 'logs/error.log'

    if not os.path.exists(error_log_path):
        return errors

    try:
        with open(error_log_path, 'r') as f:
            lines = f.readlines()
            # 读取最后 N 行
            for line in lines[-limit:]:
                errors.append(line.strip())
    except Exception as e:
        errors.append(f"无法读取错误日志: {e}")

    return reversed(errors)  # 最新的在前面
```

**创建模板 `documents/templates/admin/system_status.html`**:

```html
{% extends "admin/base_site.html" %}
{% load static %}

{% block title %}{{ title }}{% endblock %}

{% block content %}
<h1>{{ title }}</h1>

<div class="module" style="margin-bottom: 20px;">
    <h2>数据库状态</h2>
    <table>
        <tr>
            <th style="width: 200px;">状态</th>
            <td>
                {% if db_status.status == 'ok' %}
                    <span style="color: green;">✓ 正常</span>
                {% else %}
                    <span style="color: red;">✗ 异常</span>
                {% endif %}
            </td>
        </tr>
        <tr>
            <th>数据库</th>
            <td>{{ db_status.vendor|upper }} {{ db_status.version }}</td>
        </tr>
        <tr>
            <th>响应时间</th>
            <td>{{ db_status.latency_ms }} ms</td>
        </tr>
    </table>
</div>

<div class="module" style="margin-bottom: 20px;">
    <h2>数据统计</h2>
    <table>
        <tr>
            <th style="width: 200px;">AgentCard 总数</th>
            <td>{{ stats.agentcard_total }} 个</td>
        </tr>
        <tr>
            <th>AgentCard 活跃数</th>
            <td>{{ stats.agentcard_active }} 个</td>
        </tr>
        <tr>
            <th>Namespace</th>
            <td>{{ stats.namespace_count }} 个</td>
        </tr>
        <tr>
            <th>Schema</th>
            <td>{{ stats.schema_count }} 个</td>
        </tr>
    </table>
</div>

<div class="module">
    <h2>最近错误日志 (最近 50 条)</h2>
    <pre style="max-height: 400px; overflow-y: auto; background: #f8f8f8; padding: 10px; font-size: 12px;">{% for error in recent_errors %}{{ error }}
{% empty %}暂无错误日志{% endfor %}</pre>
</div>

<p style="margin-top: 20px; color: #666;">
    检查时间: {{ check_time|date:"Y-m-d H:i:s" }}
</p>
{% endblock %}
```

**注册 URL** (`core/urls.py`):

```python
from documents.admin_views import system_status

urlpatterns = [
    path('admin/system-status/', system_status, name='admin-system-status'),
    # ...
]
```

---

### 步骤 4: Docker Compose 配置

**更新 `docker-compose.prod.yml`**，添加日志卷：

```yaml
services:
  web:
    volumes:
      - .:/app
      - ./logs:/app/logs  # 日志目录持久化
      - static_volume:/app/staticfiles
      - media_volume:/app/media

    environment:
      - DJANGO_LOG_LEVEL=INFO  # 可通过环境变量控制
```

**添加 `.dockerignore` 排除日志**:

```
logs/
*.log
```

---

### 步骤 5: Nginx 配置（健康检查和日志）

**`nginx.conf`** (新建):

```nginx
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name _;

    # 访问日志
    access_log /var/log/nginx/access.log combined;
    error_log /var/log/nginx/error.log warn;

    # 健康检查端点（不记录日志）
    location /health/ {
        access_log off;
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 静态文件
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
    }

    # 媒体文件
    location /media/ {
        alias /app/media/;
        expires 7d;
    }

    # API 和 Admin
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

### 步骤 6: (可选) 集成 Sentry

**安装依赖**:

```bash
# 添加到 requirements.in
sentry-sdk[django]>=2.0.0
```

**配置 `settings.py`**:

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Sentry 配置（仅生产环境）
if not DEBUG and env.str('SENTRY_DSN', default=''):
    sentry_sdk.init(
        dsn=env.str('SENTRY_DSN'),
        integrations=[DjangoIntegration()],

        # 性能监控（可选）
        traces_sample_rate=0.1,  # 10% 的请求

        # 环境标识
        environment=env.str('DJANGO_ENV', default='production'),

        # 发送前过滤敏感信息
        send_default_pii=False,
    )
```

**环境变量** (`.env.prod`):

```bash
# Sentry (可选)
SENTRY_DSN=https://xxx@sentry.io/yyy
```

---

## 使用指南

### 本地开发环境测试

```bash
# 1. 启动服务
docker-compose up -d

# 2. 测试健康检查
curl http://localhost:8000/health/
curl http://localhost:8000/health/ready/
curl http://localhost:8000/health/db/

# 3. 查看日志
tail -f logs/django.log
tail -f logs/error.log

# 4. 访问监控面板
# http://localhost:8000/admin/system-status/
```

---

### 生产环境部署

```bash
# 1. 确保日志目录存在
mkdir -p logs

# 2. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 3. 配置外部监控（可选）
# - UptimeRobot (免费) 监控 /health/ready/
# - 设置告警邮件/Slack
```

---

## 监控策略

### 主动监控

| 监控项 | 检查间隔 | 告警条件 |
|--------|---------|---------|
| `/health/ready/` | 1分钟 | 连续2次失败 |
| 磁盘空间 | 5分钟 | > 80% |
| 日志错误率 | 5分钟 | > 5% |
| 响应时间 | 1分钟 | P95 > 1000ms |

### 被动监控

- Sentry 自动捕获异常
- 管理员定期查看 Admin 监控面板
- 查看日志文件

---

## 扩展路径

当需要更强大的监控能力时，可以渐进式添加：

### 阶段 2: 指标收集

- **Prometheus + Grafana** - 时序数据库 + 可视化
- **django-prometheus** - 导出 Django 指标
- 指标类型：请求速率、响应时间、错误率、数据库查询性能

### 阶段 3: 日志聚合

- **ELK Stack** (Elasticsearch + Logstash + Kibana)
- 或 **Loki + Grafana** (更轻量)
- 支持日志全文搜索、聚合分析、可视化

### 阶段 4: 分布式追踪

- **Jaeger** 或 **Zipkin**
- 追踪跨服务的请求链路
- 分析性能瓶颈

### 阶段 5: 告警系统

- **Alertmanager** (Prometheus 生态)
- 多渠道通知（邮件、Slack、PagerDuty）
- 告警聚合和去重

---

## 成本估算

### MVP 阶段（免费）

- ✅ 健康检查端点 - 0 成本
- ✅ 结构化日志 - 0 成本
- ✅ Admin 监控面板 - 0 成本
- ✅ Sentry 免费层 - 0 成本（5,000 事件/月）
- ✅ UptimeRobot 免费层 - 0 成本（50 个监控器）

**总成本: $0/月**

### 扩展阶段

- Prometheus + Grafana（自托管）- 服务器成本
- ELK Stack（自托管）- 服务器成本（内存需求较高）
- Sentry 付费版 - $26/月起（50,000 事件）

---

## 总结

这个 MVP 监控方案提供了：

✅ **健康检查** - 让外部系统知道服务状态
✅ **结构化日志** - 便于问题排查和分析
✅ **Admin 面板** - 快速查看系统概况
✅ **错误追踪** - 自动捕获和聚合异常
✅ **可扩展性** - 可平滑升级到 Prometheus/ELK

**实施时间**: 约 2-4 小时
**维护成本**: 极低（主要是定期查看日志）
**扩展难度**: 简单（增量添加组件）

---

**下一步**: 先实施步骤 1-3（健康检查 + 日志 + Admin 面板），验证可用后再考虑 Sentry。
