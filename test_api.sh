#!/bin/bash

# AgentCard API 完整测试脚本
# 使用方法: bash test_api.sh

API_BASE="http://localhost:8000/api"
AUTH="-u admin:admin"  # 需要先创建 admin 用户

echo "=========================================="
echo "AgentCard API 测试"
echo "=========================================="
echo ""

# 颜色代码
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 辅助函数
print_test() {
    echo -e "${YELLOW}[$1]${NC} $2"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# ==========================================
# 测试 1: API 根路径
# ==========================================
print_test "1" "测试 API 根路径"
response=$(curl -s $API_BASE/)
if echo "$response" | grep -q "namespaces"; then
    print_success "API 根路径正常"
    echo "$response" | python3 -m json.tool
else
    print_error "API 根路径失败"
fi
echo ""

# ==========================================
# 测试 2: Namespaces API
# ==========================================
print_test "2" "测试 Namespaces API"

# 2.1 列表（GET）
echo "2.1 获取命名空间列表..."
curl -s "$API_BASE/namespaces/" | python3 -m json.tool | head -20
echo ""

# 2.2 创建（POST）- 需要认证
echo "2.2 创建新命名空间 'dev'..."
curl -s -X POST "$API_BASE/namespaces/" \
  -H "Content-Type: application/json" \
  $AUTH \
  -d '{
    "id": "dev",
    "name": "开发环境",
    "description": "用于开发和测试的命名空间",
    "is_active": true
  }' | python3 -m json.tool
echo ""

echo "2.3 创建命名空间 'prod'..."
curl -s -X POST "$API_BASE/namespaces/" \
  -H "Content-Type: application/json" \
  $AUTH \
  -d '{
    "id": "prod",
    "name": "生产环境",
    "description": "生产环境的命名空间",
    "is_active": true
  }' | python3 -m json.tool
echo ""

# 2.4 详情（GET）
echo "2.4 获取命名空间 'dev' 详情..."
curl -s "$API_BASE/namespaces/dev/" | python3 -m json.tool
echo ""

# 2.5 更新（PATCH）
echo "2.5 更新命名空间 'dev'..."
curl -s -X PATCH "$API_BASE/namespaces/dev/" \
  -H "Content-Type: application/json" \
  $AUTH \
  -d '{
    "description": "开发环境（已更新）"
  }' | python3 -m json.tool
echo ""

# ==========================================
# 测试 3: Schemas API
# ==========================================
print_test "3" "测试 Schemas API"

# 3.1 创建 Schema（需要先在 Django Admin 创建，或使用 Django Shell）
echo "3.1 创建 Schema 'physicalAsset v1'..."
echo "注意：Schema 创建需要包含字段，这里我们通过 API 创建简化版..."
# 由于 SchemaField 是嵌套的，通过 API 创建比较复杂
# 我们改用 Django shell 创建
echo "跳过（需要通过 Django Admin 或 Shell 创建完整的 Schema + Fields）"
echo ""

# 3.2 列表
echo "3.2 获取 Schema 列表..."
curl -s "$API_BASE/schemas/" | python3 -m json.tool
echo ""

# 3.3 Schema Catalog
echo "3.3 获取 Schema 目录..."
curl -s "$API_BASE/schemas/catalog/" | python3 -m json.tool
echo ""

# ==========================================
# 测试 4: AgentCards API
# ==========================================
print_test "4" "测试 AgentCards API"

# 4.1 创建 AgentCard（POST）
echo "4.1 创建 AgentCard 'HPLC-001'..."
curl -s -X POST "$API_BASE/agentcards/" \
  -H "Content-Type: application/json" \
  $AUTH \
  -d '{
    "namespace": "dev",
    "name": "HPLC-001",
    "version": "1.0.0",
    "is_default_version": true,
    "is_active": true,
    "protocol_version": "0.3.0",
    "description": "Agilent 1260 高效液相色谱仪",
    "url": "https://lab.example.com/instruments/hplc-001",
    "preferred_transport": "http",
    "capabilities": {
      "streaming": false,
      "tools": true
    },
    "default_input_modes": ["application/json", "text/plain"],
    "default_output_modes": ["application/json"],
    "skills": [
      {
        "name": "runAnalysis",
        "description": "运行液相色谱分析",
        "inputModes": ["application/json"],
        "outputModes": ["application/json"]
      },
      {
        "name": "getStatus",
        "description": "获取仪器状态",
        "inputModes": ["text/plain"],
        "outputModes": ["application/json"]
      }
    ],
    "domain_extensions": {}
  }' | python3 -m json.tool
echo ""

# 4.2 创建第二个版本
echo "4.2 创建 AgentCard 'HPLC-001' v2.0.0..."
curl -s -X POST "$API_BASE/agentcards/" \
  -H "Content-Type: application/json" \
  $AUTH \
  -d '{
    "namespace": "dev",
    "name": "HPLC-001",
    "version": "2.0.0",
    "is_default_version": false,
    "is_active": true,
    "protocol_version": "0.3.0",
    "description": "Agilent 1260 高效液相色谱仪（增强版）",
    "url": "https://lab.example.com/instruments/hplc-001",
    "preferred_transport": "http",
    "capabilities": {
      "streaming": true,
      "tools": true
    },
    "default_input_modes": ["application/json"],
    "default_output_modes": ["application/json"],
    "skills": [
      {
        "name": "runAnalysis",
        "description": "运行液相色谱分析",
        "inputModes": ["application/json"],
        "outputModes": ["application/json"]
      }
    ],
    "domain_extensions": {}
  }' | python3 -m json.tool
