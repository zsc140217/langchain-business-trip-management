"""
统一RAG-Agent架构 API入口
集成架构v2的OrchestratorAgent + ApprovalEngine + 飞书客户端

对应 docs/ARCHITECTURE_V2_PLAN.md
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.llm import get_llm
from src.rag.loader import load_documents
from src.rag.retriever import create_vectorstore, get_retriever
from src.harness.feishu_client import FeishuClient
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.approval_engine import ApprovalEngine
from src.memory.memory_service import MemoryService
from src.monitoring.prometheus_exporter import setup_metrics_endpoint, PrometheusMiddleware
from src.monitoring.alert_manager import AlertManager, AlertmanagerWebhook
from src.tools.registry import get_all_tools

# 导入Module 5的审批图
from src.modules.module_5_langgraph.graphs.approval_graph import create_approval_graph

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== FastAPI应用初始化 ====================

app = FastAPI(
    title="统一RAG-Agent架构 API",
    version="2.0.0",
    description="""
    企业差旅管理系统 - 架构v2

    ## 核心特性
    - **统一入口路由**: OrchestratorAgent自动识别查询意图
    - **两个业务域**: Q&A域（政策查询）+ 审批域（报销审批）
    - **飞书集成**: 审批结果自动推送到飞书群
    - **记忆系统**: 三层记忆（短期/工作/长期）
    - **监控追踪**: LangSmith全链路追踪

    ## 使用示例

    ### Q&A域查询
    ```bash
    curl -X POST "http://localhost:8001/api/unified/chat" \\
         -H "Content-Type: application/json" \\
         -d '{"query": "北京住宿标准是多少？", "user_id": "user123"}'
    ```

    ### 审批域申请
    ```bash
    curl -X POST "http://localhost:8001/api/unified/chat" \\
         -H "Content-Type: application/json" \\
         -d '{"query": "我要报销去北京出差3天的费用", "user_id": "user123"}'
    ```
    """
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 全局变量 ====================

# 在startup事件中初始化
orchestrator = None
memory_service = None
feishu_client = None

# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    """对话请求模型"""
    query: str = Field(..., description="用户查询", min_length=1)
    user_id: str = Field(default="default_user", description="用户ID")
    conversation_id: Optional[str] = Field(None, description="会话ID")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "我要报销去北京出差3天的费用",
                "user_id": "user123",
                "conversation_id": "conv456"
            }
        }


class ChatResponse(BaseModel):
    """对话响应模型"""
    answer: str = Field(..., description="回答内容")
    route: str = Field(default="", description="路由路径（qa_domain/approval_domain）")
    user_id: str = Field(..., description="用户ID")
    conversation_id: Optional[str] = Field(None, description="会话ID")


class StatsResponse(BaseModel):
    """统计信息响应"""
    total_requests: int
    fast_path_hits: int
    qa_domain_requests: int
    approval_domain_requests: int


# ==================== 全局变量 ====================

orchestrator: Optional[OrchestratorAgent] = None
memory_service: Optional[MemoryService] = None
feishu_client: Optional[FeishuClient] = None


# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化所有组件"""
    global orchestrator, memory_service, feishu_client

    logger.info("=" * 80)
    logger.info("🚀 统一RAG-Agent架构 v2.0 启动中...")
    logger.info("=" * 80)

    try:
        # 0. 初始化 LangSmith 追踪
        try:
            from src.monitoring import initialize_langsmith
            ls_config = initialize_langsmith(
                project_name="business-trip-management",
                tags=["unified-api", "v2"],
            )
            logger.info(f"LangSmith tracing: {ls_config.enabled}")
        except Exception as e:
            logger.warning(f"LangSmith initialization failed: {e}")

        # 1. 检查环境变量
        dashscope_key = os.getenv("DASHSCOPE_API_KEY")
        feishu_webhook_key = os.getenv("FEISHU_WEBHOOK_KEY")

        if not dashscope_key:
            logger.error("❌ 缺少 DASHSCOPE_API_KEY 环境变量")
            return

        if not feishu_webhook_key:
            logger.warning("⚠️  缺少 FEISHU_WEBHOOK_KEY，飞书通知功能将不可用")

        # 2. 初始化LLM
        logger.info("🤖 初始化LLM...")
        llm = get_llm(temperature=0.3)

        # 3. 初始化飞书客户端
        logger.info("📱 初始化飞书客户端...")
        if feishu_webhook_key:
            feishu_client = FeishuClient(webhook_key=feishu_webhook_key)
            logger.info("✅ 飞书客户端初始化成功")
        else:
            feishu_client = None
            logger.warning("⚠️  飞书客户端未初始化（缺少WEBHOOK_KEY）")
        # AlertManager webhook receiver
        alert_manager = AlertManager(feishu_client=feishu_client)


        # 4. 初始化记忆服务
        logger.info("🧠 初始化记忆服务...")
        memory_service = MemoryService()
        logger.info("✅ 记忆服务初始化成功")

        # 5. 加载文档并创建检索器
        logger.info("📚 加载企业差旅政策文档...")
        documents = load_documents("data/travel_policy.txt")
        vectorstore = create_vectorstore(documents)
        retriever = get_retriever(vectorstore, k=3)
        logger.info(f"✅ 文档加载完成，共 {len(documents)} 个文档块")

        # 6. 注册所有工具
        logger.info("🔧 注册工具...")
        tools = get_all_tools()
        logger.info(f"✅ 工具注册完成，共 {len(tools)} 个工具")
        for tool_name in tools.keys():
            logger.info(f"   - {tool_name}")

        # 7. 创建审批图
        logger.info("📊 创建审批工作流...")
        approval_graph = create_approval_graph()
        logger.info("✅ 审批工作流创建成功")

        # 8. 创建审批引擎
        logger.info("⚖️  初始化审批引擎...")
        if feishu_client:
            approval_engine = ApprovalEngine(
                llm=llm,
                memory_service=memory_service,
                feishu_client=feishu_client,
                approval_graph=approval_graph,
                auto_approval_threshold=1000  # 1000元以下自动审批
            )
            logger.info("✅ 审批引擎初始化成功（飞书通知已启用）")
        else:
            # 如果没有飞书客户端，创建一个mock客户端
            class MockFeishuClient:
                def send_card_message(self, title, content, card_type):
                    logger.warning(f"[MockFeishu] 跳过发送: {title}")
                    return {"StatusCode": 0}
                def send_approval_card(self, **kwargs):
                    logger.warning(f"[MockFeishu] 跳过发送审批卡片")
                    return {"StatusCode": 0}

            approval_engine = ApprovalEngine(
                llm=llm,
                memory_service=memory_service,
                feishu_client=MockFeishuClient(),
                approval_graph=approval_graph,
                auto_approval_threshold=1000
            )
            logger.warning("⚠️  审批引擎初始化成功（使用Mock飞书客户端）")

        # 8.5. 启动飞书长连接客户端（后台线程）
        feishu_app_id = os.getenv("FEISHU_APP_ID")
        feishu_app_secret = os.getenv("FEISHU_APP_SECRET")

        if feishu_app_id and feishu_app_secret:
            try:
                import threading
                from src.harness.feishu_ws_client import FeishuWSClient
                from src.harness.feishu_callback_handler import FeishuCallbackHandler

                logger.info("🔗 启动飞书长连接客户端...")

                # 创建回调处理器
                callback_handler = FeishuCallbackHandler(approval_engine=approval_engine)

                # 创建长连接客户端
                ws_client = FeishuWSClient(
                    app_id=feishu_app_id,
                    app_secret=feishu_app_secret,
                    callback_handler=callback_handler
                )

                # 在后台线程中启动（避免阻塞主线程）
                def start_ws_client():
                    try:
                        ws_client.start()
                    except Exception as e:
                        logger.error(f"❌ 飞书长连接客户端启动失败: {e}", exc_info=True)

                ws_thread = threading.Thread(target=start_ws_client, daemon=True)
                ws_thread.start()

                logger.info("✅ 飞书长连接客户端已在后台启动")
                logger.info("   - 审批回调功能已启用")

            except Exception as e:
                logger.warning(f"⚠️  飞书长连接客户端启动失败: {e}")
                logger.warning("   - 审批回调功能将不可用，但不影响其他功能")
        else:
            logger.info("ℹ️  未配置飞书长连接（FEISHU_APP_ID/SECRET），跳过启动")
            logger.info("   - 审批回调功能将不可用")

        # 9. 创建统一入口Agent
        logger.info("🎯 初始化OrchestratorAgent...")
        orchestrator = OrchestratorAgent(
            llm=llm,
            tools=tools,
            approval_engine=approval_engine,
            memory_service=memory_service
        )
        logger.info("✅ OrchestratorAgent初始化成功")

        # 10. 启动完成
        logger.info("=" * 80)
        logger.info("✅ 统一RAG-Agent架构 v2.0 启动完成！")
        logger.info("=" * 80)
        logger.info("📍 服务地址: http://0.0.0.0:8001")
        logger.info("📖 API文档: http://0.0.0.0:8001/docs")
        logger.info("🏥 健康检查: http://0.0.0.0:8001/health")
        logger.info("=" * 80)

        # 11. 发送启动通知到飞书
        if feishu_client:
            try:
                feishu_client.send_card_message(
                    title="🚀 系统启动通知",
                    content=f"""**统一RAG-Agent架构 v2.0** 已成功启动

**服务地址**: http://localhost:8001
**API文档**: http://localhost:8001/docs
**启动时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

系统功能：
- ✅ Q&A域（政策查询）
- ✅ 审批域（报销审批）
- ✅ 飞书通知（实时推送）
- ✅ 记忆系统（三层记忆）

祝您使用愉快！""",
                    card_type="success"
                )
                logger.info("✅ 飞书启动通知已发送")
            except Exception as e:
                logger.error(f"❌ 飞书启动通知发送失败: {e}")

    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()


