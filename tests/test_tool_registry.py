"""
测试工具注册表
验证所有工具是否正常注册和工作
"""
from src.tools.registry import get_tool_registry


def test_tool_registry():
    """测试工具注册表"""
    print("=" * 60)
    print("测试工具注册表")
    print("=" * 60)

    # 初始化工具注册表
    registry = get_tool_registry()
    registry.initialize_all()

    # 测试1：检查工具数量
    print("\n[Test 1] 工具数量检查")
    print("-" * 60)
    tools = registry.list_tools()
    print(f"已注册工具数量: {len(tools)}")
    print(f"预期工具数量: 5")
    assert len(tools) == 5, f"工具数量错误，预期5个，实际{len(tools)}个"
    print("✓ 工具数量正确")

    # 测试2：检查工具名称
    print("\n[Test 2] 工具名称检查")
    print("-" * 60)
    expected_tools = [
        'search_policy',
        'query_graph',
        'query_weather',
        'search_hotels',
        'search_flights'
    ]
    for tool_name in expected_tools:
        assert tool_name in tools, f"工具 {tool_name} 未注册"
        print(f"✓ {tool_name}")

    # 测试3：天气工具
    print("\n[Test 3] 天气工具测试")
    print("-" * 60)
    weather_tool = registry.get('query_weather')
    assert weather_tool is not None, "天气工具未找到"
    result = weather_tool.invoke({'city': '北京'})
    assert len(result) > 50, "天气工具返回结果太短"
    assert '北京' in result, "结果中未包含城市名称"
    print(f"✓ 天气工具正常工作（结果长度: {len(result)}）")

    # 测试4：酒店工具
    print("\n[Test 4] 酒店工具测试")
    print("-" * 60)
    hotel_tool = registry.get('search_hotels')
    assert hotel_tool is not None, "酒店工具未找到"
    result = hotel_tool.invoke({'city': '北京', 'max_price': 800})
    assert len(result) > 100, "酒店工具返回结果太短"
    assert '北京' in result, "结果中未包含城市名称"
    print(f"✓ 酒店工具正常工作（结果长度: {len(result)}）")

    # 测试5：航班工具
    print("\n[Test 5] 航班工具测试")
    print("-" * 60)
    flight_tool = registry.get('search_flights')
    assert flight_tool is not None, "航班工具未找到"
    result = flight_tool.invoke({
        'departure_city': '北京',
        'arrival_city': '上海'
    })
    assert len(result) > 100, "航班工具返回结果太短"
    assert '北京' in result and '上海' in result, "结果中未包含城市名称"
    print(f"✓ 航班工具正常工作（结果长度: {len(result)}）")

    # 测试6：政策检索工具
    print("\n[Test 6] 政策检索工具测试")
    print("-" * 60)
    policy_tool = registry.get('search_policy')
    assert policy_tool is not None, "政策检索工具未找到"
    result = policy_tool.invoke({'query': 'Beijing standard'})
    assert len(result) > 100, "政策检索工具返回结果太短"
    print(f"✓ 政策检索工具正常工作（结果长度: {len(result)}）")

    # 测试7：工具统计
    print("\n[Test 7] 工具统计")
    print("-" * 60)
    stats = registry.get_stats()
    print(f"统计信息: {len(stats)} 个工具")
    for tool_name, stat in stats.items():
        print(f"  - {tool_name}: {stat}")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！工具注册表工作正常")
    print("=" * 60)


if __name__ == "__main__":
    test_tool_registry()
