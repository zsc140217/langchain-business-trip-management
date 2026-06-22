"""
带Human-in-the-Loop审批的ReAct图
T1.4核心实现
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from ..state import TravelAgentState
from ..nodes.rewrite_node import rewrite_node
from ..nodes.retrieve_node import retrieve_node
from ..nodes.check_approval_node import check_approval_node
from ..nodes.approval_node import approval_node
from ..nodes.process_approval_node import process_approval_node
from ..nodes.agent_node import agent_node
from ..nodes.tools_node import tools_node
from ..nodes.answer_node import answer_node
from ..utils.conditions import should_continue, needs_approval, after_approval


def create_approval_graph():
    """创建带审批的ReAct图"""
    workflow = StateGraph(TravelAgentState)

    workflow.add_node("rewrite", rewrite_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("check_approval", check_approval_node)
    workflow.add_node("approval", approval_node)
    workflow.add_node("process_approval", process_approval_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("answer", answer_node)

    workflow.set_entry_point("rewrite")
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("retrieve", "check_approval")

    workflow.add_conditional_edges("check_approval", needs_approval, {"approval": "approval", "agent": "agent"})
    workflow.add_edge("approval", "process_approval")
    workflow.add_conditional_edges("process_approval", after_approval, {"agent": "agent", "end": "answer"})
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": "answer"})
    workflow.add_edge("tools", "agent")
    workflow.add_edge("answer", END)

    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)
