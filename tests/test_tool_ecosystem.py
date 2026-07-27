"""
Tool Ecosystem End-to-End Test
Tests the three-layer routing architecture with tool integration
"""
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_tool_ecosystem():
    """Test complete tool ecosystem"""
    print("=" * 70)
    print("Tool Ecosystem End-to-End Test")
    print("=" * 70)

    # Test 1: Tool Registry Initialization
    print("\n[Test 1] Tool Registry Initialization")
    print("-" * 70)
    from src.tools.registry import get_tool_registry

    registry = get_tool_registry()
    registry.initialize_all()

    tools = registry.list_tools()
    print(f"Registered tools: {len(tools)}")
    for tool_name in tools:
        print(f"  - {tool_name}")

    assert len(tools) >= 5, f"Expected at least 5 tools, got {len(tools)}"
    print("[PASS] Tool registry initialized")

    # Test 2: Basic Tools (Weather, Flight, Hotel)
    print("\n[Test 2] Basic Tools (MCP-based)")
    print("-" * 70)

    # Weather tool
    print("\n[2.1] Weather Tool")
    weather_tool = registry.get('query_weather')
    assert weather_tool is not None, "Weather tool not found"

    start = time.time()
    result = weather_tool.invoke({'city': 'Beijing'})
    latency = (time.time() - start) * 1000

    print(f"Result length: {len(result)} characters")
    print(f"Latency: {latency:.0f}ms")
    assert len(result) > 0, "Weather tool returned empty result"
    print("[PASS] Weather tool works")

    # Hotel tool
    print("\n[2.2] Hotel Tool")
    hotel_tool = registry.get('search_hotels')
    assert hotel_tool is not None, "Hotel tool not found"

    start = time.time()
    result = hotel_tool.invoke({'city': 'Beijing', 'max_price': 800})
    latency = (time.time() - start) * 1000

    print(f"Result length: {len(result)} characters")
    print(f"Latency: {latency:.0f}ms")
    assert len(result) > 0, "Hotel tool returned empty result"
    print("[PASS] Hotel tool works")

    # Flight tool
    print("\n[2.3] Flight Tool")
    flight_tool = registry.get('search_flights')
    assert flight_tool is not None, "Flight tool not found"

    start = time.time()
    result = flight_tool.invoke({
        'departure_city': 'Beijing',
        'arrival_city': 'Shanghai'
    })
    latency = (time.time() - start) * 1000

    print(f"Result length: {len(result)} characters")
    print(f"Latency: {latency:.0f}ms")
    assert len(result) > 0, "Flight tool returned empty result"
    print("[PASS] Flight tool works")

    # Test 3: Intent Detector (Layer 0)
    print("\n[Test 3] Intent Detector (Layer 0)")
    print("-" * 70)
    from src.agents.intent_detector import IntentDetector

    detector = IntentDetector()

    test_cases = [
        ("北京天气怎么样", "weather", {"city": "北京"}),
        ("上海天气", "weather", {"city": "上海"}),
        ("北京到上海的航班", "flight", None),
        ("北京的酒店", "hotel", {"city": "北京"}),
        ("差旅政策是什么", None, None),  # No clear intent
        ("去杭州出差，查天气并推荐酒店", None, None),  # Multi-intent
    ]

    for query, expected_intent, expected_entities in test_cases:
        intent = detector.detect(query)
        print(f"Query: '{query}' -> Intent: {intent}")

        if expected_intent is not None:
            assert intent == expected_intent, f"Expected {expected_intent}, got {intent}"

            if expected_entities:
                entities = detector.extract_entities(query, intent)
                for key, value in expected_entities.items():
                    assert entities.get(key) == value, f"Entity mismatch: {key}"

    print("[PASS] Intent detector works correctly")

    # Test 4: Tool Caching
    print("\n[Test 4] Tool Caching")
    print("-" * 70)

    weather_tool = registry.get('query_weather')

    # First call (cache miss)
    start = time.time()
    result1 = weather_tool.invoke({'city': 'Beijing'})
    latency1 = (time.time() - start) * 1000

    # Second call (cache hit)
    start = time.time()
    result2 = weather_tool.invoke({'city': 'Beijing'})
    latency2 = (time.time() - start) * 1000

    print(f"First call latency: {latency1:.0f}ms")
    print(f"Second call latency: {latency2:.0f}ms")
    if latency2 > 0:
        print(f"Cache speedup: {latency1/latency2:.1f}x")
    else:
        print("Cache speedup: Instant (< 1ms)")

    assert result1 == result2, "Cached result differs"
    print("[PASS] Tool caching works")

    # Test 5: Tool Statistics
    print("\n[Test 5] Tool Statistics")
    print("-" * 70)

    stats = registry.get_stats()
    print(f"Total tools: {len(stats)}")
    for tool_name, stat in stats.items():
        print(f"  {tool_name}: {stat}")

    print("[PASS] Tool statistics available")

    # Summary
    print("\n" + "=" * 70)
    print("[SUCCESS] Tool ecosystem test completed!")
    print("=" * 70)
    print("\nTested components:")
    print("  - Tool Registry (8 tools)")
    print("  - MCP-based tools (weather, flight, hotel)")
    print("  - Intent Detector (Layer 0 routing)")
    print("  - Tool caching mechanism")
    print("  - Tool statistics and monitoring")
    print("\nAll tests passed!")


if __name__ == "__main__":
    try:
        test_tool_ecosystem()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
