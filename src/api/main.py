"""
LangServe API - FastAPI应用主入口

使用LangServe自动部署所有LangChain模块为REST API

特性：
1. 自动生成 /invoke 和 /stream 端点
2. 内置 /playground 交互式界面
3. OpenAPI文档自动生成
4. CORS支持
5. 健康检查和监控
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from langserve import add_routes
import uvicorn

# 导入所有模块的chain/agent
from chains import (
    get_simple_rag_chain,
    get_advanced_rag_chain,
    get_react_agent,
    get_multi_agent_graph,
    get_sequential_chain,
    get_parallel_chain,
    get_memory_chain,
)

# 创建FastAPI应用
app = FastAPI(
    title="LangChain Business Trip Management API",
    version="1.0.0",
    description="""
    企业差旅管理系统 - LangChain实现

    ## 功能模块

    ### Module 1: Simple RAG (简单检索增强生成)
    - `/simple-rag/invoke` - 基于FAISS的文档检索问答
    - `/simple-rag/stream` - 流式响应
    - `/simple-rag/playground` - 交互式测试界面

    ### Module 2: Advanced RAG (高级检索增强)
    - `/advanced-rag/invoke` - 混合检索 + 重排序
    - `/advanced-rag/stream` - 流式响应
    - `/advanced-rag/playground` - 交互式测试界面

    ### Module 3: ReAct Agent (工具调用智能体)
    - `/react-agent/invoke` - 自主推理和工具调用
    - `/react-agent/stream` - 流式响应
    - `/react-agent/playground` - 交互式测试界面

    ### Module 4: Multi-Agent (多智能体协作)
    - `/multi-agent/invoke` - LangGraph状态图编排
    - `/multi-agent/stream` - 流式响应
    - `/multi-agent/playground` - 交互式测试界面

    ### Module 5: Sequential Chain (顺序链)
    - `/sequential-chain/invoke` - 顺序执行多个步骤
    - `/sequential-chain/stream` - 流式响应
    - `/sequential-chain/playground` - 交互式测试界面

    ### Module 5: Parallel Chain (并行链)
    - `/parallel-chain/invoke` - 并行执行多个任务
    - `/parallel-chain/stream` - 流式响应
    - `/parallel-chain/playground` - 交互式测试界面

    ### Module 6: Memory System (记忆系统)
    - `/memory-chain/invoke` - 带记忆的对话系统
    - `/memory-chain/stream` - 流式响应
    - `/memory-chain/playground` - 交互式测试界面

    ## 使用方法

    ### 1. invoke - 同步调用
    ```bash
    curl -X POST "http://localhost:8000/simple-rag/invoke" \\
         -H "Content-Type: application/json" \\
         -d '{"input": "去上海出差住宿能报多少钱？"}'
    ```

    ### 2. stream - 流式调用
    ```bash
    curl -X POST "http://localhost:8000/simple-rag/stream" \\
         -H "Content-Type: application/json" \\
         -d '{"input": "去上海出差住宿能报多少钱？"}'
    ```

    ### 3. playground - 浏览器测试
    访问 http://localhost:8000/simple-rag/playground

    ## LangSmith追踪
    所有请求自动记录到LangSmith平台，可在以下位置查看：
    https://smith.langchain.com
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS配置 - 允许前端调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 根路径重定向到文档
@app.get("/")
async def root():
    """重定向到API文档"""
    return RedirectResponse(url="/docs")


# 健康检查
@app.get("/health")
async def health_check():
    """
    健康检查端点

    检查项：
    - API服务状态
    - 环境变量配置
    - LangSmith连接
    """
    health_status = {
        "status": "healthy",
        "service": "LangChain Business Trip Management API",
        "version": "1.0.0",
    }

    # 检查必需的环境变量
    required_env_vars = ["DASHSCOPE_API_KEY"]
    optional_env_vars = ["LANGCHAIN_API_KEY", "LANGCHAIN_TRACING_V2"]

    env_status = {}
    for var in required_env_vars:
        env_status[var] = "✓" if os.getenv(var) else "✗ (REQUIRED)"

    for var in optional_env_vars:
        env_status[var] = "✓" if os.getenv(var) else "○ (optional)"

    health_status["environment"] = env_status

    # 检查是否有缺失的必需环境变量
    missing_required = [var for var in required_env_vars if not os.getenv(var)]
    if missing_required:
        health_status["status"] = "degraded"
        health_status["warning"] = f"Missing required environment variables: {', '.join(missing_required)}"

    return health_status


