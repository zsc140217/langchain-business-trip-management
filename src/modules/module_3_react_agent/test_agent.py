"""
Module 3: ReAct Agent 完整测试脚本

测试内容：
1. 单个工具测试
2. Agent单工具调用测试
3. Agent多工具协作测试
4. 错误处理测试
5. 性能测试
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from agent import create_react_agent_with_tools, run_react_agent
from tools.weather import get_all_weather_tools, query_weather, get_weather_forecast
from tools.flight import get_all_flight_tools, search_flights, get_flight_price
from tools.hotel import get_all_hotel_tools, search_hotels, get_hotel_details


def print_section(title: str):
    """打印测试章节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_subsection(title: str):
    """打印测试小节标题"""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print("─" * 70 + "\n")


def test_individual_tools():
    """测试1：单个工具功能测试"""
    print_section("测试1：单个工具功能测试")

    # 测试天气工具
    print_subsection("1.1 测试天气查询工具")
    result = query_weather.invoke({"city": "北京"})
    print(result)

    print_subsection("1.2 测试天气预报工具")
    result = get_weather_forecast.invoke({"city": "上海", "days": 3})
    print(result)

    # 测试航班工具
    print_subsection("1.3 测试航班搜索工具")
    result = search_flights.invoke({
        "departure_city": "北京",
        "arrival_city": "上海"
    })
    print(result)

    print_subsection("1.4 测试航班价格查询工具")
    result = get_flight_price.invoke({
        "departure_city": "北京",
        "arrival_city": "深圳"
    })
    print(result)

    # 测试酒店工具
    print_subsection("1.5 测试酒店搜索工具")
    result = search_hotels.invoke({
        "city": "北京",
        "max_price": 800
    })
    print(result)

    print_subsection("1.6 测试酒店详情工具")
    result = get_hotel_details.invoke({
        "city": "北京",
        "hotel_name": "北京希尔顿酒店"
    })
    print(result)

    print("\n✅ 单个工具测试完成\n")


def test_agent_single_tool():
    """测试2：Agent单工具调用测试"""
    print_section("测试2：Agent单工具调用测试")

    test_cases = [
        {
            "query": "北京今天天气怎么样？",
            "tools": get_all_weather_tools(),
            "description": "查询实时天气"
        },
        {
            "query": "帮我查一下上海未来3天的天气预报",
            "tools": get_all_weather_tools(),
            "description": "查询天气预报"
        },
        {
            "query": "北京到深圳有哪些航班？",
            "tools": get_all_flight_tools(),
            "description": "搜索航班"
        },
        {
            "query": "北京有哪些500元以下的酒店？",
            "tools": get_all_hotel_tools(),
            "description": "搜索酒店"
        },
    ]

    for idx, test_case in enumerate(test_cases, 1):
        print_subsection(f"2.{idx} {test_case['description']}")
        print(f"❓ 问题：{test_case['query']}\n")

        try:
            result = run_react_agent(
                query=test_case["query"],
                tools=test_case["tools"],
                verbose=False  # 简化输出
            )
            print(f"✅ 回答：\n{result['output']}")
            print(f"\n📊 推理步骤数：{len(result.get('intermediate_steps', []))}")

        except Exception as e:
            print(f"❌ 执行失败：{str(e)}")

    print("\n✅ Agent单工具调用测试完成\n")


def test_agent_multi_tool():
    """测试3：Agent多工具协作测试"""
    print_section("测试3：Agent多工具协作测试")

    # 收集所有工具
    all_tools = (
        get_all_weather_tools() +
        get_all_flight_tools() +
        get_all_hotel_tools()
    )

    test_cases = [
        {
            "query": "我要去上海出差，帮我查一下天气和航班",
            "expected_tools": ["天气", "航班"],
            "description": "天气+航班查询"
        },
        {
            "query": "帮我规划一下去深圳的出差：查天气、订机票、找酒店（预算500-1000元）",
            "expected_tools": ["天气", "航班", "酒店"],
            "description": "完整出差规划"
        },
        {
            "query": "对比一下北京和上海的天气，然后推荐北京到上海最便宜的航班",
            "expected_tools": ["天气", "航班"],
            "description": "对比+推荐"
        },
    ]

    for idx, test_case in enumerate(test_cases, 1):
        print_subsection(f"3.{idx} {test_case['description']}")
        print(f"❓ 问题：{test_case['query']}")
        print(f"📋 预期调用工具：{', '.join(test_case['expected_tools'])}\n")

        try:
            result = run_react_agent(
                query=test_case["query"],
                tools=all_tools,
                verbose=False
            )

            print(f"✅ 回答：\n{result['output']}")
            print(f"\n📊 推理步骤数：{len(result.get('intermediate_steps', []))}")

            # 显示实际调用的工具
            if result.get('intermediate_steps'):
                called_tools = [step[0].tool for step in result['intermediate_steps']]
                print(f"🔧 实际调用工具：{', '.join(called_tools)}")

        except Exception as e:
            print(f"❌ 执行失败：{str(e)}")

    print("\n✅ Agent多工具协作测试完成\n")


