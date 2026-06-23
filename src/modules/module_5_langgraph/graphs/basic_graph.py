"""
基础图：T1.1 StateGraph基础架构
实现最简单的 retrieve → answer 流程
"""
from langgraph.graph import StateGraph, END
from ..state import TravelAgentState
from ..nodes.retrieve_node import retrieve_node
from ..nodes.answer_node import answer_node


def create_basic_graph():
    """
    创建基础RAG图

    流程：START → retrieve → answer → END

    这是最简单的LangGraph应用：
    1. 用户输入查询
    2. 检索相关文档
    3. 生成答案
    4. 结束

    Returns:
        编译后的图
    """
    print("[INFO] 创建基础RAG图...")

    # 创建StateGraph
    workflow = StateGraph(TravelAgentState)

    # 添加节点
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("answer", answer_node)

    # 添加边（定义执行顺序）
    workflow.set_entry_point("retrieve")  # 从retrieve开始
    workflow.add_edge("retrieve", "answer")  # retrieve完成后执行answer
    workflow.add_edge("answer", END)  # answer完成后结束

    # 编译图
    graph = workflow.compile()

    print("[SUCCESS] 基础图创建完成！")
    print("\n流程：START → retrieve → answer → END")

    return graph


def run_basic_graph(query: str):
    """
    运行基础图的便捷函数

    Args:
        query: 用户查询

    Returns:
        最终状态
    """
    from ..state import create_initial_state

    # 创建图
    graph = create_basic_graph()

    # 创建初始状态
    initial_state = create_initial_state(query)

    print(f"\n{'='*60}")
    print(f"[START] 开始执行基础图")
    print(f"查询：{query}")
    print(f"{'='*60}\n")

    # 执行图
    final_state = graph.invoke(initial_state)

    print(f"\n{'='*60}")
    print(f"[DONE] 执行完成")
    print(f"{'='*60}\n")

    return final_state


# 测试代码
if __name__ == "__main__":
    """测试基础图"""
    print("测试基础RAG图...\n")

    # 测试查询
    query = "上海出差住宿标准是多少？"

    try:
        # 运行图
        result = run_basic_graph(query)

        # 打印结果
        print("最终答案：")
        print("-" * 60)
        print(result.get("answer", "未生成答案"))
        print("-" * 60)

        print(f"\n状态信息：")
        print(f"  检索文档数：{len(result.get('documents', []))}")
        print(f"  迭代次数：{result.get('iteration', 0)}")

        print("\n[SUCCESS] 基础图测试成功！")

    except Exception as e:
        print(f"\n[ERROR] 测试失败：{e}")
        import traceback
        traceback.print_exc()
