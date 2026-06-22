"""
T1.5 流式输出图：基于checkpoint_graph实现streaming
核心：使用 graph.stream() 实时返回每个节点的执行结果
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


def create_streaming_graph():
    """创建支持流式输出的ReAct图"""
    workflow = StateGraph(TravelAgentState)
    workflow.add_node("rewrite", rewrite_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("answer", answer_node)
    workflow.set_entry_point("rewrite")
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("retrieve", "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": "answer"})
    workflow.add_edge("tools", "agent")
    workflow.add_edge("answer", END)
    return workflow.compile(checkpointer=MemorySaver())


def run_streaming(query: str, thread_id: str = "stream-001", max_iterations: int = 3):
    """流式执行图，实时返回每个节点的输出"""
    from ..state import create_initial_state
    graph = create_streaming_graph()
    initial_state = create_initial_state(query, max_iterations=max_iterations)
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n[STREAMING] Query: {query}")
    print("-" * 60)

    for chunk in graph.stream(initial_state, config):
        for node_name, state_update in chunk.items():
            print(f"\n[NODE] {node_name}")
            if "documents" in state_update:
                print(f"  - Documents: {len(state_update['documents'])}")
            if "answer" in state_update:
                print(f"  - Answer ready")
            yield (node_name, state_update)

    print("-" * 60)
    print("[STREAMING] Complete\n")
