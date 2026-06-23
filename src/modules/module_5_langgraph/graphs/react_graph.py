"""
ReAct图：条件分支 + 循环
T1.2核心实现
"""
from langgraph.graph import StateGraph, END
from ..state import TravelAgentState
from ..nodes.rewrite_node import rewrite_node
from ..nodes.retrieve_node import retrieve_node
from ..nodes.agent_node import agent_node
from ..nodes.tools_node import tools_node
from ..nodes.answer_node import answer_node
from ..utils.conditions import should_continue


def create_react_graph():
    """
    创建ReAct图：支持条件分支和循环
    
    流程：
    START → rewrite → retrieve → agent → should_continue
                                    ↓           ↓
                                answer ←─── tools
                                    ↓           ↓
                                   END    (loop back)
    
    关键特性：
    1. 条件边：agent后根据tool_calls决定路由
    2. 循环：tools → agent 形成ReAct循环
    3. 循环控制：max_iterations防止无限循环
    
    Returns:
        编译后的图
    """
    print("[+] Creating ReAct Graph (Conditional Edges + Loop)...")

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

    # 关键：条件边（T1.2核心）
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",   # 有tool_calls → 执行工具
            "end": "answer"     # 无tool_calls → 生成答案
        }
    )

    # 关键：循环边
    workflow.add_edge("tools", "agent")  # 工具执行后回到agent

    # 结束
    workflow.add_edge("answer", END)

    graph = workflow.compile()

    print("[OK] ReAct Graph Created!")
    print("\nFlow Diagram:")
    print("  START -> rewrite -> retrieve -> agent")
    print("                              |     |")
    print("                          answer <- tools")
    print("                              |     |")
    print("                            END   (loop)")
    
    return graph


def run_react_graph(query: str, max_iterations: int = 3):
    """
    运行ReAct图的便捷函数
    
    Args:
        query: 用户查询
        max_iterations: 最大迭代次数
        
    Returns:
        最终状态
    """
    from ..state import create_initial_state
    
    graph = create_react_graph()
    initial_state = create_initial_state(query, max_iterations=max_iterations)
    
    print(f"\n{'='*60}")
    print(f"[RUN] ReAct Graph")
    print(f"Query: {query}")
    print(f"Max Iterations: {max_iterations}")
    print(f"{'='*60}\n")

    final_state = graph.invoke(initial_state)

    print(f"\n{'='*60}")
    print(f"[OK] Execution Complete")
    print(f"Actual Iterations: {final_state.get('iteration', 0)}")
    print(f"{'='*60}\n")
    
    return final_state


# 测试代码
if __name__ == "__main__":
    print("Testing ReAct Graph...\n")

    query = "上海和北京的住宿标准对比"

    try:
        result = run_react_graph(query, max_iterations=3)

        print("Final Answer:")
        print("-" * 60)
        print(result.get("answer", "No answer generated"))
        print("-" * 60)

        print(f"\nIterations: {result.get('iteration', 0)}")
        print(f"Documents: {len(result.get('documents', []))}")

        print("\n[OK] ReAct Graph Test Passed!")

    except Exception as e:
        print(f"\n[ERROR] Test Failed: {e}")
        import traceback
        traceback.print_exc()
