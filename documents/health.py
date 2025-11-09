"""
健康检查端点

提供三个级别的健康检查：
1. /health/ - 存活性检查（Liveness）
2. /health/ready/ - 就绪性检查（Readiness）
3. /health/db/ - 数据库详细检查
"""

from django.http import JsonResponse
from django.db import connection
from django.utils import timezone
import time


def health_liveness(request):
    """
    存活性检查 - 最简单的检查

    用途：判断应用是否还活着，是否需要重启
    检查项：Django 进程是否响应

    返回：
        200 OK - 服务正常
    """
    return JsonResponse({
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'service': 'agent-source-db',
        'version': '1.0.0'
    })


def health_readiness(request):
    """
    就绪性检查 - 检查关键依赖

    用途：判断应用是否准备好接收流量
    检查项：
    - 数据库连接正常
    - 迁移已应用

    返回：
        200 OK - 准备就绪
        503 Service Unavailable - 未就绪
    """
    checks = {}
    overall_status = 'ready'

    # 检查数据库连接
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

        unapplied_count = len(plan)
        checks['migrations'] = {
            'status': 'ok' if unapplied_count == 0 else 'warning',
            'unapplied': unapplied_count
        }

        if unapplied_count > 0:
            overall_status = 'not_ready'
    except Exception as e:
        checks['migrations'] = {
            'status': 'error',
            'error': str(e)
        }
        overall_status = 'not_ready'

    status_code = 200 if overall_status == 'ready' else 503

    return JsonResponse({
        'status': overall_status,
        'timestamp': timezone.now().isoformat(),
        'checks': checks
    }, status=status_code)


def health_database(request):
    """
    数据库详细检查

    返回数据库连接状态、版本、响应时间等详细信息

    返回：
        200 OK - 数据库正常
        503 Service Unavailable - 数据库异常
    """
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
        latency = (time.time() - start) * 1000

        # 简化 PostgreSQL 版本号显示
        # 例如: "PostgreSQL 18.0 (Debian 18.0-1.pgdg120+1)" -> "PostgreSQL 18.0"
        version_simple = version.split(',')[0].split('(')[0].strip()

        return JsonResponse({
            'status': 'ok',
            'database': {
                'vendor': connection.vendor,
                'version': version_simple,
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
