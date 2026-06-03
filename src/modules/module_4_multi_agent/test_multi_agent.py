"""
Multi-Agent Orchestration Tests
Test the complete multi-agent system with various scenarios
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from modules.module_4_multi_agent import (
    MultiAgentGraph,
    SupervisorAgent,
    PolicyWorkerAgent,
    WeatherWorkerAgent,
    ItineraryWorkerAgent,
    create_initial_state
)
from models.llm import get_llm
from tools.weather_tool import WeatherTool
import time


def test_single_agent_query():
    """Test query that requires only one agent"""
    print("\n" + "="*80)
    print("Test 1: Single Agent Query (Weather Only)")
    print("="*80)

    llm = get_llm(temperature=0.3)

    # Initialize agents
    supervisor = SupervisorAgent(llm)
    policy_agent = PolicyWorkerAgent(llm)
    weather_agent = WeatherWorkerAgent(llm, WeatherTool())
    itinerary_agent = ItineraryWorkerAgent(llm)

    # Create graph
    graph = MultiAgentGraph(
        supervisor_agent=supervisor,
        policy_agent=policy_agent,
        weather_agent=weather_agent,
        itinerary_agent=itinerary_agent,
        max_iterations=5
    )

    # Test query
    query = "北京今天天气怎么样？"
    print(f"\nQuery: {query}")

    start_time = time.time()
    result = graph.invoke({"query": query})
    elapsed = time.time() - start_time

    print(f"\n{'='*80}")
    print("Execution Trace:")
    print(f"{'='*80}")
    for msg in result["messages"]:
        print(f"[{msg['agent']}] {msg['message'][:100]}...")

    print(f"\n{'='*80}")
    print("Final Answer:")
    print(f"{'='*80}")
    print(result["final_answer"])

    print(f"\nExecution time: {elapsed:.2f}s")
    print(f"Iterations: {result['iteration_count']}")

    return result


def test_multi_agent_query():
    """Test query that requires multiple agents"""
    print("\n" + "="*80)
    print("Test 2: Multi-Agent Query (Weather + Policy + Itinerary)")
    print("="*80)

    llm = get_llm(temperature=0.3)

    # Initialize agents
    supervisor = SupervisorAgent(llm)
    policy_agent = PolicyWorkerAgent(llm)
    weather_agent = WeatherWorkerAgent(llm, WeatherTool())
    itinerary_agent = ItineraryWorkerAgent(llm)

    # Create graph
    graph = MultiAgentGraph(
        supervisor_agent=supervisor,
        policy_agent=policy_agent,
        weather_agent=weather_agent,
        itinerary_agent=itinerary_agent,
        max_iterations=5
    )

    # Test query
    query = "我要去杭州出差3天，帮我查一下天气，推荐符合公司标准的酒店"
    print(f"\nQuery: {query}")

    start_time = time.time()
    result = graph.invoke({"query": query})
    elapsed = time.time() - start_time

    print(f"\n{'='*80}")
    print("Execution Trace:")
    print(f"{'='*80}")
    for msg in result["messages"]:
        agent = msg['agent']
        message = msg['message']
        if 'final_answer' in msg:
            print(f"[{agent}] Task completed")
        else:
            print(f"[{agent}] {message[:80]}...")

    print(f"\n{'='*80}")
    print("Final Answer:")
    print(f"{'='*80}")
    print(result["final_answer"])

    print(f"\nExecution time: {elapsed:.2f}s")
    print(f"Iterations: {result['iteration_count']}")
    print(f"Agents involved: {list(result['results'].keys())}")

    return result


def test_policy_only_query():
    """Test query that requires only policy agent"""
    print("\n" + "="*80)
    print("Test 3: Policy-Only Query")
    print("="*80)

    llm = get_llm(temperature=0.3)

    # Initialize agents
    supervisor = SupervisorAgent(llm)
    policy_agent = PolicyWorkerAgent(llm)
    weather_agent = WeatherWorkerAgent(llm, WeatherTool())
    itinerary_agent = ItineraryWorkerAgent(llm)

    # Create graph
    graph = MultiAgentGraph(
        supervisor_agent=supervisor,
        policy_agent=policy_agent,
        weather_agent=weather_agent,
        itinerary_agent=itinerary_agent,
        max_iterations=5
    )

    # Test query
    query = "公司的差旅住宿标准是什么？"
    print(f"\nQuery: {query}")

    start_time = time.time()
    result = graph.invoke({"query": query})
    elapsed = time.time() - start_time

    print(f"\n{'='*80}")
    print("Final Answer:")
    print(f"{'='*80}")
    print(result["final_answer"])

    print(f"\nExecution time: {elapsed:.2f}s")
    print(f"Iterations: {result['iteration_count']}")

    return result


def test_weather_comparison():
    """Test query that compares weather in multiple cities"""
    print("\n" + "="*80)
    print("Test 4: Weather Comparison")
    print("="*80)

    llm = get_llm(temperature=0.3)

    # Initialize agents
    supervisor = SupervisorAgent(llm)
    policy_agent = PolicyWorkerAgent(llm)
    weather_agent = WeatherWorkerAgent(llm, WeatherTool())
    itinerary_agent = ItineraryWorkerAgent(llm)

    # Create graph
    graph = MultiAgentGraph(
        supervisor_agent=supervisor,
        policy_agent=policy_agent,
        weather_agent=weather_agent,
        itinerary_agent=itinerary_agent,
        max_iterations=5
    )

    # Test query
    query = "对比一下北京和上海的天气"
    print(f"\nQuery: {query}")

    start_time = time.time()
    result = graph.invoke({"query": query})
    elapsed = time.time() - start_time

    print(f"\n{'='*80}")
    print("Final Answer:")
    print(f"{'='*80}")
    print(result["final_answer"])

    print(f"\nExecution time: {elapsed:.2f}s")

    return result


def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*80)
    print("MULTI-AGENT ORCHESTRATION TEST SUITE")
    print("="*80)

    try:
        # Test 1: Single agent
        test_single_agent_query()

        # Test 2: Multiple agents
        test_multi_agent_query()

        # Test 3: Policy only
        test_policy_only_query()

        # Test 4: Weather comparison
        test_weather_comparison()

        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
