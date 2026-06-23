"""
FastAPI 接口：差旅审批申请
实现方案 A（单向推送）：接收申请 → LangGraph 处理 → 推送到飞书群
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import os
from dotenv import load_dotenv

from src.modules.module_5_langgraph.graphs.react_graph import create_react_graph
from src.harness.feishu_client import FeishuClient, determine_card_type

# 加载环境变量
load_dotenv()

# 初始化 FastAPI
app = FastAPI(
    title="差旅审批 API",
    description="基于 LangGraph + 飞书的智能差旅审批系统",
    version="1.0.0"
)

# 初始化组件
graph = create_react_graph()
feishu_webhook_key = os.getenv("FEISHU_WEBHOOK_KEY")

if not feishu_webhook_key:
    raise ValueError("FEISHU_WEBHOOK_KEY environment variable is required")

feishu_client = FeishuClient(feishu_webhook_key)


class TravelRequest(BaseModel):
    """差旅申请请求模型"""
    destination: str = Field(..., description="目的地城市", example="上海")
    start_date: str = Field(..., description="开始日期", example="2026-06-20")
    end_date: str = Field(..., description="结束日期", example="2026-06-22")
    purpose: str = Field(..., description="出差目的", example="客户拜访")
    user_name: str = Field(default="员工", description="申请人姓名", example="张三")


class TravelResponse(BaseModel):
    """差旅申请响应模型"""
    status: str = Field(..., description="处理状态", example="success")
    approval_result: str = Field(..., description="审批结果消息")
    feishu_sent: bool = Field(..., description="飞书消息是否发送成功")
    query: str = Field(..., description="处理的查询语句")
    iteration: int = Field(..., description="实际迭代次数")


@app.get("/")
async def root():
    """API 根路径"""
    return {
        "message": "差旅审批 API",
        "version": "1.0.0",
        "endpoints": {
            "submit": "/api/travel/submit",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "feishu_configured": feishu_webhook_key is not None
    }


@app.post("/api/travel/submit", response_model=TravelResponse)
async def submit_travel_application(request: TravelRequest):
    """
    提交差旅申请并推送结果到飞书

    流程：
    1. 构造查询语句
    2. 调用 LangGraph ReAct Agent 处理
    3. 提取审批结果
    4. 推送到飞书群（卡片消息）

    Args:
        request: 差旅申请信息

    Returns:
        处理结果和飞书推送状态
    """
    try:
        # 1. 构造查询语句
        query = (
            f"我要去{request.destination}出差，"
            f"时间{request.start_date}到{request.end_date}，"
            f"目的是{request.purpose}"
        )

        print(f"[API] Received request: {query}")

        # 2. 调用 LangGraph 处理
        from src.modules.module_5_langgraph.state import create_initial_state
        initial_state = create_initial_state(query, max_iterations=3)
        result = graph.invoke(initial_state)

        # 3. 提取审批结果
        approval_message = result.get("answer") or result.get("response", "审批处理失败")
        iteration = result.get("iteration", 0)

        print(f"[API] LangGraph result: {approval_message}")
        print(f"[API] Iterations: {iteration}")

        # 4. 判断卡片类型
        card_type = determine_card_type(approval_message)

        # 5. 推送到飞书群
        feishu_result = feishu_client.send_card_message(
            title=f"差旅申请 - {request.user_name}",
            content=f"**目的地**: {request.destination}\n"
                    f"**日期**: {request.start_date} 至 {request.end_date}\n"
                    f"**目的**: {request.purpose}\n\n"
                    f"---\n\n"
                    f"{approval_message}",
            card_type=card_type
        )

        feishu_sent = feishu_result.get("StatusCode") == 0

        if not feishu_sent:
            print(f"[WARN] Feishu send failed: {feishu_result}")
        else:
            print("[OK] Message sent to Feishu successfully")

        return TravelResponse(
            status="success",
            approval_result=approval_message,
            feishu_sent=feishu_sent,
            query=query,
            iteration=iteration
        )

    except Exception as e:
        print(f"[ERROR] API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"处理失败: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    print("[+] Starting Travel Approval API...")
    print(f"[+] Feishu configured: {feishu_webhook_key is not None}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
