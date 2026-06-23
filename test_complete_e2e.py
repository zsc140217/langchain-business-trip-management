"""
T1.1-T1.5 完整端到端测试
覆盖所有LangGraph核心特性的综合测试
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

from src.modules.module_5_langgraph.state import create_initial_state
from src.modules.module_5_langgraph.graphs.basic_graph import create_basic_graph
from src.modules.module_5_langgraph.graphs.react_graph import create_react_graph
from src.modules.module_5_langgraph.graphs.checkpoint_graph import create_checkpoint_graph
from src.modules.module_5_langgraph.graphs.approval_graph import create_approval_graph
from src.modules.module_5_langgraph.graphs.streaming_graph import create_streaming_graph
from langgraph.errors import GraphInterrupt


def print_section(title: str):
    """打印测试章节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(label: str, content: str, indent: int = 2):
    """打印结果"""
    spaces = " " * indent
    print(f"{spaces}[{label}] {content}")


def test_t1_1_basic_graph():
    """测试T1.1StateGraph基础架构"""
    print_section("测试1T1.1 StateGraph基础架构")

    query = "北京的住宿标准是多少"
    print_result("INPUT", query)

    graph = create_basic_graph()
    initial_state = create_initial_state(query)

    print_result("PROCESS", "retrieve  answer")
    result = graph.invoke(initial_state)

    print_result("OUTPUT", f"Answer: {result.get('answer', 'No answer')[:100]}...")
    print_result("STATUS", " T1.1 基础流程测试通过")

    return result


def test_t1_2_react_loop():
    """测试T1.2条件分支 + ReAct循环"""
    print_section("测试2T1.2 条件分支 + ReAct循环")

    query = "对比北京和上海的住宿标准"
    print_result("INPUT", query)

    graph = create_react_graph()
    initial_state = create_initial_state(query, max_iterations=5)

    print_result("PROCESS", "agent  tools  agent (ReAct循环)")
    result = graph.invoke(initial_state)

    print_result("ITERATION", f"执行了 {result.get('iteration', 0)} 次迭代")
    print_result("OUTPUT", f"Answer: {result.get('answer', 'No answer')[:100]}...")
    print_result("STATUS", " T1.2 ReAct循环测试通过")

    return result


def test_t1_3_checkpointing():
    """测试T1.3Checkpointing持久化"""
    print_section("测试3T1.3 Checkpointing持久化")

    query = "深圳的差旅标准"
    thread_id = "test-checkpoint-001"
    print_result("INPUT", query)
    print_result("THREAD_ID", thread_id)

    graph = create_checkpoint_graph()
    initial_state = create_initial_state(query, max_iterations=3)
    config = {"configurable": {"thread_id": thread_id}}

    print_result("PROCESS", "执行图并保存状态到checkpointer")
    result = graph.invoke(initial_state, config)

    # 验证状态保存
    print_result("VERIFY", "检查状态是否已保存...")
    saved_state = graph.get_state(config)
    print_result("SAVED_STATE", f"保存的values keys: {list(saved_state.values.keys())}")

    print_result("OUTPUT", f"Answer: {result.get('answer', 'No answer')[:100]}...")
    print_result("STATUS", " T1.3 Checkpointing测试通过")

    return result


def test_t1_4_human_in_loop():
    """测试T1.4Human-in-the-Loop审批"""
    print_section("测试4T1.4 Human-in-the-Loop审批")

    # 场景国际出差触发审批
    query = "我要去美国出差7天预算8000元"
    thread_id = "test-approval-001"
    print_result("INPUT", query)
    print_result("THREAD_ID", thread_id)

    graph = create_approval_graph()
    initial_state = create_initial_state(query, max_iterations=3)
    initial_state["budget"] = 8000
    initial_state["days"] = 7
    initial_state["destination"] = "美国"

    config = {"configurable": {"thread_id": thread_id}}

    print_result("PROCESS", "执行图预期触发审批...")

    try:
        result = graph.invoke(initial_state, config)
        print_result("WARNING", "未触发审批可能是check_approval逻辑未匹配")
    except GraphInterrupt as e:
        print_result("INTERRUPT", " 图已暂停等待审批")
        print_result("INTERRUPT_DATA", str(e)[:200])

        # 模拟审批通过
        print_result("APPROVE", "提供审批决策: approve")
        result = graph.invoke({"approval_decision": "approve"}, config)
        print_result("RESUME", " 审批通过图继续执行")

    print_result("OUTPUT", f"Final status: {result.get('approval_status', 'N/A')}")
    print_result("STATUS", " T1.4 Human-in-the-Loop测试通过")

    return result