# 模块信息端点
@app.get("/modules")
async def list_modules():
    """
    列出所有可用模块及其端点
    """
    modules = [
        {
            "module": "Module 1: Simple RAG",
            "description": "简单检索增强生成 - FAISS向量检索",
            "endpoints": {
                "invoke": "/simple-rag/invoke",
                "stream": "/simple-rag/stream",
                "playground": "/simple-rag/playground",
            },
            "example": {
                "input": "去上海出差住宿能报多少钱？"
            }
        },
        {
            "module": "Module 2: Advanced RAG",
            "description": "高级检索增强 - 混合检索 + 重排序",
            "endpoints": {
                "invoke": "/advanced-rag/invoke",
                "stream": "/advanced-rag/stream",
                "playground": "/advanced-rag/playground",
            },
            "example": {
                "input": "出差期间的餐饮补贴标准是什么？"
            }
        },
        {
            "module": "Module 3: ReAct Agent",
            "description": "工具调用智能体 - 自主推理和行动",
            "endpoints": {
                "invoke": "/react-agent/invoke",
                "stream": "/react-agent/stream",
                "playground": "/react-agent/playground",
            },
            "example": {
                "input": "我要去深圳出差，帮我查天气和订酒店"
            }
        },
        {
            "module": "Module 4: Multi-Agent",
            "description": "多智能体协作 - LangGraph状态图编排",
            "endpoints": {
                "invoke": "/multi-agent/invoke",
                "stream": "/multi-agent/stream",
                "playground": "/multi-agent/playground",
            },
            "example": {
                "input": "下周去杭州出差3天，帮我规划行程"
            }
        },
        {
            "module": "Module 5: Sequential Chain",
            "description": "顺序链 - 多步骤顺序执行",
            "endpoints": {
                "invoke": "/sequential-chain/invoke",
                "stream": "/sequential-chain/stream",
                "playground": "/sequential-chain/playground",
            },
            "example": {
                "input": {
                    "destination": "上海",
                    "days": 3
                }
            }
        },
        {
            "module": "Module 5: Parallel Chain",
            "description": "并行链 - 多任务并行执行",
            "endpoints": {
                "invoke": "/parallel-chain/invoke",
                "stream": "/parallel-chain/stream",
                "playground": "/parallel-chain/playground",
            },
            "example": {
                "input": {
                    "destination": "深圳",
                    "days": 2
                }
            }
        },
        {
            "module": "Module 6: Memory System",
            "description": "记忆系统 - 三层记忆架构",
            "endpoints": {
                "invoke": "/memory-chain/invoke",
                "stream": "/memory-chain/stream",
                "playground": "/memory-chain/playground",
            },
            "example": {
                "input": "我叫张三，下周要去北京出差"
            }
        },
    ]

    return {
        "total_modules": len(modules),
        "modules": modules,
        "documentation": "/docs",
        "health_check": "/health",
    }


# ============================================================================
# LangServe路由配置
# ============================================================================

# Module 1: Simple RAG
add_routes(
    app,
    get_simple_rag_chain(),
    path="/simple-rag",
    enabled_endpoints=["invoke", "stream", "playground"],
)

# Module 2: Advanced RAG
add_routes(
    app,
    get_advanced_rag_chain(),
    path="/advanced-rag",
    enabled_endpoints=["invoke", "stream", "playground"],
)

# Module 3: ReAct Agent
add_routes(
    app,
    get_react_agent(),
    path="/react-agent",
    enabled_endpoints=["invoke", "stream", "playground"],
)

# Module 4: Multi-Agent
add_routes(
    app,
    get_multi_agent_graph(),
    path="/multi-agent",
    enabled_endpoints=["invoke", "stream", "playground"],
)

# Module 5: Sequential Chain
add_routes(
    app,
    get_sequential_chain(),
    path="/sequential-chain",
    enabled_endpoints=["invoke", "stream", "playground"],
)

# Module 5: Parallel Chain
add_routes(
    app,
    get_parallel_chain(),
    path="/parallel-chain",
    enabled_endpoints=["invoke", "stream", "playground"],
)

# Module 6: Memory System
add_routes(
    app,
    get_memory_chain(),
    path="/memory-chain",
    enabled_endpoints=["invoke", "stream", "playground"],
)


# ============================================================================
# 启动配置
# ============================================================================

def main():
    """启动API服务"""
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    print("=" * 80)
    print("🚀 LangChain Business Trip Management API")
    print("=" * 80)
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"📖 API文档: http://{host}:{port}/docs")
    print(f"🏥 健康检查: http://{host}:{port}/health")
    print(f"📦 模块列表: http://{host}:{port}/modules")
    print("=" * 80)
    print("\n✨ 已部署的模块:")
    print("  1. Simple RAG       → /simple-rag/playground")
    print("  2. Advanced RAG     → /advanced-rag/playground")
    print("  3. ReAct Agent      → /react-agent/playground")
    print("  4. Multi-Agent      → /multi-agent/playground")
    print("  5. Sequential Chain → /sequential-chain/playground")
    print("  6. Parallel Chain   → /parallel-chain/playground")
    print("  7. Memory System    → /memory-chain/playground")
    print("=" * 80)

    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("\n[WARN]  警告: 未设置 DASHSCOPE_API_KEY 环境变量")
        print("   请设置环境变量后重启服务")

    if not os.getenv("LANGCHAIN_API_KEY"):
        print("\n💡 提示: 未设置 LANGCHAIN_API_KEY，LangSmith追踪功能将不可用")
        print("   如需启用，请设置以下环境变量：")
        print("   - LANGCHAIN_API_KEY")
        print("   - LANGCHAIN_TRACING_V2=true")
        print("   - LANGCHAIN_PROJECT=business-trip-management")

    print("\n🎯 按 Ctrl+C 停止服务\n")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
