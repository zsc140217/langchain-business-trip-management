"""
Multi-Agent State Graph
LangGraph state management for multi-agent orchestration

Architecture:
- StateGraph: Defines agent workflow and transitions
- AgentState: Shared state across all agents
- Supervisor: Routes tasks to appropriate workers
- Workers: Execute specialized tasks (policy, weather, itinerary)

Design Principles:
- Immutable State: All state updates return new state
- Type Safety: TypedDict for state schema
- Observability: LangSmith tracing enabled
- Conditional Routing: Supervisor-based decision making
"""
from typing import TypedDict, List, Dict, Any, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langsmith import traceable
import operator
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# State Schema
# ============================================================================

class AgentState(TypedDict):
    """
    Shared state for multi-agent system

    State fields are passed between agents and updated immutably.
    Using Annotated with operator.add for list fields enables appending.

    Fields:
        query: Original user query
        context: Shared context (user info, conversation history, etc.)
        next_agent: Next agent to execute (routing decision)
        messages: Agent messages and results (append-only)
        results: Task execution results
        final_answer: Final integrated response
        iteration_count: Number of routing iterations (prevent infinite loops)
    """
    query: str
    context: Dict[str, Any]
    next_agent: str
    messages: Annotated[List[Dict[str, str]], operator.add]
    results: Dict[str, Any]
    final_answer: str
    iteration_count: int


# ============================================================================
# State Graph Builder
# ============================================================================

