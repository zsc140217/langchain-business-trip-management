"""
Multi-Agent Orchestration Example
Demonstrates the complete multi-agent system with LangGraph

This example shows:
1. State Graph definition with supervisor-worker pattern
2. Conditional routing based on query analysis
3. Parallel and sequential agent execution
4. Result integration and final answer generation
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
    create_initial_state,
    extract_final_answer,
    get_execution_trace
)
from models.llm import get_llm
from tools.weather_tool import WeatherTool
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """
    Main example demonstrating multi-agent orchestration
    """
    print("="*80)
    print("Multi-Agent Orchestration with LangGraph")
    print("="*80)

    # Step 1: Initialize LLM
    print("\n[1] Initializing LLM...")
    llm = get_llm(temperature=0.3)
    print("✓ LLM initialized (qwen-plus)")

    # Step 2: Create worker agents
    print("\n[2] Creating worker agents...")

    # Policy agent (queries company policies)
    policy_agent = PolicyWorkerAgent(llm)
    print("✓ PolicyWorkerAgent created")

    # Weather agent (queries weather information)
    weather_tool = WeatherTool()
    weather_agent = WeatherWorkerAgent(llm, weather_tool)
    print("✓ WeatherWorkerAgent created")

    # Itinerary agent (plans trip itineraries)
    itinerary_agent = ItineraryWorkerAgent(llm)
    print("✓ ItineraryWorkerAgent created")

    # Step 3: Create supervisor agent
    print("\n[3] Creating supervisor agent...")
    supervisor = SupervisorAgent(llm, temperature=0.3)
    print("✓ SupervisorAgent created")
    print(f"  Available workers: {supervisor.get_available_workers()}")

    # Step 4: Build multi-agent graph
    print("\n[4] Building LangGraph StateGraph...")
    graph = MultiAgentGraph(
        supervisor_agent=supervisor,
        policy_agent=policy_agent,
        weather_agent=weather_agent,
        itinerary_agent=itinerary_agent,
        max_iterations=5
    )
    print("✓ Multi-agent graph compiled")

    # Step 5: Execute queries
    print("\n[5] Executing queries...")
    print("="*80)

    # Example 1: Simple weather query
    print("\n" + "-"*80)
    print("Example 1: Simple Weather Query")
    print("-"*80)

    query1 = "北京今天天气怎么样？"
    print(f"Query: {query1}")

    result1 = graph.invoke({"query": query1})

    print(f"\nExecution trace:")
    for i, msg in enumerate(get_execution_trace(result1), 1):
        print(f"  {i}. [{msg['agent']}] {msg['message'][:60]}...")

    print(f"\nFinal answer:\n{extract_final_answer(result1)}")
    print(f"\nIterations: {result1['iteration_count']}")

    # Example 2: Complex multi-agent query
    print("\n" + "-"*80)
    print("Example 2: Complex Multi-Agent Query")
    print("-"*80)

    query2 = "我要去杭州出差3天，帮我查询天气、公司住宿标准，并推荐行程安排"
    print(f"Query: {query2}")

    result2 = graph.invoke({"query": query2})

    print(f"\nExecution trace:")
    for i, msg in enumerate(get_execution_trace(result2), 1):
        print(f"  {i}. [{msg['agent']}] {msg['message'][:60]}...")

    print(f"\nAgents invoked: {list(result2['results'].keys())}")
    print(f"\nFinal answer:\n{extract_final_answer(result2)}")
    print(f"\nIterations: {result2['iteration_count']}")

    # Example 3: Policy-only query
    print("\n" + "-"*80)
    print("Example 3: Policy-Only Query")
    print("-"*80)

    query3 = "公司差旅的餐饮报销标准是多少？"
    print(f"Query: {query3}")

    result3 = graph.invoke({"query": query3})

    print(f"\nFinal answer:\n{extract_final_answer(result3)}")

    # Summary
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    print(f"✓ {len([query1, query2, query3])} queries executed successfully")
    print(f"✓ Total agents invoked: {len(set([r for res in [result1, result2, result3] for r in res['results'].keys()]))}")
    print(f"✓ Multi-agent orchestration working correctly")

    print("\n" + "="*80)
    print("Multi-Agent System Architecture")
    print("="*80)
    print("""
    User Query
        ↓
    Supervisor Agent (routing)
        ↓
    ┌───────────┬────────────┬─────────────┐
    ↓           ↓            ↓             ↓
Policy    Weather    Itinerary    (parallel/sequential)
Worker     Worker     Worker
    ↓           ↓            ↓
    └───────────┴────────────┴─────────────┘
                ↓
        Supervisor (integration)
                ↓
          Final Answer
    """)

    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
