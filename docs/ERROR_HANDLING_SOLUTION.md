# 生产环境错误处理改进方案

## 问题现状

当前系统在生产环境（`DEBUG=False`）下：
- ❌ 任何错误都会导致白屏500错误
- ❌ 用户无法获取任何有用信息
- ❌ 用户无法继续使用系统
- ❌ 管理员难以快速定位问题

## 🎯 推荐方案（分阶段实施）

---

## 阶段1：最小改动方案（立即可实施，1-2小时）

### 目标
- 提供友好的错误页面
- 添加错误追踪ID
- 增强日志记录
- 允许用户返回系统继续操作

### 实施步骤

#### 1.1 创建自定义错误页面模板

**文件：`core/templates/500.html`**
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统错误 - AgentCard 管理系统</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .error-container {
            background: white;
            border-radius: 12px;
            padding: 40px;
            max-width: 600px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
        }
        .error-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        h1 {
            color: #333;
            margin: 0 0 10px 0;
            font-size: 32px;
        }
        .error-code {
            font-family: "Courier New", monospace;
            background: #f5f5f5;
            padding: 8px 12px;
            border-radius: 4px;
            display: inline-block;
            margin: 20px 0;
            font-size: 14px;
            color: #666;
        }
        p {
            color: #666;
            line-height: 1.6;
            margin: 15px 0;
        }
        .actions {
            margin-top: 30px;
            display: flex;
            gap: 15px;
            justify-content: center;
        }
        .btn {
            padding: 12px 24px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s;
            display: inline-block;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
        .btn-secondary {
            background: #f5f5f5;
            color: #333;
        }
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        .help-text {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 14px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">⚠️</div>
        <h1>系统遇到了一个错误</h1>
        <p>抱歉，系统在处理您的请求时遇到了问题。我们已经记录了这个错误，技术团队会尽快处理。</p>

        {% if error_id %}
        <div class="error-code">
            错误追踪ID: {{ error_id }}
        </div>
        <p style="font-size: 14px;">请在联系管理员时提供此追踪ID</p>
        {% endif %}

        <div class="actions">
            <a href="/" class="btn btn-primary">返回首页</a>
            <a href="javascript:history.back()" class="btn btn-secondary">返回上一页</a>
        </div>

        <div class="help-text">
            <p>如果问题持续出现，请联系系统管理员</p>
        </div>
    </div>
</body>
</html>
```

**文件：`core/templates/404.html`**
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>页面未找到 - AgentCard 管理系统</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .error-container {
            background: white;
            border-radius: 12px;
            padding: 40px;
            max-width: 600px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
        }
        .error-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        h1 {
            color: #333;
            margin: 0 0 10px 0;
            font-size: 32px;
        }
        .error-number {
            font-size: 80px;
            font-weight: bold;
            color: #667eea;
            margin: 20px 0;
        }
        p {
            color: #666;
            line-height: 1.6;
            margin: 15px 0;
        }
        .actions {
            margin-top: 30px;
            display: flex;
            gap: 15px;
            justify-content: center;
        }
        .btn {
            padding: 12px 24px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s;
            display: inline-block;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">🔍</div>
        <div class="error-number">404</div>
        <h1>页面未找到</h1>
        <p>您访问的页面不存在或已被移除。</p>

        <div class="actions">
            <a href="/" class="btn btn-primary">返回首页</a>
        </div>
    </div>
</body>
</html>
```

#### 1.2 创建自定义错误处理中间件

**文件：`core/middleware.py`**
```python
"""
自定义中间件：错误处理和追踪
"""
import uuid
import logging
import traceback
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings

logger = logging.getLogger(__name__)


class ErrorTrackingMiddleware:
    """
    错误追踪中间件

    功能：
    1. 捕获所有未处理的异常
    2. 生成唯一的错误追踪ID
    3. 记录详细的错误信息到日志
    4. 返回友好的错误页面（包含追踪ID）
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        处理未捕获的异常
        """
        # 生成唯一的错误追踪ID
        error_id = str(uuid.uuid4())[:8].upper()

        # 记录详细错误信息
        logger.error(
            f"[ERROR-{error_id}] Unhandled exception",
            extra={
                'error_id': error_id,
                'path': request.path,
                'method': request.method,
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'ip': self._get_client_ip(request),
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
            },
            exc_info=True  # 包含完整的堆栈追踪
        )

        # 根据请求类型返回不同的响应
        if request.path.startswith('/api/'):
            # API请求：返回JSON格式错误
            return JsonResponse({
                'error': 'Internal Server Error',
                'message': '服务器内部错误，请稍后重试',
                'error_id': error_id,
                'detail': str(exception) if settings.DEBUG else None
            }, status=500)
        else:
            # Web请求：返回HTML错误页面
            return render(request, '500.html', {
                'error_id': error_id,
            }, status=500)

    @staticmethod
    def _get_client_ip(request):
        """获取客户端真实IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

#### 1.3 更新settings.py配置

在 `core/settings.py` 中添加：

```python
# 1. 更新TEMPLATES配置，添加templates目录
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],  # 添加这行
        'APP_DIRS': True,
        ...
    },
]