class MultiAgentGraph:
    """
    Multi-agent orchestration graph using LangGraph

    Architecture:
        User Query → Supervisor (routing) → Worker Agents → Supervisor (integrate) → END

    Workflow:
        1. Supervisor analyzes query and decides which worker(s) to invoke
        2. Workers execute tasks in parallel or sequence
        3. Supervisor integrates results and decides next step
        4. Repeat until task complete (or max iterations reached)

    Example:
        graph = MultiAgentGraph(supervisor, workers)
        result = graph.invoke({"query": "Check weather and recommend hotels"})
    """

    def __init__(
        self,
        supervisor_agent,
        policy_agent,
        weather_agent,
        itinerary_agent,
        max_iterations: int = 5
    ):
        """
        Initialize multi-agent graph

        Args:
            supervisor_agent: Supervisor agent for routing decisions
            policy_agent: Policy query worker
            weather_agent: Weather query worker
            itinerary_agent: Itinerary planning worker
            max_iterations: Max routing iterations to prevent infinite loops
        """
        self.supervisor = supervisor_agent
        self.policy_agent = policy_agent
        self.weather_agent = weather_agent
        self.itinerary_agent = itinerary_agent
        self.max_iterations = max_iterations

        # Build the graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()

        logger.info("Multi-agent graph initialized")

    def _build_graph(self) -> StateGraph:
        """
        Build LangGraph StateGraph

        Graph structure:
            START → supervisor → [policy_worker | weather_worker | itinerary_worker | END]
                                      ↓              ↓                   ↓
                                      └──────────────┴───────────────────→ supervisor

        Returns:
            Compiled StateGraph
        """
        # Create graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("policy_worker", self._policy_worker_node)
        workflow.add_node("weather_worker", self._weather_worker_node)
        workflow.add_node("itinerary_worker", self._itinerary_worker_node)

        # Set entry point
        workflow.set_entry_point("supervisor")

        # Add conditional edges from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_decision,
            {
                "policy_worker": "policy_worker",
                "weather_worker": "weather_worker",
                "itinerary_worker": "itinerary_worker",
                "END": END
            }
        )

        # Add edges back to supervisor after worker execution
        workflow.add_edge("policy_worker", "supervisor")
        workflow.add_edge("weather_worker", "supervisor")
        workflow.add_edge("itinerary_worker", "supervisor")

        logger.info("Graph structure built successfully")
        return workflow

    @traceable(name="supervisor_node")
    def _supervisor_node(self, state: AgentState) -> AgentState:
        """
        Supervisor node: Routing and result integration

        Responsibilities:
            1. Analyze query and decide which worker to invoke
            2. Integrate worker results into final answer
            3. Decide whether task is complete or needs more work

        Args:
            state: Current agent state

        Returns:
            Updated state with routing decision
        """
        logger.info(f"Supervisor: Iteration {state['iteration_count']}")

        # Check max iterations
        if state["iteration_count"] >= self.max_iterations:
            logger.warning(f"Max iterations ({self.max_iterations}) reached")
            return {
                **state,
                "next_agent": "END",
                "final_answer": state.get("final_answer") or "任务执行超时，请简化您的问题。"
            }

        # Invoke supervisor agent
        supervisor_result = self.supervisor.execute({
            "query": state["query"],
            "context": state["context"],
            "results": state["results"],
            "iteration": state["iteration_count"]
        })

        # Update state
        new_state = state.copy()
        new_state["next_agent"] = supervisor_result["next_agent"]
        new_state["iteration_count"] = state["iteration_count"] + 1

        # If task complete, set final answer
        if supervisor_result["next_agent"] == "END":
            new_state["final_answer"] = supervisor_result.get("final_answer", "")
            new_state["messages"] = state.get("messages", []) + [{
                "agent": "supervisor",
                "message": "Task completed",
                "final_answer": new_state["final_answer"]
            }]
        else:
            new_state["messages"] = state.get("messages", []) + [{
                "agent": "supervisor",
                "message": f"Routing to {supervisor_result['next_agent']}"
            }]

        return new_state

    @traceable(name="policy_worker_node")
    def _policy_worker_node(self, state: AgentState) -> AgentState:
        """
        Policy worker node: Query company policies

        Args:
            state: Current agent state

        Returns:
            Updated state with policy query results
        """
        logger.info("Policy worker: Executing task")

        # Execute policy agent
        result = self.policy_agent.execute({
            "query": state["query"],
            "context": state["context"]
        })

        # Update state (immutable)
        new_state = state.copy()
        new_state["results"]["policy"] = result
        new_state["messages"] = state.get("messages", []) + [{
            "agent": "policy_worker",
            "message": result
        }]

        logger.info(f"Policy worker completed: {result[:100]}...")
        return new_state

    @traceable(name="weather_worker_node")
    def _weather_worker_node(self, state: AgentState) -> AgentState:
        """
        Weather worker node: Query weather information

        Args:
            state: Current agent state

        Returns:
            Updated state with weather query results
        """
        logger.info("Weather worker: Executing task")

        # Execute weather agent
        result = self.weather_agent.execute({
            "query": state["query"],
            "context": state["context"]
        })

        # Update state (immutable)
        new_state = state.copy()
        new_state["results"]["weather"] = result
        new_state["messages"] = state.get("messages", []) + [{
            "agent": "weather_worker",
            "message": result
        }]

        logger.info(f"Weather worker completed: {result[:100]}...")
        return new_state

    @traceable(name="itinerary_worker_node")
    def _itinerary_worker_node(self, state: AgentState) -> AgentState:
        """
        Itinerary worker node: Plan trip itinerary

        Args:
            state: Current agent state

        Returns:
            Updated state with itinerary planning results
        """
        logger.info("Itinerary worker: Executing task")

        # Execute itinerary agent
        result = self.itinerary_agent.execute({
            "query": state["query"],
            "context": state["context"],
            "results": state["results"]  # Can use weather/policy results
        })

        # Update state (immutable)
        new_state = state.copy()
        new_state["results"]["itinerary"] = result
        new_state["messages"] = state.get("messages", []) + [{
            "agent": "itinerary_worker",
            "message": result
        }]

        logger.info(f"Itinerary worker completed: {result[:100]}...")
        return new_state

    def _route_decision(self, state: AgentState) -> Literal["policy_worker", "weather_worker", "itinerary_worker", "END"]:
        """
        Routing decision function

        Called by LangGraph to determine next node based on supervisor's decision

        Args:
            state: Current agent state

        Returns:
            Next node name
        """
        next_agent = state["next_agent"]
        logger.info(f"Routing decision: {next_agent}")
        return next_agent

    @traceable(name="multi_agent_invoke")
    def invoke(self, input_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke multi-agent graph

        Args:
            input_state: Initial state with at least "query" field

        Returns:
            Final state with results and final_answer
        """
        # Initialize state
        initial_state: AgentState = {
            "query": input_state["query"],
            "context": input_state.get("context", {}),
            "next_agent": "supervisor",
            "messages": [],
            "results": {},
            "final_answer": "",
            "iteration_count": 0
        }

        logger.info(f"Invoking multi-agent graph with query: {input_state['query']}")

        # Execute graph
        final_state = self.app.invoke(initial_state)

        logger.info("Multi-agent graph execution completed")
        return final_state

    def visualize(self, output_path: str = "multi_agent_graph.png"):
        """
        Visualize graph structure

        Requires: pip install pygraphviz (optional)

        Args:
            output_path: Output file path
        """
        try:
            from IPython.display import Image, display

            # Get graph visualization
            graph_image = self.app.get_graph().draw_mermaid_png()

            # Save to file
            with open(output_path, "wb") as f:
                f.write(graph_image)

            logger.info(f"Graph visualization saved to {output_path}")
            return graph_image

        except ImportError:
            logger.warning("Visualization requires IPython and pygraphviz")
            return None


# ============================================================================
# Helper Functions
# ============================================================================

def create_initial_state(query: str, user_id: str = "anonymous", **context) -> AgentState:
    """
    Create initial agent state

    Args:
        query: User query
        user_id: User identifier
        **context: Additional context

    Returns:
        Initial AgentState
    """
    return {
        "query": query,
        "context": {"user_id": user_id, **context},
        "next_agent": "supervisor",
        "messages": [],
        "results": {},
        "final_answer": "",
        "iteration_count": 0
    }


def extract_final_answer(state: AgentState) -> str:
    """
    Extract final answer from state

    Args:
        state: Final agent state

    Returns:
        Final answer string
    """
    return state.get("final_answer", "No answer generated")


def get_execution_trace(state: AgentState) -> List[Dict[str, str]]:
    """
    Get execution trace (message history)

    Args:
        state: Final agent state

    Returns:
        List of agent messages
    """
    return state.get("messages", [])
