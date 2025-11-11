"""
自定义中间件：错误处理和追踪
"""
import uuid
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings

logger = logging.getLogger('documents')  # 使用documents logger确保输出到正确的日志文件


class ErrorTrackingMiddleware:
    """
    错误追踪中间件

    功能：
    1. 捕获所有未处理的异常
    2. 生成唯一的错误追踪ID
    3. 记录详细的错误信息到日志文件
    4. 返回友好的错误页面（包含追踪ID）
    5. 在HTTP响应头中添加 X-Error-ID 便于追踪

    行为：
    - API请求（/api/*）：返回JSON格式的错误响应
    - 普通Web请求：显示友好的自定义错误页面（500.html）
    - 所有错误都记录到 logs/error.log 文件中，格式为 [ERROR-XXXXXXXX]
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        处理未捕获的异常

        注意：此方法在任何未处理的异常时都会被调用，包括：
        - 500 Internal Server Error
        - ValidationError (如果未在视图中捕获)
        - 其他未处理的异常
        """
        # 生成唯一的错误追踪ID
        error_id = str(uuid.uuid4())[:8].upper()

        # 记录详细错误信息（始终记录，无论DEBUG状态）
        logger.error(
            f"[ERROR-{error_id}] Unhandled exception: {type(exception).__name__}",
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
            response = JsonResponse({
                'error': 'Internal Server Error',
                'message': '服务器内部错误，请稍后重试',
                'error_id': error_id,
                'detail': str(exception) if settings.DEBUG else None
            }, status=500)
            response['X-Error-ID'] = error_id
            return response

        # Web请求：返回友好的错误页面
        response = render(request, '500.html', {
            'error_id': error_id,
        }, status=500)
        response['X-Error-ID'] = error_id
        return response

    @staticmethod
    def _get_client_ip(request):
        """获取客户端真实IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
