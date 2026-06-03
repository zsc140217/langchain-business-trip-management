# Module 4: Multi-Agent Orchestration

**LangGraph-based multi-agent system with Supervisor-Worker pattern**

## 📋 Overview

This module implements a sophisticated multi-agent orchestration system using LangGraph's StateGraph. It demonstrates the Supervisor-Worker pattern where a central supervisor agent routes tasks to specialized worker agents, coordinates their execution, and integrates results into a coherent response.

## 🚀 Installation

Before running this module, install the required dependencies:

```bash
# Install LangGraph (required)
pip install langgraph>=0.0.26

# Install LangSmith for tracing (optional but recommended)
pip install langsmith>=0.1.0

# Or install all requirements
pip install -r requirements.txt
```

## 🎯 Key Features

- **LangGraph StateGraph**: Declarative workflow definition with state management
- **Supervisor-Worker Pattern**: Central routing and coordination
- **Conditional Routing**: Dynamic agent selection based on query analysis
- **Parallel Execution**: Workers can execute concurrently when dependencies allow
- **Result Integration**: LLM-based synthesis of multi-agent outputs
- **Immutable State**: Type-safe state updates using TypedDict
- **LangSmith Tracing**: Built-in observability for debugging

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Query                              │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────┐
│                    Supervisor Agent                             │
│  • Analyze query intent                                        │
│  • Route to appropriate worker(s)                              │
│  • Integrate results                                           │
│  • Decide completion                                           │
└─────────┬────────────┬────────────┬─────────────────────────────┘
          ↓            ↓            ↓
    ┌─────────┐  ┌─────────┐  ┌──────────┐
    │ Policy  │  │ Weather │  │Itinerary │
    │ Worker  │  │ Worker  │  │  Worker  │
    └─────────┘  └─────────┘  └──────────┘
          ↓            ↓            ↓
          └────────────┴────────────┘
                      ↓
          ┌───────────────────────┐
          │   Result Integration  │
          └───────────────────────┘
                      ↓
          ┌───────────────────────┐
          │    Final Answer       │
          └───────────────────────┘
```

## 📁 File Structure

```
module_4_multi_agent/
├── __init__.py              # Module exports
├── state_graph.py           # LangGraph StateGraph definition
├── supervisor.py            # Supervisor agent (routing & integration)
├── workers/
│   ├── __init__.py          # Worker exports
│   ├── policy_agent.py      # Policy query worker
│   ├── weather_agent.py     # Weather query worker
│   └── itinerary_agent.py   # Itinerary planning worker
├── example.py               # Complete usage example
├── test_multi_agent.py      # Comprehensive tests
└── README.md               # This file
```

## 🔧 Components

### 1. State Graph (`state_graph.py`)

**Core Concepts:**
- **AgentState**: TypedDict defining shared state schema
- **StateGraph**: LangGraph workflow with nodes and edges
- **Conditional Edges**: Dynamic routing based on supervisor decisions

**State Schema:**
```python
class AgentState(TypedDict):
    query: str                              # Original user query
    context: Dict[str, Any]                 # Shared context
    next_agent: str                         # Routing decision
    messages: List[Dict[str, str]]          # Execution trace
    results: Dict[str, Any]                 # Worker results
    final_answer: str                       # Integrated response
    iteration_count: int                    # Loop counter
```

**Graph Structure:**
```
START → supervisor → [policy_worker | weather_worker | itinerary_worker | END]
                          ↓              ↓                   ↓
                          └──────────────┴───────────────────→ supervisor
```

### 2. Supervisor Agent (`supervisor.py`)

**Responsibilities:**
- Query analysis and intent recognition
- Worker routing decisions
- Result integration using LLM
- Task completion detection

**Routing Strategy:**
- **Rule-based** (default): Keyword matching for efficiency
- **LLM-based** (optional): More flexible but higher latency

**Priority Order:** weather → policy → itinerary

### 3. Worker Agents

#### Policy Worker (`workers/policy_agent.py`)
- Queries company travel policies using RAG
- Provides compliance guidance
- Returns policy standards (accommodation, meals, transportation)

#### Weather Worker (`workers/weather_agent.py`)
- Queries real-time weather using WeatherTool
- Extracts city names from queries
- Provides weather-based travel recommendations

#### Itinerary Worker (`workers/itinerary_agent.py`)
- Plans comprehensive trip itineraries
- Integrates weather and policy information
- Recommends hotels, transportation, budget

## 🚀 Usage

### Basic Example

```python
from src.modules.module_4_multi_agent import (
    MultiAgentGraph,
    SupervisorAgent,
    PolicyWorkerAgent,
    WeatherWorkerAgent,
    ItineraryWorkerAgent
)
from src.models.llm import get_llm
from src.tools.weather_tool import WeatherTool

