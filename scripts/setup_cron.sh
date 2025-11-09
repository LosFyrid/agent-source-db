#!/bin/bash

# ============================================================
# 设置自动备份 Cron 任务
# ============================================================
# 使用方法: ./scripts/setup_cron.sh
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}AgentCard 自动备份配置${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# 获取项目绝对路径
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_SCRIPT="${PROJECT_DIR}/scripts/backup_database.sh"

echo "项目目录: $PROJECT_DIR"
echo "备份脚本: $BACKUP_SCRIPT"
echo ""

# 检查脚本是否存在
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo -e "${RED}错误: 备份脚本不存在${NC}"
    exit 1
fi

# 确保脚本有执行权限
chmod +x "$BACKUP_SCRIPT"

echo -e "${YELLOW}请选择备份频率:${NC}"
echo "1) 每天凌晨 3 点（推荐）"
echo "2) 每周日凌晨 2 点"
echo "3) 每天凌晨 2 点"
echo "4) 自定义"
echo ""
read -p "请输入选项 (1-4): " CHOICE

case $CHOICE in
    1)
        CRON_SCHEDULE="0 3 * * *"
        SCHEDULE_DESC="每天凌晨 3 点"
        ;;
    2)
        CRON_SCHEDULE="0 2 * * 0"
        SCHEDULE_DESC="每周日凌晨 2 点"
        ;;
    3)
        CRON_SCHEDULE="0 2 * * *"
        SCHEDULE_DESC="每天凌晨 2 点"
        ;;
    4)
        echo ""
        echo "Cron 格式: 分 时 日 月 周"
        echo "示例: 0 3 * * * (每天凌晨 3 点)"
        read -p "请输入 Cron 表达式: " CRON_SCHEDULE
        SCHEDULE_DESC="自定义: $CRON_SCHEDULE"
        ;;
    *)
        echo -e "${RED}无效的选项${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}请选择备份环境:${NC}"
echo "1) 仅生产环境（推荐）"
echo "2) 仅测试环境"
echo "3) 生产和测试环境都备份"
echo ""
read -p "请输入选项 (1-3): " ENV_CHOICE

case $ENV_CHOICE in
    1)
        CRON_COMMAND="$CRON_SCHEDULE $BACKUP_SCRIPT prod >> ${PROJECT_DIR}/logs/backup.log 2>&1"
        ENV_DESC="仅生产环境"
        ;;
    2)
        CRON_COMMAND="$CRON_SCHEDULE $BACKUP_SCRIPT test >> ${PROJECT_DIR}/logs/backup.log 2>&1"
        ENV_DESC="仅测试环境"
        ;;
    3)
        CRON_COMMAND_PROD="$CRON_SCHEDULE $BACKUP_SCRIPT prod >> ${PROJECT_DIR}/logs/backup.log 2>&1"
        CRON_COMMAND_TEST="$CRON_SCHEDULE $BACKUP_SCRIPT test >> ${PROJECT_DIR}/logs/backup.log 2>&1"
        ENV_DESC="生产和测试环境"
        ;;
    *)
        echo -e "${RED}无效的选项${NC}"
        exit 1
        ;;
esac

# 创建日志目录
mkdir -p "${PROJECT_DIR}/logs"

echo ""
echo -e "${YELLOW}============================================================${NC}"
echo "备份配置摘要:"
echo "  频率: $SCHEDULE_DESC"
echo "  环境: $ENV_DESC"
echo "  日志: ${PROJECT_DIR}/logs/backup.log"
echo -e "${YELLOW}============================================================${NC}"
echo ""

read -p "确认添加到 crontab? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "操作已取消"
    exit 0
fi

# 备份当前 crontab
crontab -l > /tmp/crontab_backup_$$.txt 2>/dev/null || true

# 添加新的 cron 任务
if [ "$ENV_CHOICE" == "3" ]; then
    # 生产和测试环境
    (crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT"; echo "$CRON_COMMAND_PROD"; echo "$CRON_COMMAND_TEST") | crontab -
else
    # 单个环境
    (crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT"; echo "$CRON_COMMAND") | crontab -
fi

echo ""
echo -e "${GREEN}✓ Cron 任务已添加！${NC}"
echo ""
echo "当前 crontab 配置:"
echo -e "${BLUE}------------------------------------------------------------${NC}"
crontab -l | grep "$BACKUP_SCRIPT"
echo -e "${BLUE}------------------------------------------------------------${NC}"
echo ""
echo "提示:"
echo "  - 查看 crontab: crontab -l"
echo "  - 编辑 crontab: crontab -e"
echo "  - 删除 crontab: crontab -r"
echo "  - 查看备份日志: tail -f ${PROJECT_DIR}/logs/backup.log"
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}配置完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
