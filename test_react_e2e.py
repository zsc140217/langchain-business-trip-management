"""
端到端测试：ReAct图 - 真实LLM + 真实工具调用
运行方式：python test_react_e2e.py
"""
# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from src.modules.module_5_langgraph.graphs.react_graph import run_react_graph


def test_weather_query():
    """测试天气查询（需要调用工具）"""
    print("="*60)
    print("测试1：天气查询（需要工具调用）")
    print("="*60)

    query = "查询北京今天的天气"

    try:
        result = run_react_graph(query, max_iterations=3)

        print("\n" + "="*60)
        print("测试结果")
        print("="*60)
        print(f"执行成功")
        print(f"迭代次数：{result.get('iteration', 0)}")
        print(f"消息数量：{len(result.get('messages', []))}")
        print(f"\n最终答案：")
        print("-"*60)
        print(result.get('answer', '未生成答案'))
        print("-"*60)

        # 检查是否真的调用了工具
        messages = result.get('messages', [])
        has_tool_message = any('ToolMessage' in str(type(msg)) for msg in messages)
        print(f"\n是否调用了工具：{'是' if has_tool_message else '否'}")

        return True

    except Exception as e:
        print(f"\n测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_query():
    """测试简单查询（可能不需要工具）"""
    print("\n" + "="*60)
    print("测试2：简单政策查询（可能不需要工具）")
    print("="*60)

    query = "北京的住宿标准是多少"

    try:
        result = run_react_graph(query, max_iterations=3)

        print("\n" + "="*60)
        print("测试结果")
        print("="*60)
        print(f"执行成功")
        print(f"迭代次数：{result.get('iteration', 0)}")
        print(f"消息数量：{len(result.get('messages', []))}")
        print(f"\n最终答案：")
        print("-"*60)
        print(result.get('answer', '未生成答案'))
        print("-"*60)

        return True

    except Exception as e:
        print(f"\n测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("ReAct图端到端测试开始\n")

    results = []

    # 测试1：需要工具调用
    results.append(("天气查询", test_weather_query()))

    # 测试2：简单查询
    results.append(("政策查询", test_simple_query()))

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    for name, success in results:
        status = "通过" if success else "失败"
        print(f"{name}: {status}")

    total = len(results)
    passed = sum(1 for _, success in results if success)
    print(f"\n总计：{passed}/{total} 通过")


if __name__ == "__main__":
    main()
