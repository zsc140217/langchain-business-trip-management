"""
带Checkpointing的ReAct图：支持状态持久化和恢复
T1.3核心实现

Checkpointing功能：
1. 状态持久化：每个节点执行后自动保存状态
2. 断点恢复：可以从任意checkpoint恢复执行
3. 会话管理：通过thread_id隔离不同会话
4. 时间旅行：可以查看历史checkpoint
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from ..state import TravelAgentState
from ..nodes.rewrite_node import rewrite_node
from ..nodes.retrieve_node import retrieve_node
from ..nodes.agent_node import agent_node
from ..nodes.tools_node import tools_node
from ..nodes.answer_node import answer_node
from ..utils.conditions import should_continue
from pathlib import Path
from typing import Optional


def create_checkpoint_graph(checkpointer_type: str = "memory"):
    """创建带Checkpointing的ReAct图"""
    print(f"[+] Creating ReAct Graph with {checkpointer_type.upper()} Checkpointing...")

    workflow = StateGraph(TravelAgentState)

    # 添加节点
    workflow.add_node("rewrite", rewrite_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("answer", answer_node)

    # 添加边
    workflow.set_entry_point("rewrite")
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("retrieve", "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": "answer"})
    workflow.add_edge("tools", "agent")
    workflow.add_edge("answer", END)

    # 创建Checkpointer
    if checkpointer_type == "memory":
        checkpointer = MemorySaver()
        print("[OK] Using MemorySaver (in-memory)")
    else:
        # SQLite需要额外安装: pip install langgraph-checkpoint-sqlite
        raise ValueError(f"Unsupported: {checkpointer_type}. Only 'memory' is available without extra dependencies.")

    graph = workflow.compile(checkpointer=checkpointer)
    print("[OK] Graph with Checkpointing Created!")
    return graph


def run_checkpoint_graph(query: str, thread_id: str, max_iterations: int = 3, checkpointer_type: str = "memory"):
    """运行带Checkpointing的ReAct图"""
    from ..state import create_initial_state

    graph = create_checkpoint_graph(checkpointer_type)
    initial_state = create_initial_state(query, max_iterations=max_iterations)

    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n{'='*60}")
    print(f"[RUN] Query: {query} | Thread: {thread_id}")
    print(f"{'='*60}\n")

    final_state = graph.invoke(initial_state, config)

    print(f"\n{'='*60}")
    print(f"[OK] Complete | Iterations: {final_state.get('iteration', 0)}")
    print(f"{'='*60}\n")

    return final_state


def get_checkpoint_history(graph, thread_id: str):
    """获取checkpoint历史"""
    config = {"configurable": {"thread_id": thread_id}}
    checkpoints = []
    for cp in graph.get_state_history(config):
        checkpoints.append({
            "checkpoint_id": cp.config["configurable"]["checkpoint_id"],
            "step": cp.metadata.get("step", -1),
        })
    return checkpoints


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("Testing Checkpointing...\n")
    result = run_checkpoint_graph("查询北京天气", "test-001", checkpointer_type="memory")
    print(f"\nAnswer: {result.get('answer', 'N/A')}")
