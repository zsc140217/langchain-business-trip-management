#!/bin/bash
# LangServe API 快速启动脚本

set -e  # 遇到错误立即退出

echo "========================================"
echo "LangServe API 快速启动"
echo "========================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查Python版本
echo -e "\n${YELLOW}[1/5] 检查Python版本${NC}"
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "当前Python版本: $python_version"

if ! python -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo -e "${RED}错误: 需要Python 3.11或更高版本${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python版本检查通过${NC}"

# 检查环境变量
echo -e "\n${YELLOW}[2/5] 检查环境变量${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}未找到.env文件，从模板创建...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠ 请编辑.env文件，填写DASHSCOPE_API_KEY${NC}"
        echo -e "${YELLOW}  然后重新运行此脚本${NC}"
        exit 1
    else
        echo -e "${RED}错误: 未找到.env.example模板${NC}"
        exit 1
    fi
fi

# 加载环境变量
source .env

if [ -z "$DASHSCOPE_API_KEY" ] || [ "$DASHSCOPE_API_KEY" = "your_dashscope_api_key_here" ]; then
    echo -e "${RED}错误: 请在.env文件中设置DASHSCOPE_API_KEY${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 环境变量检查通过${NC}"

# 安装依赖
echo -e "\n${YELLOW}[3/5] 检查依赖${NC}"
if ! pip list | grep -q "langserve"; then
    echo "正在安装依赖..."
    pip install -r requirements_api.txt
    echo -e "${GREEN}✓ 依赖安装完成${NC}"
else
    echo -e "${GREEN}✓ 依赖已安装${NC}"
fi

# 检查端口
echo -e "\n${YELLOW}[4/5] 检查端口${NC}"
PORT=${PORT:-8000}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠ 端口$PORT已被占用${NC}"
    echo "尝试使用端口8001..."
    PORT=8001
fi
echo -e "${GREEN}✓ 将使用端口$PORT${NC}"

# 启动API服务
echo -e "\n${YELLOW}[5/5] 启动API服务${NC}"
echo "========================================"
echo "🚀 正在启动LangServe API..."
echo "========================================"
echo ""
echo "📍 服务地址: http://localhost:$PORT"
echo "📖 API文档: http://localhost:$PORT/docs"
echo "🏥 健康检查: http://localhost:$PORT/health"
echo "📦 模块列表: http://localhost:$PORT/modules"
echo ""
echo "✨ Playground界面:"
echo "  1. Simple RAG       → http://localhost:$PORT/simple-rag/playground"
echo "  2. Advanced RAG     → http://localhost:$PORT/advanced-rag/playground"
echo "  3. ReAct Agent      → http://localhost:$PORT/react-agent/playground"
echo "  4. Multi-Agent      → http://localhost:$PORT/multi-agent/playground"
echo "  5. Sequential Chain → http://localhost:$PORT/sequential-chain/playground"
echo "  6. Parallel Chain   → http://localhost:$PORT/parallel-chain/playground"
echo "  7. Memory System    → http://localhost:$PORT/memory-chain/playground"
echo ""
echo "🎯 按 Ctrl+C 停止服务"
echo "========================================"
echo ""

# 启动服务
export PORT=$PORT
cd .. && python -m api.main