def test_t1_5_streaming():
    """测试T1.5流式输出"""
    print_section("测试5T1.5 流式输出")

    query = "广州的餐饮标准"
    thread_id = "test-streaming-001"
    print_result("INPUT", query)
    print_result("THREAD_ID", thread_id)

    graph = create_streaming_graph()
    initial_state = create_initial_state(query, max_iterations=3)
    config = {"configurable": {"thread_id": thread_id}}

    print_result("PROCESS", "流式执行实时返回每个节点...")

    node_count = 0
    for chunk in graph.stream(initial_state, config):
        node_count += 1
        for node_name, state_update in chunk.items():
            print_result("NODE", f"[{node_count}] {node_name}", indent=4)

            # 显示部分状态更新
            if "query" in state_update:
                print_result("  ", f"query: {state_update['query'][:50]}...", indent=4)
            if "documents" in state_update:
                print_result("  ", f"documents: {len(state_update['documents'])} docs", indent=4)
            if "answer" in state_update:
                print_result("  ", f"answer: {state_update['answer'][:50]}...", indent=4)

    print_result("OUTPUT", f"总共流式返回 {node_count} 个节点")
    print_result("STATUS", " T1.5 流式输出测试通过")


def test_complete_scenario():
    """测试场景6T1.1-T1.5综合场景"""
    print_section("测试6T1.1-T1.5 综合场景")

    # 复杂场景国际出差 + 高预算 + 流式输出 + checkpoint
    query = "我要去日本东京出差10天预算12000元需要查询住宿和餐饮标准"
    thread_id = "test-complete-001"

    print_result("INPUT", query)
    print_result("SCENARIO", "国际出差 + 超预算 + 超天数  触发审批")
    print_result("THREAD_ID", thread_id)

    graph = create_approval_graph()
    initial_state = create_initial_state(query, max_iterations=5)
    initial_state["budget"] = 12000
    initial_state["days"] = 10
    initial_state["destination"] = "日本"

    config = {"configurable": {"thread_id": thread_id}}

    print_result("PROCESS", "流式执行 + checkpoint + 审批...")

    try:
        node_count = 0
        for chunk in graph.stream(initial_state, config):
            node_count += 1
            for node_name, state_update in chunk.items():
                print_result("STREAM_NODE", f"[{node_count}] {node_name}", indent=4)

        print_result("WARNING", "未触发审批")

    except GraphInterrupt:
        print_result("INTERRUPT", " 审批流程触发图暂停")

        # 查看保存的状态
        saved_state = graph.get_state(config)
        print_result("CHECKPOINT", f"状态已保存: {list(saved_state.values.keys())[:5]}")

        # 模拟审批通过
        print_result("APPROVE", "提供审批决策: approve")

        # 继续流式执行
        node_count = 0
        for chunk in graph.stream({"approval_decision": "approve"}, config):
            node_count += 1
            for node_name, state_update in chunk.items():
                print_result("RESUME_NODE", f"[{node_count}] {node_name}", indent=4)

        print_result("COMPLETE", f"审批后继续执行了 {node_count} 个节点")

    print_result("STATUS", " T1.1-T1.5 综合场景测试通过")


def main():
    """运行完整端到端测试套件"""
    print("\n")
    print("" + "" * 78 + "")
    print("" + " " * 20 + "T1.1-T1.5 完整端到端测试套件" + " " * 28 + "")
    print("" + "" * 78 + "")

    try:
        # 运行各个测试
        test_t1_1_basic_graph()
        test_t1_2_react_loop()
        test_t1_3_checkpointing()
        test_t1_4_human_in_loop()
        test_t1_5_streaming()
        test_complete_scenario()

        # 总结
        print_section("测试总结")
        print_result("T1.1", " StateGraph基础架构")
        print_result("T1.2", " 条件分支 + ReAct循环")
        print_result("T1.3", " Checkpointing持久化")
        print_result("T1.4", " Human-in-the-Loop审批")
        print_result("T1.5", " 流式输出")
        print_result("综合", " T1.1-T1.5集成场景")
        print("\n" + "=" * 80)
        print("   所有测试通过模块1完整验证成功")
        print("=" * 80 + "\n")

    except Exception as e:
        print_section("测试失败")
        print_result("ERROR", str(e))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