# 2. 添加自定义中间件（在MIDDLEWARE列表中添加）
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.ErrorTrackingMiddleware',  # 添加这行
]

# 3. 生产环境配置
if not DEBUG:
    # 管理员邮箱（接收错误通知）
    ADMINS = [
        ('Admin', env('ADMIN_EMAIL', default='admin@example.com')),
    ]

    # 发送错误邮件（可选）
    # EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # EMAIL_HOST = env('EMAIL_HOST')
    # EMAIL_PORT = env.int('EMAIL_PORT', default=587)
    # EMAIL_USE_TLS = True
    # EMAIL_HOST_USER = env('EMAIL_HOST_USER')
    # EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
```

---

## 阶段2：增强方案（建议1-2天实施）

### 2.1 DRF异常处理器（API专用）

**文件：`core/exceptions.py`**
```python
"""
DRF自定义异常处理器
"""
import uuid
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    自定义DRF异常处理器

    返回统一格式的错误响应：
    {
        "error": "错误类型",
        "message": "用户友好的错误消息",
        "error_id": "追踪ID",
        "details": {...}  # 仅DEBUG模式
    }
    """
    # 调用DRF默认处理器
    response = exception_handler(exc, context)

    # 生成错误追踪ID
    error_id = str(uuid.uuid4())[:8].upper()

    # 记录错误
    request = context.get('request')
    logger.error(
        f"[API-ERROR-{error_id}] {type(exc).__name__}: {str(exc)}",
        extra={
            'error_id': error_id,
            'path': request.path if request else 'unknown',
            'method': request.method if request else 'unknown',
            'user': request.user.username if request and request.user.is_authenticated else 'anonymous',
        },
        exc_info=True
    )

    if response is not None:
        # DRF已处理的异常（400/403/404等）
        response.data = {
            'error': exc.__class__.__name__,
            'message': _get_user_friendly_message(exc),
            'error_id': error_id,
            'details': response.data
        }
    else:
        # 未处理的异常（500）
        response = Response({
            'error': 'InternalServerError',
            'message': '服务器内部错误，请稍后重试',
            'error_id': error_id,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response


def _get_user_friendly_message(exc):
    """
    将技术性错误消息转换为用户友好的消息
    """
    error_messages = {
        'ValidationError': '数据验证失败，请检查输入',
        'PermissionDenied': '您没有权限执行此操作',
        'NotAuthenticated': '请先登录',
        'NotFound': '请求的资源不存在',
        'MethodNotAllowed': '不支持此HTTP方法',
        'ParseError': '请求数据格式错误',
    }

    exc_name = exc.__class__.__name__
    return error_messages.get(exc_name, str(exc))
```

在 `settings.py` 中配置DRF异常处理器：
```python
REST_FRAMEWORK = {
    ...
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
}
```

### 2.2 Admin表单增强错误处理

**文件：`documents/admin.py`** - 在现有admin类中添加：

```python
from django.contrib import messages
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class SafeAdminMixin:
    """
    为Django Admin添加安全的错误处理
    """

    def save_model(self, request, obj, form, change):
        """重写save_model，添加错误处理"""
        try:
            with transaction.atomic():
                super().save_model(request, obj, form, change)
                self.message_user(
                    request,
                    f"{obj._meta.verbose_name} '{obj}' 保存成功",
                    messages.SUCCESS
                )
        except Exception as e:
            logger.exception(f"Admin save error: {type(e).__name__}")
            self.message_user(
                request,
                f"保存失败：{str(e)}",
                messages.ERROR
            )
            raise

    def delete_model(self, request, obj):
        """重写delete_model，添加错误处理"""
        try:
            obj_str = str(obj)
            super().delete_model(request, obj)
            self.message_user(
                request,
                f"{obj._meta.verbose_name} '{obj_str}' 删除成功",
                messages.SUCCESS
            )
        except Exception as e:
            logger.exception(f"Admin delete error: {type(e).__name__}")
            self.message_user(
                request,
                f"删除失败：{str(e)}",
                messages.ERROR
            )
            raise


# 在现有Admin类中继承此Mixin
class AgentCardAdmin(SafeAdminMixin, admin.ModelAdmin):
    ...
```

---

## 阶段3：专业方案（可选，建议使用Sentry）

### 3.1 Sentry集成（推荐生产环境使用）

#### 安装Sentry SDK
```bash
pip install sentry-sdk
# 或添加到 requirements.in
# sentry-sdk>=1.40.0
```

#### 配置Sentry
在 `settings.py` 中添加：

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if not DEBUG:
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),  # 从环境变量读取
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=0.1,  # 性能监控采样率
        send_default_pii=False,  # 不发送敏感信息
        environment=env('DJANGO_ENV', default='production'),
        release=env('APP_VERSION', default='unknown'),
    )
```

#### Sentry优势
- ✅ 实时错误监控和告警
- ✅ 完整的堆栈追踪和上下文信息
- ✅ 用户反馈收集
- ✅ 性能监控
- ✅ 错误趋势分析
- ✅ 自动错误分组和去重

---

## 📊 方案对比

| 方案 | 实施难度 | 时间成本 | 用户体验 | 运维价值 | 成本 |
|------|---------|---------|---------|---------|------|
| 阶段1：自定义错误页面 | ⭐ 简单 | 1-2小时 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 免费 |
| 阶段2：增强错误处理 | ⭐⭐ 中等 | 1-2天 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 免费 |
| 阶段3：Sentry集成 | ⭐⭐⭐ 较难 | 0.5天 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 免费/付费 |

---

## 🚀 实施建议

### 立即实施（今天）
1. ✅ 创建自定义500/404错误页面
2. ✅ 添加ErrorTrackingMiddleware
3. ✅ 更新settings.py配置

### 本周内实施
1. ✅ DRF异常处理器
2. ✅ Admin错误处理增强

### 长期计划
1. 考虑Sentry集成（尤其是生产环境）
2. 建立错误监控Dashboard
3. 定期审查错误日志

---

## 📝 测试检查清单

部署后需要测试的场景：

- [ ] 访问不存在的页面（404）
- [ ] 提交无效的表单数据（ValidationError）
- [ ] 删除有依赖关系的对象（IntegrityError）
- [ ] API请求返回的错误格式
- [ ] 错误追踪ID是否正确记录到日志
- [ ] 用户能否从错误页面返回继续使用系统

---

## 🔍 日志查看命令

查看错误日志：
```bash
# 查看错误日志
docker-compose exec web tail -f logs/error.log

# 搜索特定错误ID
docker-compose exec web grep "ERROR-A1B2C3D4" logs/error.log

# 查看最近的500错误
docker-compose exec web tail -100 logs/error.log | grep "500"
```

---

## 📧 环境变量配置示例

在 `.env.prod` 中添加：

```env
# 错误处理配置
ADMIN_EMAIL=admin@your-domain.com

# Sentry配置（可选）
# SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
# APP_VERSION=v1.0.0
# DJANGO_ENV=production
```

---

这个方案能够：
1. ✅ 提供友好的错误页面，不再白屏
2. ✅ 用户可以返回继续使用系统
3. ✅ 每个错误都有追踪ID，方便定位
4. ✅ 详细的错误日志记录
5. ✅ API和Web分别处理
6. ✅ 零成本（不使用Sentry的话）