# ==================== API端点 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "统一RAG-Agent架构 API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "chat": "/api/unified/chat"
    }




@app.post("/api/monitoring/alert")
async def receive_alert(webhook: AlertmanagerWebhook):
    """接收 AlertManager Webhook 告警，推送到飞书"""
    try:
        result = await alert_manager.handle_alert(webhook)
        return {"status": "success", "message": "Alert processed"}
    except Exception as e:
        logger.error(f"AlertManager webhook failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查"""
    health_status = {
        "status": "healthy" if orchestrator else "initializing",
        "components": {
            "orchestrator": orchestrator is not None,
            "memory_service": memory_service is not None,
            "feishu_client": feishu_client is not None,
        },
        "environment": {
            "DASHSCOPE_API_KEY": "✓" if os.getenv("DASHSCOPE_API_KEY") else "✗",
            "FEISHU_WEBHOOK_KEY": "✓" if os.getenv("FEISHU_WEBHOOK_KEY") else "✗",
            "LANGCHAIN_TRACING_V2": "✓" if os.getenv("LANGCHAIN_TRACING_V2") else "○",
        }
    }

    return health_status


@app.post("/api/unified/chat", response_model=ChatResponse)
async def unified_chat(request: ChatRequest):
    """
    统一对话接口

    自动路由到：
    - Q&A域：政策查询、天气查询、酒店查询等
    - 审批域：报销申请、审批状态查询等

    飞书通知：
    - 审批通过/拒绝 → 自动发送飞书卡片消息
    """
    if not orchestrator:
        raise HTTPException(
            status_code=503,
            detail="系统未初始化，请检查日志"
        )

    try:
        logger.info(f"[API] 收到请求: user_id={request.user_id}, query={request.query}")

        # 调用OrchestratorAgent路由
        answer = orchestrator.route(
            query=request.query,
            user_id=request.user_id,
            conversation_id=request.conversation_id
        )

        # 判断路由路径
        stats = orchestrator.get_stats()
        if stats["approval_domain"] > 0:
            route = "approval_domain"
        elif stats["fast_path"] > 0:
            route = "fast_path"
        else:
            route = "qa_domain"

        logger.info(f"[API] 响应完成: route={route}")

        return ChatResponse(
            answer=answer,
            route=route,
            user_id=request.user_id,
            conversation_id=request.conversation_id
        )

    except Exception as e:
        logger.error(f"[API] 处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.get("/api/unified/stats", response_model=StatsResponse)
async def get_stats():
    """获取统计信息"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="系统未初始化")

    stats = orchestrator.get_stats()

    return StatsResponse(
        total_requests=stats["total"],
        fast_path_hits=stats["fast_path"],
        qa_domain_requests=stats["qa_domain"],
        approval_domain_requests=stats["approval_domain"]
    )


@app.post("/api/unified/stats/reset")
async def reset_stats():
    """重置统计信息"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="系统未初始化")

    orchestrator.reset_stats()

    return {"message": "统计信息已重置"}


@app.post("/api/test/feishu")
async def test_feishu():
    """测试飞书通知"""
    if not feishu_client:
        raise HTTPException(status_code=503, detail="飞书客户端未初始化")

    try:
        result = feishu_client.send_card_message(
            title="🧪 测试通知",
            content=f"""这是一条测试消息

**发送时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**测试项目**: 飞书卡片消息推送
**状态**: 成功

如果您看到这条消息，说明飞书集成工作正常！✅""",
            card_type="info"
        )

        logger.info(f"[测试] 飞书通知发送结果: {result}")

        return {
            "message": "飞书测试消息已发送",
            "result": result
        }

    except Exception as e:
        logger.error(f"[测试] 飞书通知发送失败: {e}")
        raise HTTPException(status_code=500, detail=f"发送失败: {str(e)}")


# ==================== 启动服务 ====================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        "unified_api:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
