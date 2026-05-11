"""
FastAPI主应用
提供企业差旅智能体的HTTP接口

对应Spring Boot的Controller层
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.llm import get_llm
from src.rag.loader import load_documents
from src.rag.retriever import create_vectorstore, get_retriever
from src.rag.chain import create_rag_chain
from src.tools.weather import query_weather, compare_weather

# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    """
    对话请求模型

    对应Spring Boot的DTO
    """
    message: str = Field(..., description="用户消息", min_length=1)
    chat_id: Optional[str] = Field("default", description="会话ID")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "去上海出差住宿标准是多少？",
                "chat_id": "user123"
            }
        }


class ChatResponse(BaseModel):
    """对话响应模型"""
    answer: str = Field(..., description="回答内容")
    sources: Optional[List[str]] = Field(None, description="来源文档")


class WeatherResponse(BaseModel):
    """天气响应模型"""
    city: str
    weather: str


# ==================== 应用初始化 ====================

app = FastAPI(
    title="LangChain企业差旅智能体",
    description="基于LangChain的企业差旅管理系统，提供规章问答、天气查询等功能",
    version="1.0.0"
)

# 配置CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量：存储初始化的组件
rag_chain = None
llm = None
retriever = None


@app.on_event("startup")
async def startup_event():
    """
    应用启动时初始化RAG组件

    对应Spring Boot的@PostConstruct
    """
    global rag_chain, llm, retriever

    print("🚀 正在启动LangChain企业差旅智能体...")

    try:
        # 检查环境变量
        if not os.getenv("DASHSCOPE_API_KEY"):
            print("⚠️  警告：未找到DASHSCOPE_API_KEY，请配置.env文件")
            return

        # 1. 加载文档
        print("📄 加载企业差旅规章...")
        documents = load_documents("data/travel_policy.txt")

        # 2. 创建向量存储
        print("🔄 创建向量存储...")
        vectorstore = create_vectorstore(documents)

        # 3. 创建检索器
        retriever = get_retriever(vectorstore, k=3)

        # 4. 创建LLM
        print("🤖 初始化LLM...")
        llm = get_llm(temperature=0.3)

        # 5. 创建RAG链
        print("⛓️  创建RAG链...")
        rag_chain = create_rag_chain(llm, retriever)

        print("✅ 启动成功！")

    except Exception as e:
        print(f"❌ 启动失败：{e}")
        import traceback
        traceback.print_exc()


# ==================== API接口 ====================

@app.get("/")
async def root():
    """
    根路径
    """
    return {
        "message": "欢迎使用LangChain企业差旅智能体",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """
    健康检查接口

    对应Spring Boot的Actuator
    """
    return {
        "status": "ok",
        "rag_initialized": rag_chain is not None,
        "llm_initialized": llm is not None
    }


@app.post("/api/chat/sync", response_model=ChatResponse)
async def chat_sync(request: ChatRequest):
    """
    同步对话接口

    对应Spring AI的：
    @PostMapping("/chat/sync")
    public String chatSync(@RequestBody ChatRequest request)

    这个接口会等待LLM生成完整回答后再返回
    适合简单查询，响应时间较短的场景
    """
    if rag_chain is None:
        raise HTTPException(
            status_code=503,
            detail="RAG系统未初始化，请检查配置"
        )

    try:
        # 调用RAG链
        result = rag_chain.invoke({"query": request.message})

        # 提取来源文档
        sources = [doc.page_content[:100] + "..."
                  for doc in result["source_documents"]]

        return ChatResponse(
            answer=result["result"],
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败：{str(e)}")


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式对话接口

    对应Spring AI的：
    @GetMapping("/chat/sse")
    public Flux<String> chatSSE(@RequestParam String message)

    这个接口会实时返回LLM生成的内容
    适合长回答，提升用户体验

    流式输出的优势：
    - 用户不用等待完整回答
    - 可以看到生成过程
    - 感觉更快
    """
    if llm is None or retriever is None:
        raise HTTPException(
            status_code=503,
            detail="系统未初始化"
        )

    async def generate():
        """
        生成器函数，逐块返回内容

        SSE（Server-Sent Events）格式：
        data: {"content": "文本内容"}\n\n
        """
        try:
            # 1. 检索相关文档
            docs = retriever.get_relevant_documents(request.message)
            context = "\n".join([doc.page_content for doc in docs])

            # 2. 构建Prompt
            prompt = f"""你是一个企业差旅助手。请根据以下企业差旅规章回答用户的问题。

规章内容：
{context}

用户问题：{request.message}

请给出准确、详细的回答。"""

            # 3. 创建流式LLM
            llm_stream = get_llm(streaming=True, temperature=0.3)

            # 4. 流式生成
            for chunk in llm_stream.stream(prompt):
                # 发送数据块
                yield f"data: {json.dumps({'content': chunk.content}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)  # 避免发送太快

            # 5. 发送结束标记
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/weather", response_model=WeatherResponse)
async def get_weather(city: str):
    """
    天气查询接口

    对应Spring AI的：
    @GetMapping("/weather")
    public String queryWeather(@RequestParam String city)

    这个接口直接调用天气工具
    """
    try:
        result = query_weather.invoke({"city": city})
        return WeatherResponse(city=city, weather=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@app.get("/api/weather/compare")
async def compare_weather_api(city1: str, city2: str):
    """
    天气对比接口
    """
    try:
        result = compare_weather.invoke({"city1": city1, "city2": city2})
        return {"comparison": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比失败：{str(e)}")


# ==================== 启动应用 ====================

if __name__ == "__main__":
    """
    直接运行此文件启动服务

    对应Spring Boot的：
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
    """
    import uvicorn

    # 从环境变量读取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    print(f"""
╔══════════════════════════════════════════════════════════╗
║     LangChain企业差旅智能体                               ║
╠══════════════════════════════════════════════════════════╣
║  服务地址: http://{host}:{port}                     ║
║  API文档: http://{host}:{port}/docs                 ║
║  健康检查: http://{host}:{port}/health              ║
╚══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # 开发模式：代码改动自动重启
        log_level="info"
    )
