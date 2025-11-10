#!/bin/bash
set -e

echo "==> Entrypoint: Starting..."

# 检查 staticfiles 目录是否为空（或只有 .gitkeep 等隐藏文件）
if [ -z "$(ls -A /app/staticfiles 2>/dev/null | grep -v '^\.')" ]; then
    echo "==> Staticfiles directory is empty, collecting static files..."
    python manage.py collectstatic --noinput --clear
    echo "==> Static files collected successfully"
else
    echo "==> Static files already exist, skipping collection"
fi

echo "==> Entrypoint: Executing command: $@"

# 执行传入的命令（例如 gunicorn）
exec "$@"
