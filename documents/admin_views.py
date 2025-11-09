"""
Admin 监控视图

提供系统状态监控页面，显示：
- 数据库状态
- 数据统计
- 最近错误日志
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db import connection
from django.utils import timezone
import os
import time

from documents.models import AgentCard, Namespace, SchemaRegistry


@staff_member_required
def system_status(request):
    """
    系统状态监控页面

    需要 staff 权限才能访问
    """

    # 数据库状态
    db_status = check_database_status()

    # 数据统计
    stats = {
        'agentcard_total': AgentCard.objects.count(),
        'agentcard_active': AgentCard.objects.filter(is_active=True).count(),
        'namespace_count': Namespace.objects.count(),
        'namespace_active': Namespace.objects.filter(is_active=True).count(),
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
    """
    检查数据库状态

    返回：
        dict: 包含数据库状态信息
    """
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
        latency = (time.time() - start) * 1000

        # 简化版本号显示
        version_simple = version.split(',')[0].split('(')[0].strip()

        return {
            'status': 'ok',
            'vendor': connection.vendor,
            'version': version_simple,
            'latency_ms': round(latency, 2)
        }
    except Exception as e:
        return {
            'status': 'error',
            'vendor': connection.vendor,
            'error': str(e),
            'latency_ms': None
        }


def read_recent_errors(limit=50):
    """
    读取最近的错误日志

    Args:
        limit: 最多读取的行数

    Returns:
        list: 错误日志列表（最新的在前面）
    """
    errors = []
    error_log_path = 'logs/error.log'

    if not os.path.exists(error_log_path):
        return ['日志文件尚不存在（系统首次运行或未发生错误）']

    try:
        with open(error_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

            # 如果文件为空
            if not lines:
                return ['暂无错误日志']

            # 读取最后 N 行
            recent_lines = lines[-limit:] if len(lines) > limit else lines

            # 反转顺序（最新的在前面）
            for line in reversed(recent_lines):
                line = line.strip()
                if line:  # 跳过空行
                    errors.append(line)

        if not errors:
            return ['暂无错误日志']

        return errors

    except Exception as e:
        return [f'无法读取错误日志: {e}']