# Initialize LLM
llm = get_llm(temperature=0.3)

# Create worker agents
policy_agent = PolicyWorkerAgent(llm)
weather_agent = WeatherWorkerAgent(llm, WeatherTool())
itinerary_agent = ItineraryWorkerAgent(llm)

# Create supervisor
supervisor = SupervisorAgent(llm)

# Build multi-agent graph
graph = MultiAgentGraph(
    supervisor_agent=supervisor,
    policy_agent=policy_agent,
    weather_agent=weather_agent,
    itinerary_agent=itinerary_agent,
    max_iterations=5
)

# Execute query
result = graph.invoke({
    "query": "去杭州出差3天，查天气并推荐符合公司标准的酒店"
})

# Get final answer
print(result["final_answer"])

# Get execution trace
for msg in result["messages"]:
    print(f"[{msg['agent']}] {msg['message']}")
```

### Run Complete Example

```bash
# Run example with multiple query types
python src/modules/module_4_multi_agent/example.py
```

### Run Tests

```bash
# Run comprehensive test suite
python src/modules/module_4_multi_agent/test_multi_agent.py
```

## 🔄 Execution Flow

### Example: Complex Multi-Agent Query

**Query:** "去杭州出差3天，查天气、公司住宿标准，推荐行程"

**Flow:**
1. **Supervisor** analyzes query → Routes to weather_worker
2. **Weather Worker** queries weather for 杭州 → Returns weather data
3. **Supervisor** checks completion → Routes to policy_worker
4. **Policy Worker** queries accommodation policy → Returns policy standards
5. **Supervisor** checks completion → Routes to itinerary_worker
6. **Itinerary Worker** plans trip using weather + policy → Returns itinerary
7. **Supervisor** integrates results → Returns final answer
8. **END**

**Execution Trace:**
```
[supervisor] Routing to weather_worker
[weather_worker] 杭州：晴天，24°C，风速2m/s，湿度65% [模拟数据]
[supervisor] Routing to policy_worker
[policy_worker] 住宿标准：一线城市≤500元/晚...
[supervisor] Routing to itinerary_worker
[itinerary_worker] 行程规划：Day 1: 抵达杭州，入住酒店...
[supervisor] Task completed
```

## 🎨 State Management

### Immutable Updates

State updates follow immutable patterns:

```python
# ❌ WRONG: Mutating state
def _worker_node(self, state: AgentState) -> AgentState:
    state["results"]["worker"] = result  # Mutation!
    return state

# ✅ CORRECT: Creating new state
def _worker_node(self, state: AgentState) -> AgentState:
    new_state = state.copy()
    new_state["results"]["worker"] = result
    return new_state
```

### List Append Pattern

Using `Annotated` with `operator.add` for list fields:

```python
class AgentState(TypedDict):
    messages: Annotated[List[Dict], operator.add]  # Enables appending

# Usage
new_state["messages"] = [{"agent": "worker", "message": "Done"}]  # Appends!
```

## 🛠️ Reused Components

This module reuses existing implementations:

| Component | Source | Purpose |
|-----------|--------|---------|
| BaseAgent | `src/agents/base_agent.py` | Agent base class with LLM/tool integration |
| WeatherTool | `src/tools/weather_tool.py` | Weather query tool with caching |
| BaseTool | `src/tools/base_tool.py` | Tool base class with retry/tracing |
| Schemas | `src/models/schemas.py` | Type-safe data models |
| LLM | `src/models/llm.py` | Tongyi Qianwen LLM wrapper |

## 📊 Performance Considerations

### Routing Strategy Trade-offs

| Strategy | Latency | Accuracy | Predictability | Cost |
|----------|---------|----------|----------------|------|
| Rule-based | Low | Good | High | Low |
| LLM-based | High | Better | Medium | High |

**Recommendation:** Use rule-based routing (default) for production. Use LLM-based for complex edge cases.

### Parallel vs Sequential Execution

- **Parallel**: Workers with no dependencies can execute concurrently
- **Sequential**: Workers with dependencies execute in order
- Current implementation: Sequential (simpler, more predictable)
- Future enhancement: Detect dependencies and parallelize

## 🧪 Testing

### Test Coverage

1. **Single Agent Query** - Only one worker needed
2. **Multi-Agent Query** - Multiple workers coordinated
3. **Policy-Only Query** - Specific worker routing
4. **Weather Comparison** - Multiple cities in one query

### Running Tests

```bash
# Run all tests
python src/modules/module_4_multi_agent/test_multi_agent.py

