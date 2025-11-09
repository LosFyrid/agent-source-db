#!/bin/bash

# ============================================================
# AgentCard 快速部署/更新脚本
# ============================================================
# 使用方法:
#   ./scripts/deploy.sh prod  # 部署/更新生产环境
#   ./scripts/deploy.sh test  # 部署/更新测试环境
# ============================================================

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    ENV_FILE=".env.prod"
    BRANCH="main"
    PORT="8000"
elif [ "$ENV" == "test" ]; then
    COMPOSE_FILE="docker-compose.test.yml"
    ENV_FILE=".env.test"
    BRANCH="develop"
    PORT="8001"
else
    echo -e "${RED}错误: 无效的环境参数 '$ENV'${NC}"
    echo "有效参数: prod, test"
    exit 1
fi

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}AgentCard 系统部署${NC}"
echo -e "${BLUE}============================================================${NC}"
echo "环境: $ENV"
echo "分支: $BRANCH"
echo "端口: $PORT"
echo "配置: $ENV_FILE"
echo -e "${BLUE}============================================================${NC}"
echo ""

# 检查配置文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}错误: 配置文件 $ENV_FILE 不存在！${NC}"
    echo "请先创建配置文件:"
    echo "  cp ${ENV_FILE}.example $ENV_FILE"
    echo "  nano $ENV_FILE"
    exit 1
fi

# 步骤 1: 更新代码
echo -e "${YELLOW}[1/6] 更新代码...${NC}"
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"
echo -e "${GREEN}✓ 代码更新完成${NC}"
echo ""

# 步骤 2: 构建镜像
echo -e "${YELLOW}[2/6] 构建 Docker 镜像...${NC}"
docker-compose -f "$COMPOSE_FILE" build
echo -e "${GREEN}✓ 镜像构建完成${NC}"
echo ""

# 步骤 3: 启动服务
echo -e "${YELLOW}[3/6] 启动服务...${NC}"
docker-compose -f "$COMPOSE_FILE" up -d
echo -e "${GREEN}✓ 服务启动完成${NC}"
echo ""

# 步骤 4: 等待数据库就绪
echo -e "${YELLOW}[4/6] 等待数据库就绪...${NC}"
sleep 5
echo -e "${GREEN}✓ 数据库已就绪${NC}"
echo ""

# 步骤 5: 运行数据库迁移
echo -e "${YELLOW}[5/6] 运行数据库迁移...${NC}"
docker-compose -f "$COMPOSE_FILE" exec -T web python manage.py migrate --noinput
echo -e "${GREEN}✓ 数据库迁移完成${NC}"
echo ""

# 步骤 6: 收集静态文件
echo -e "${YELLOW}[6/6] 收集静态文件...${NC}"
docker-compose -f "$COMPOSE_FILE" exec -T web python manage.py collectstatic --noinput
echo -e "${GREEN}✓ 静态文件收集完成${NC}"
echo ""

# 显示服务状态
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "服务状态:"
docker-compose -f "$COMPOSE_FILE" ps
echo ""
echo "访问地址:"
echo "  管理后台: http://YOUR_SERVER_IP:$PORT/admin/"
echo "  API: http://YOUR_SERVER_IP:$PORT/api/"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose -f $COMPOSE_FILE logs -f"
echo "  重启服务: docker-compose -f $COMPOSE_FILE restart"
echo "  停止服务: docker-compose -f $COMPOSE_FILE stop"
echo -e "${GREEN}============================================================${NC}"
