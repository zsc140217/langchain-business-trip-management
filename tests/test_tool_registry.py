"""
测试工具注册表
验证所有工具是否正常注册和工作
"""
from src.tools.registry import get_tool_registry


def test_tool_registry():
    """测试工具注册表"""
    print("=" * 60)
    print("Test Tool Registry")
    print("=" * 60)

    # 初始化工具注册表
    registry = get_tool_registry()
    registry.initialize_all()

    # 测试1：检查工具数量
    print("\n[Test 1] Tool Count Check")
    print("-" * 60)
    tools = registry.list_tools()
    print(f"Registered tools: {len(tools)}")
    print(f"Expected: 8")
    assert len(tools) == 8, f"Tool count error, expected 8, got {len(tools)}"
    print("[PASS] Tool count correct")

    # 测试2：检查工具名称
    print("\n[Test 2] Tool Name Check")
    print("-" * 60)
    expected_tools = [
        'search_policy',           # 政策检索
        'query_graph',             # 图谱查询
        'query_weather',           # 天气查询
        'search_hotels',           # 酒店搜索
        'search_flights',          # 航班搜索
        'check_approval_status',   # 审批状态查询
        'cancel_approval',         # 取消审批
        'query_memory'             # 记忆查询
    ]
    for tool_name in expected_tools:
        assert tool_name in tools, f"Tool {tool_name} not registered"
        print(f"[PASS] {tool_name}")

    # 测试3：天气工具
    print("\n[Test 3] Weather Tool Test")
    print("-" * 60)
    weather_tool = registry.get('query_weather')
    assert weather_tool is not None, "Weather tool not found"
    result = weather_tool.invoke({'city': '北京'})
    assert len(result) > 20, "Weather tool result too short"
    assert '北京' in result, "City name not in result"
    print(f"[PASS] Weather tool works (result length: {len(result)})")

    # 测试4：酒店工具
    print("\n[Test 4] Hotel Tool Test")
    print("-" * 60)
    hotel_tool = registry.get('search_hotels')
    assert hotel_tool is not None, "Hotel tool not found"
    result = hotel_tool.invoke({'city': '北京', 'max_price': 800})
    assert len(result) > 50, "Hotel tool result too short"
    assert '北京' in result, "City name not in result"
    print(f"[PASS] Hotel tool works (result length: {len(result)})")

    # 测试5：航班工具
    print("\n[Test 5] Flight Tool Test")
    print("-" * 60)
    flight_tool = registry.get('search_flights')
    assert flight_tool is not None, "Flight tool not found"
    result = flight_tool.invoke({
        'departure_city': '北京',
        'arrival_city': '上海'
    })
    assert len(result) > 50, "Flight tool result too short"
    assert '北京' in result and '上海' in result, "City names not in result"
    print(f"[PASS] Flight tool works (result length: {len(result)})")

    # 测试6：政策检索工具
    print("\n[Test 6] Policy Search Tool Test")
    print("-" * 60)
    policy_tool = registry.get('search_policy')
    assert policy_tool is not None, "Policy search tool not found"
    result = policy_tool.invoke({'query': 'Beijing standard'})
    assert len(result) > 50, "Policy search tool result too short"
    print(f"[PASS] Policy search tool works (result length: {len(result)})")

    # 测试7：审批状态查询工具
    print("\n[Test 7] Approval Status Tool Test")
    print("-" * 60)
    approval_tool = registry.get('check_approval_status')
    assert approval_tool is not None, "Approval status tool not found"
    print("[PASS] Approval status tool registered")

    # 测试8：记忆查询工具
    print("\n[Test 8] Memory Query Tool Test")
    print("-" * 60)
    memory_tool = registry.get('query_memory')
    assert memory_tool is not None, "Memory query tool not found"
    print("[PASS] Memory query tool registered")

    # 测试9：工具统计
    print("\n[Test 9] Tool Statistics")
    print("-" * 60)
    stats = registry.get_stats()
    print(f"Statistics: {len(stats)} tools")
    for tool_name, stat in stats.items():
        print(f"  - {tool_name}: {stat}")

    print("\n" + "=" * 60)
    print("[SUCCESS] All tests passed! Tool registry works properly")
    print("=" * 60)


if __name__ == "__main__":
    test_tool_registry()