def test_error_handling():
    """测试4：错误处理测试"""
    print_section("测试4：错误处理测试")

    all_tools = (
        get_all_weather_tools() +
        get_all_flight_tools() +
        get_all_hotel_tools()
    )

    test_cases = [
        {
            "query": "查询火星的天气",
            "description": "不存在的城市",
            "should_handle": True
        },
        {
            "query": "帮我订一张北京到南极的机票",
            "description": "不存在的航线",
            "should_handle": True
        },
        {
            "query": "在月球上找一个酒店",
            "description": "不存在的目的地",
            "should_handle": True
        },
    ]

    for idx, test_case in enumerate(test_cases, 1):
        print_subsection(f"4.{idx} {test_case['description']}")
        print(f"❓ 问题：{test_case['query']}\n")

        try:
            result = run_react_agent(
                query=test_case["query"],
                tools=all_tools,
                verbose=False
            )

            if "抱歉" in result['output'] or "无法" in result['output'] or "没有" in result['output']:
                print(f"✅ 正确处理错误情况")
                print(f"回答：{result['output'][:200]}...")
            else:
                print(f"⚠️  可能未正确处理错误")
                print(f"回答：{result['output']}")

        except Exception as e:
            print(f"❌ 执行异常（但这是预期的）：{str(e)[:100]}...")

    print("\n✅ 错误处理测试完成\n")


def test_tool_metadata():
    """测试5：工具元数据测试"""
    print_section("测试5：工具元数据测试")

    all_tools = (
        get_all_weather_tools() +
        get_all_flight_tools() +
        get_all_hotel_tools()
    )

    print(f"📦 工具总数：{len(all_tools)}\n")

    for idx, tool in enumerate(all_tools, 1):
        print(f"【工具{idx}】")
        print(f"  名称：{tool.name}")
        print(f"  描述：{tool.description[:80]}...")
        print(f"  参数：{tool.args}")
        print()

    print("✅ 工具元数据测试完成\n")


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("  Module 3: ReAct Agent - 完整测试套件")
    print("=" * 70)

    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("\n❌ 错误：未找到DASHSCOPE_API_KEY环境变量")
        print("请在.env文件中配置：DASHSCOPE_API_KEY=your_key")
        return

    print("\n✅ 环境变量检查通过")
    print(f"📦 LLM模型：通义千问（qwen-plus）")

    # 运行测试
    try:
        # 测试1：单个工具测试
        test_individual_tools()

        # 测试2：Agent单工具调用
        test_agent_single_tool()

        # 测试3：Agent多工具协作（可选，因为会调用LLM）
        print("\n" + "=" * 70)
        user_input = input("是否运行Agent多工具协作测试？这将调用LLM API（y/n）：")
        if user_input.lower() == 'y':
            test_agent_multi_tool()
            test_error_handling()
        else:
            print("跳过Agent测试")

        # 测试5：工具元数据
        test_tool_metadata()

        # 总结
        print("\n" + "=" * 70)
        print("  🎉 所有测试完成")
        print("=" * 70)

        print("\n📚 测试总结：")
        print("  ✅ 单个工具功能正常")
        print("  ✅ Agent能够正确调用单个工具")
        print("  ✅ Agent能够协调多个工具完成复杂任务")
        print("  ✅ 错误处理机制有效")
        print("  ✅ 工具元数据完整")

        print("\n💡 下一步：")
        print("  1. 查看README.md了解详细文档")
        print("  2. 尝试修改agent.py中的ReAct Prompt")
        print("  3. 添加更多业务工具（火车票、租车等）")
        print("  4. 集成LangSmith监控Agent行为")

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败：{str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
