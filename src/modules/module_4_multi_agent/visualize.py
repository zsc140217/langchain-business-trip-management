"""
Graph Visualization
Generate visual representation of the multi-agent graph structure

Requires: pip install pygraphviz (optional for PNG export)
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
    ItineraryWorkerAgent
)
from models.llm import get_llm


def visualize_graph():
    """
    Generate graph visualization
    """
    print("="*80)
    print("Multi-Agent Graph Visualization")
    print("="*80)

    # Initialize components
    print("\n[1] Initializing agents...")
    llm = get_llm(temperature=0.3)

    supervisor = SupervisorAgent(llm)
    policy_agent = PolicyWorkerAgent(llm)
    weather_agent = WeatherWorkerAgent(llm)
    itinerary_agent = ItineraryWorkerAgent(llm)

    # Create graph
    print("[2] Building graph...")
    graph = MultiAgentGraph(
        supervisor_agent=supervisor,
        policy_agent=policy_agent,
        weather_agent=weather_agent,
        itinerary_agent=itinerary_agent,
        max_iterations=5
    )

    # Generate Mermaid diagram (text)
    print("\n[3] Generating Mermaid diagram...\n")
    print("="*80)
    print("MERMAID DIAGRAM (copy to https://mermaid.live)")
    print("="*80)

    mermaid_code = """
graph TD
    START([User Query]) --> SUPERVISOR[Supervisor Agent<br/>Routing & Integration]

    SUPERVISOR -->|policy needed| POLICY[Policy Worker<br/>Company Policies]
    SUPERVISOR -->|weather needed| WEATHER[Weather Worker<br/>Weather Data]
    SUPERVISOR -->|itinerary needed| ITINERARY[Itinerary Worker<br/>Trip Planning]
    SUPERVISOR -->|complete| END([Final Answer])

    POLICY --> SUPERVISOR
    WEATHER --> SUPERVISOR
    ITINERARY --> SUPERVISOR

    style START fill:#e1f5e1
    style END fill:#ffe1e1
    style SUPERVISOR fill:#e1e5ff
    style POLICY fill:#fff3e1
    style WEATHER fill:#fff3e1
    style ITINERARY fill:#fff3e1
"""
    print(mermaid_code)

    # Generate ASCII art representation
    print("\n" + "="*80)
    print("ASCII FLOW DIAGRAM")
    print("="*80)
    print("""
    ┌─────────────────┐
    │   User Query    │
    └────────┬────────┘
             ↓
    ┌────────────────────────────┐
    │   Supervisor Agent         │
    │  • Analyze query           │
    │  • Route to workers        │
    │  • Integrate results       │
    └──┬─────────┬─────────┬─────┘
       ↓         ↓         ↓
    ┌──────┐ ┌──────┐ ┌──────────┐
    │Policy│ │Weather│ │Itinerary│
    │Worker│ │Worker │ │  Worker  │
    └──┬───┘ └───┬──┘ └────┬─────┘
       ↓         ↓         ↓
       └─────────┴─────────┘
                 ↓
    ┌─────────────────────────┐
    │   Result Integration    │
    └────────────┬────────────┘
                 ↓
    ┌─────────────────────────┐
    │     Final Answer        │
    └─────────────────────────┘
    """)

    # State transitions
    print("\n" + "="*80)
    print("STATE TRANSITIONS")
    print("="*80)
    print("""
State: AgentState {
    query: str
    context: Dict
    next_agent: str              ← Routing decision
    messages: List[Dict]          ← Execution trace
    results: Dict[str, Any]       ← Worker outputs
    final_answer: str
    iteration_count: int
}

Transition Flow:
1. START → supervisor (iteration_count = 0)
2. supervisor → weather_worker (if weather needed)
3. weather_worker → supervisor (results["weather"] = ...)
4. supervisor → policy_worker (if policy needed)
5. policy_worker → supervisor (results["policy"] = ...)
6. supervisor → itinerary_worker (if itinerary needed)
7. itinerary_worker → supervisor (results["itinerary"] = ...)
8. supervisor → END (final_answer = integrated result)
    """)

    # Try to generate PNG (requires pygraphviz)
    try:
        print("\n[4] Generating PNG visualization...")
        output_path = "multi_agent_graph.png"
        graph.visualize(output_path)
        print(f"✓ PNG saved to {output_path}")
    except Exception as e:
        print(f"ℹ PNG generation skipped: {e}")
        print("  Install pygraphviz for PNG export: pip install pygraphviz")

    print("\n" + "="*80)
    print("✅ Visualization completed!")
    print("="*80)
    print("\nVisualization options:")
    print("1. Copy Mermaid code to https://mermaid.live")
    print("2. Use ASCII diagrams in documentation")
    print("3. Install pygraphviz for PNG export")


if __name__ == "__main__":
    try:
        visualize_graph()
    except Exception as e:
        print(f"\n❌ Visualization failed: {e}")
        import traceback
        traceback.print_exc()
