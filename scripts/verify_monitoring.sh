#!/bin/bash
# 监控系统验证脚本

echo "================================"
echo "🔍 监控系统完整性检查"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 检查计数器
passed=0
failed=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $2"
        ((passed++))
    else
        echo -e "${RED}❌${NC} $2 (文件不存在: $1)"
        ((failed++))
    fi
}

check_service() {
    if curl -s "$1" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} $2 ($1)"
        ((passed++))
    else
        echo -e "${RED}❌${NC} $2 (无法访问: $1)"
        ((failed++))
    fi
}

echo "📁 检查配置文件..."
check_file "monitoring/docker-compose.yml" "Docker Compose配置"
check_file "monitoring/prometheus.yml" "Prometheus配置"
check_file "monitoring/alerts.yml" "告警规则"
check_file "monitoring/alertmanager.yml" "Alertmanager配置"
check_file "monitoring/grafana/dashboards/travel-agent-overview.json" "Grafana Dashboard"
echo ""

echo "📦 检查Python模块..."
check_file "src/monitoring/__init__.py" "监控模块入口"
check_file "src/monitoring/prometheus_exporter.py" "Prometheus导出器"
check_file "src/monitoring/alert_manager.py" "告警管理器"
echo ""

echo "📄 检查文档..."
check_file "docs/MODULE5_QUICKSTART.md" "快速上手指南"
check_file "docs/MODULE5_COMPLETION_SUMMARY.md" "完成总结"
check_file "docs/MODULE5_LEARNING_QUIZ.md" "学习检验题"
echo ""

echo "🧪 检查演示脚本..."
check_file "examples/monitoring_complete_demo.py" "完整演示"
check_file "examples/monitoring_fastapi_demo.py" "FastAPI演示"
echo ""

echo "🔧 检查环境配置..."
if grep -q "LANGCHAIN_API_KEY" .env; then
    echo -e "${GREEN}✅${NC} LangSmith API Key已配置"
    ((passed++))
else
    echo -e "${RED}❌${NC} LangSmith API Key未配置"
    ((failed++))
fi
echo ""

echo "🐳 检查Docker服务..."
if command -v docker-compose &> /dev/null; then
    if docker-compose -f monitoring/docker-compose.yml ps 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}✅${NC} Docker服务运行中"
        ((passed++))
    else
        echo -e "${RED}⚠️${NC} Docker服务未启动（运行: cd monitoring && docker-compose up -d）"
    fi
else
    echo -e "${RED}❌${NC} docker-compose未安装"
    ((failed++))
fi
echo ""

echo "================================"
echo "📊 检查结果"
echo "================================"
echo -e "${GREEN}通过: $passed${NC}"
echo -e "${RED}失败: $failed${NC}"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 所有检查通过！监控系统已就绪${NC}"
    echo ""
    echo "📚 下一步:"
    echo "  1. 启动监控服务: cd monitoring && docker-compose up -d"
    echo "  2. 运行演示: python examples/monitoring_complete_demo.py"
    echo "  3. 访问 Grafana: http://localhost:3000 (admin/admin123)"
    echo "  4. 访问 LangSmith: https://smith.langchain.com/"
    exit 0
else
    echo -e "${RED}⚠️ 发现 $failed 个问题，请检查修复${NC}"
    exit 1
fi
