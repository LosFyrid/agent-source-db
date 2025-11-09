#!/bin/bash

# ============================================================
# 从生产环境复制数据到测试环境
# ============================================================
# 使用场景: 测试环境需要真实生产数据进行验证
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}============================================================${NC}"
echo -e "${YELLOW}生产数据复制到测试环境${NC}"
echo -e "${YELLOW}============================================================${NC}"
echo ""

# 警告提示
echo -e "${RED}警告: 此操作会覆盖测试环境的所有数据！${NC}"
read -p "确定要继续吗? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "操作已取消"
    exit 0
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEMP_BACKUP="temp_prod_backup_${TIMESTAMP}.sql"

echo ""
echo -e "${YELLOW}[1/3] 备份生产数据...${NC}"
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U produser agentcard_prod > "$TEMP_BACKUP"
echo -e "${GREEN}✓ 生产数据已备份到 $TEMP_BACKUP${NC}"

echo ""
echo -e "${YELLOW}[2/3] 清空测试数据库...${NC}"
docker-compose -f docker-compose.test.yml exec -T db psql -U testuser -d agentcard_test -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
echo -e "${GREEN}✓ 测试数据库已清空${NC}"

echo ""
echo -e "${YELLOW}[3/3] 恢复生产数据到测试环境...${NC}"
cat "$TEMP_BACKUP" | docker-compose -f docker-compose.test.yml exec -T db psql -U testuser agentcard_test
echo -e "${GREEN}✓ 数据恢复完成${NC}"

echo ""
echo -e "${YELLOW}清理临时文件...${NC}"
rm "$TEMP_BACKUP"
echo -e "${GREEN}✓ 临时文件已删除${NC}"

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}数据复制完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo "测试环境现在包含生产环境的所有数据"