# Run specific test
python -c "from src.modules.module_4_multi_agent.test_multi_agent import test_multi_agent_query; test_multi_agent_query()"
```

## 🐛 Debugging

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### LangSmith Tracing

All agents and nodes are decorated with `@traceable` for LangSmith observability.

Configure in `.env`:
```bash
LANGSMITH_API_KEY=your_key
LANGSMITH_PROJECT=module-4-multi-agent
```

View traces at: https://smith.langchain.com

### Execution Trace

```python
result = graph.invoke({"query": "..."})

# View all agent interactions
for msg in result["messages"]:
    print(f"[{msg['agent']}] {msg['message']}")
```

## 🔍 Key Design Decisions

### 1. Why Supervisor-Worker Pattern?

**Pros:**
- Clear separation of concerns
- Easy to add new workers
- Centralized routing logic
- Simple debugging

**Cons:**
- Supervisor is single point of failure
- Sequential routing (potential latency)

**Alternatives:**
- Peer-to-peer (more complex coordination)
- Hierarchical (multiple supervisor levels)

### 2. Why Rule-Based Routing?

**Rationale:**
- Predictable behavior in production
- Lower latency (no extra LLM call)
- Lower cost
- Easier to debug

**When to use LLM routing:**
- Complex queries with ambiguous intent
- Edge cases not covered by rules
- Rapid prototyping

### 3. Why Immutable State?

**Benefits:**
- Prevents side effects
- Easier reasoning about state changes
- Safe for parallel execution (future)
- Better debugging (state snapshots)

## 📚 Learning Resources

### LangGraph Concepts

- **StateGraph**: Declarative workflow definition
- **TypedDict State**: Type-safe state schema
- **Conditional Edges**: Dynamic routing
- **Checkpointing**: State persistence (not used here)

### Related Patterns

- **ReAct Agent** (Module 3): Single agent with tools
- **RAG Chain** (Modules 1-2): Retrieval + generation
- **Memory Systems** (Module 6): State persistence

## 🚧 Future Enhancements

1. **Parallel Execution**: Detect independent workers and parallelize
2. **Streaming**: Stream intermediate results to user
3. **Checkpointing**: Persist state for resumable workflows
4. **Dynamic Workers**: Add/remove workers at runtime
5. **Human-in-the-Loop**: Approval gates for certain decisions
6. **Error Recovery**: Retry failed workers with different strategies

## 📈 Metrics

Key metrics to track in production:

- **Routing Accuracy**: % of queries routed correctly
- **Iteration Count**: Average iterations per query
- **Worker Utilization**: Which workers are used most
- **Execution Time**: Latency by query complexity
- **Integration Quality**: User satisfaction with final answers

## 🎓 Key Takeaways

1. **LangGraph simplifies complex workflows** with declarative graph structure
2. **Supervisor-Worker pattern** is ideal for multi-domain queries
3. **Immutable state** prevents bugs and enables future parallelization
4. **Rule-based routing** is faster and more predictable than LLM routing
5. **Result integration** requires LLM for coherent multi-source synthesis

## 📞 Troubleshooting

### Common Issues

**Issue:** Worker not invoked
- Check `_identify_required_workers()` keyword matching
- Verify query contains relevant keywords

**Issue:** Infinite loop (max iterations reached)
- Check supervisor's `_is_task_complete()` logic
- Verify all required workers have results

**Issue:** Poor result integration
- Adjust supervisor LLM temperature
- Improve integration prompt
- Check worker result quality

## ✅ Success Criteria

Module is complete when:

- [x] State graph with supervisor and 3+ workers
- [x] Conditional routing based on query analysis
- [x] LLM-based result integration
- [x] Immutable state updates
- [x] Comprehensive tests (4+ scenarios)
- [x] Complete example with execution trace
- [x] README with architecture diagrams

## 🎉 Conclusion

This module demonstrates production-ready multi-agent orchestration using LangGraph. The supervisor-worker pattern provides a scalable foundation for complex workflows requiring coordination across multiple specialized agents.

**Next Steps:**
- Module 5: Function Calling & Structured Output
- Module 6: Memory Management (short/long-term)
- Module 7: Production Deployment (API + monitoring)

---

**Created:** 2026-06-02  
**Version:** 1.0.0  
**Dependencies:** langgraph, langchain, langsmith