echo ""

# 4.3 列表（GET）
echo "4.3 获取所有 AgentCard..."
curl -s "$API_BASE/agentcards/" | python3 -m json.tool
echo ""

# 4.4 按命名空间过滤
echo "4.4 按命名空间 'dev' 过滤..."
curl -s "$API_BASE/agentcards/?namespace=dev" | python3 -m json.tool | head -30
echo ""

# 4.5 只返回默认版本
echo "4.5 只返回默认版本..."
curl -s "$API_BASE/agentcards/?is_default_version=true" | python3 -m json.tool | head -30
echo ""

# 4.6 按名称搜索
echo "4.6 按名称搜索 'HPLC'..."
curl -s "$API_BASE/agentcards/?name=HPLC" | python3 -m json.tool | head -30
echo ""

# 4.7 详情（GET）
echo "4.7 获取 AgentCard 详情（ID=1）..."
curl -s "$API_BASE/agentcards/1/" | python3 -m json.tool | head -50
echo ""

# 4.8 标准 JSON（A2A 协议格式）
echo "4.8 获取标准 A2A JSON 格式..."
curl -s "$API_BASE/agentcards/1/standard-json/" | python3 -m json.tool
echo ""

# 4.9 标准 JSON（包含元数据）
echo "4.9 获取标准 JSON（包含元数据）..."
curl -s "$API_BASE/agentcards/1/standard-json/?include_metadata=true" | python3 -m json.tool | head -40
echo ""

# 4.10 按命名空间查询（自定义端点）
echo "4.10 按命名空间查询（/by-namespace/dev/）..."
curl -s "$API_BASE/agentcards/by-namespace/dev/" | python3 -m json.tool | head -30
echo ""

# ==========================================
# 测试 5: 更新和删除
# ==========================================
print_test "5" "测试更新和删除操作"

# 5.1 部分更新（PATCH）
echo "5.1 部分更新 AgentCard..."
curl -s -X PATCH "$API_BASE/agentcards/1/" \
  -H "Content-Type: application/json" \
  $AUTH \
  -d '{
    "description": "Agilent 1260 高效液相色谱仪（已更新描述）"
  }' | python3 -m json.tool | head -30
echo ""

# 5.2 删除测试（创建一个临时的再删除）
echo "5.2 创建临时 AgentCard 用于删除测试..."
curl -s -X POST "$API_BASE/agentcards/" \
  -H "Content-Type: application/json" \
  $AUTH \
  -d '{
    "namespace": "dev",
    "name": "TempAgent",
    "version": "1.0.0",
    "protocol_version": "0.3.0",
    "description": "临时测试",
    "url": "https://temp.example.com",
    "preferred_transport": "http",
    "capabilities": {},
    "default_input_modes": ["text/plain"],
    "default_output_modes": ["text/plain"],
    "skills": [{"name": "test", "description": "test"}],
    "domain_extensions": {}
  }' > /dev/null

# 获取刚创建的 ID（假设是最后一个）
LAST_ID=$(curl -s "$API_BASE/agentcards/" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data['results'][-1]['id'])")
echo "临时 AgentCard ID: $LAST_ID"

echo "5.3 删除临时 AgentCard..."
curl -s -X DELETE "$API_BASE/agentcards/$LAST_ID/" \
  $AUTH
echo "已删除 ID $LAST_ID"
echo ""

# ==========================================
# 测试 6: 错误处理
# ==========================================
print_test "6" "测试错误处理"

# 6.1 未认证的写操作
echo "6.1 测试未认证的创建操作（应该失败）..."
response=$(curl -s -X POST "$API_BASE/namespaces/" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "unauthorized",
    "name": "未授权测试"
  }')
echo "$response" | python3 -m json.tool
echo ""

# 6.2 无效数据
echo "6.2 测试无效数据（缺少必填字段）..."
curl -s -X POST "$API_BASE/agentcards/" \
  -H "Content-Type: application/json" \
  $AUTH \
  -d '{
    "namespace": "dev",
    "name": "InvalidAgent"
  }' | python3 -m json.tool
echo ""

# 6.3 不存在的资源
echo "6.3 测试访问不存在的资源..."
curl -s "$API_BASE/agentcards/99999/" | python3 -m json.tool
echo ""

# ==========================================
# 测试 7: 分页
# ==========================================
print_test "7" "测试分页功能"

echo "7.1 测试分页（page_size=1）..."
curl -s "$API_BASE/agentcards/?page_size=1" | python3 -m json.tool | head -20
echo ""

# ==========================================
# 总结
# ==========================================
echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "访问可浏览 API: http://localhost:8000/api/"
echo "查看完整文档: docs/API-GUIDE.md"
echo ""
