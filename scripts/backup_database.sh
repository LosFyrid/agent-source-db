#!/bin/bash

# ============================================================
# AgentCard 数据库备份脚本
# ============================================================
# 使用方法:
#   ./scripts/backup_database.sh prod  # 备份生产环境
#   ./scripts/backup_database.sh test  # 备份测试环境
# ============================================================

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查参数
if [ $# -eq 0 ]; then
    echo -e "${RED}错误: 请指定环境${NC}"
    echo "使用方法: $0 [prod|test]"
    exit 1
fi

ENV=$1

# 根据环境设置变量
if [ "$ENV" == "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    DB_NAME="agentcard_prod"
    DB_USER="produser"
    BACKUP_DIR="backups/prod"
elif [ "$ENV" == "test" ]; then
    COMPOSE_FILE="docker-compose.test.yml"
    DB_NAME="agentcard_test"
    DB_USER="testuser"
    BACKUP_DIR="backups/test"
else
    echo -e "${RED}错误: ��效的环境参数 '$ENV'${NC}"
    echo "有效参数: prod, test"
    exit 1
fi

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 生成备份文件名（带时间戳）
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${ENV}_${TIMESTAMP}.sql"

echo -e "${YELLOW}============================================================${NC}"
echo -e "${YELLOW}AgentCard 数据库备份${NC}"
echo -e "${YELLOW}============================================================${NC}"
echo "环境: $ENV"
echo "数据库: $DB_NAME"
echo "备份文件: $BACKUP_FILE"
echo -e "${YELLOW}============================================================${NC}"
echo ""

# 执行备份
echo -e "${GREEN}开始备份...${NC}"
docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"

# 检查备份是否成功
if [ $? -eq 0 ]; then
    # 获取文件大小
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ 备份成功！${NC}"
    echo "文件: $BACKUP_FILE"
    echo "大小: $SIZE"
    
    # 压缩备份文件（可选）
    echo ""
    echo -e "${YELLOW}压缩备份文件...${NC}"
    gzip "$BACKUP_FILE"
    COMPRESSED_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    echo -e "${GREEN}✓ 压缩完成！${NC}"
    echo "压缩文件: ${BACKUP_FILE}.gz"
    echo "压缩后大小: $COMPRESSED_SIZE"
    
    # 清理旧备份（保留最近7个）
    echo ""
    echo -e "${YELLOW}清理旧备份（保留最近7个）...${NC}"
    cd "$BACKUP_DIR"
    ls -t backup_${ENV}_*.sql.gz 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null || true
    REMAINING=$(ls -1 backup_${ENV}_*.sql.gz 2>/dev/null | wc -l)
    echo -e "${GREEN}✓ 当前保留备份数: $REMAINING${NC}"
else
    echo -e "${RED}✗ 备份失败！${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}备份完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
