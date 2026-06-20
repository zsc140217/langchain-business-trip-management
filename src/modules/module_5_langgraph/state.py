"""
LangGraph 状态定义
定义Agent Loop的共享状态结构

对应LangGraph概念：
- StateGraph需要一个TypedDict作为状态类型
- 所有节点都接收和返回这个状态
- 使用Annotated + operator.add实现列表追加（而非替换）
"""
from typing import TypedDict, List, Optional, Annotated, Literal
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
import operator


class TravelAgentState(TypedDict):
    """
    差旅Agent的共享状态

    所有节点通过读写这个状态来传递信息

    字段说明：
    - query: 用户原始查询
    - rewritten_query: 改写后的查询（用于检索优化）
    - documents: 检索到的相关文档
    - answer: 最终生成的答案
    - iteration: 当前迭代次数（用于ReAct循环）
    - max_iterations: 最大迭代次数（防止无限循环）
    - messages: 消息历史（使用operator.add追加，不是替换）
    - tool_calls: 工具调用记录
    - approval_required: 是否需要人工审批
    - approval_status: 审批状态（pending/approved/rejected）
    - approval_reason: 审批原因列表
    - cities: 需要查询的城市列表（用于并行执行）
    - city_results: 各城市的查询结果（用于并行聚合）
    """

    # 用户输入
    query: str
    rewritten_query: Optional[str]

    # RAG相关
    documents: List[Document]

    # 回答生成
    answer: Optional[str]

    # ReAct循环控制
    iteration: int
    max_iterations: int

    # 消息历史（使用Annotated + operator.add实现追加）
    messages: Annotated[List[BaseMessage], operator.add]

    # 工具调用
    tool_calls: List[dict]

    # Human-in-the-Loop审批
    approval_required: bool
    approval_status: Optional[Literal["pending", "approved", "rejected"]]
    approval_reason: List[str]

    # 并行执行（T1.5）
    cities: Optional[List[str]]
    city_results: Optional[dict]


def create_initial_state(query: str, max_iterations: int = 3) -> TravelAgentState:
    """创建初始状态"""
    return TravelAgentState(
        query=query,
        rewritten_query=None,
        documents=[],
        answer=None,
        iteration=0,
        max_iterations=max_iterations,
        messages=[],
        tool_calls=[],
        approval_required=False,
        approval_status=None,
        approval_reason=[],
        cities=None,
        city_results=None
    )
