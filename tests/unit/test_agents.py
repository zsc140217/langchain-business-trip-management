"""
Unit Tests for Agents
Test individual agent functionality in isolation

Test Coverage:
- BaseAgent functionality
- TripPlannerAgent task execution
- PolicyAdvisorAgent RAG retrieval
- ComplexityAssessor routing logic
- TaskDecomposer task generation

Run tests:
    pytest tests/unit/test_agents.py -v
    pytest tests/unit/test_agents.py::TestBaseAgent -v
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.agents.base_agent import BaseAgent, AgentExecutionError
from src.agents.trip_planner_agent import TripPlannerAgent
from src.agents.policy_advisor_agent import PolicyAdvisorAgent
from src.agents.complexity_assessor import ComplexityAssessor, QueryComplexity
from src.agents.task_decomposer import TaskDecomposer, SubTask


# ============================================================================
# Test BaseAgent
# ============================================================================

class TestBaseAgent:
    """Test BaseAgent functionality"""

    def test_base_agent_initialization(self):
        """Test agent initialization"""
        mock_llm = Mock()
        mock_tool = Mock()
        mock_tool.name = "test_tool"

        agent = BaseAgent(
            name="TestAgent",
            llm=mock_llm,
            tools=[mock_tool],
            config={"temperature": 0.5}
        )

        assert agent.name == "TestAgent"
        assert agent.llm == mock_llm
        assert "test_tool" in agent.tools
        assert agent.get_config("temperature") == 0.5

    def test_base_agent_execute_not_implemented(self):
        """Test that execute raises NotImplementedError"""
        mock_llm = Mock()
        agent = BaseAgent(name="TestAgent", llm=mock_llm)

        with pytest.raises(NotImplementedError):
            agent.execute({"query": "test"})

    def test_invoke_tool_success(self):
        """Test successful tool invocation"""
        mock_llm = Mock()
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.invoke.return_value = "tool result"

        agent = BaseAgent(name="TestAgent", llm=mock_llm, tools=[mock_tool])

        result = agent.invoke_tool("test_tool", {"param": "value"})

        assert result == "tool result"
        mock_tool.invoke.assert_called_once_with({"param": "value"})

    def test_invoke_tool_not_found(self):
        """Test tool invocation with non-existent tool"""
        mock_llm = Mock()
        agent = BaseAgent(name="TestAgent", llm=mock_llm)

        with pytest.raises(ValueError, match="Tool 'nonexistent' not found"):
            agent.invoke_tool("nonexistent", {})

    def test_invoke_tool_execution_failure(self):
        """Test tool invocation failure"""
        mock_llm = Mock()
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.invoke.side_effect = Exception("Tool error")

        agent = BaseAgent(name="TestAgent", llm=mock_llm, tools=[mock_tool])

        with pytest.raises(RuntimeError, match="Tool execution failed"):
            agent.invoke_tool("test_tool", {})

    def test_call_llm_success(self):
        """Test successful LLM call"""
        mock_llm = Mock()
        mock_llm.predict.return_value = "LLM response"

        agent = BaseAgent(name="TestAgent", llm=mock_llm)

        result = agent.call_llm("test prompt", temperature=0.3)

        assert result == "LLM response"
        mock_llm.predict.assert_called_once_with("test prompt", temperature=0.3)

    def test_call_llm_failure(self):
        """Test LLM call failure"""
        mock_llm = Mock()
        mock_llm.predict.side_effect = Exception("LLM error")

        agent = BaseAgent(name="TestAgent", llm=mock_llm)

        with pytest.raises(RuntimeError, match="LLM call failed"):
            agent.call_llm("test prompt")

    def test_validate_task_success(self):
        """Test successful task validation"""
        mock_llm = Mock()
        agent = BaseAgent(name="TestAgent", llm=mock_llm)

        task = {"field1": "value1", "field2": "value2"}
        agent.validate_task(task, required_fields=["field1", "field2"])
        # Should not raise

    def test_validate_task_missing_fields(self):
        """Test task validation with missing fields"""
        mock_llm = Mock()
        agent = BaseAgent(name="TestAgent", llm=mock_llm)

        task = {"field1": "value1"}

        with pytest.raises(ValueError, match="Missing required fields"):
            agent.validate_task(task, required_fields=["field1", "field2"])


# ============================================================================
# Test TripPlannerAgent
# ============================================================================

class TestTripPlannerAgent:
    """Test TripPlannerAgent functionality"""

    @pytest.fixture
    def mock_task_decomposer(self):
        """Create mock task decomposer"""
        decomposer = Mock(spec=TaskDecomposer)

        # Mock subtasks
        subtasks = [
            SubTask(
                id=0,
                task_type="QUERY_WEATHER",
                description="Check weather",
                parameters={"city": "Beijing"},
                depends_on=[],
                priority=0
            ),
            SubTask(
                id=1,
                task_type="QUERY_HOTEL",
                description="Recommend hotel",
                parameters={"city": "Beijing"},
                depends_on=[],
                priority=0
            )
        ]

        decomposer.decompose.return_value = subtasks
        decomposer.sort_tasks_by_dependency.return_value = [subtasks]

        return decomposer

    def test_trip_planner_initialization(self, mock_task_decomposer):
        """Test TripPlannerAgent initialization"""
        mock_llm = Mock()

        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        assert agent.name == "TripPlannerAgent"
        assert agent.task_decomposer == mock_task_decomposer

    def test_trip_planner_execute_success(self, mock_task_decomposer):
        """Test successful trip planning"""
        mock_llm = Mock()
        mock_llm.predict.return_value = "Trip itinerary: ..."

        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        task = {
            "query": "Plan a trip to Beijing",
            "user_id": "test_user"
        }

        result = agent.execute(task)

        assert "Trip itinerary" in result
        mock_task_decomposer.decompose.assert_called_once()

    def test_trip_planner_missing_query(self, mock_task_decomposer):
        """Test trip planning with missing query"""
        mock_llm = Mock()

        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        with pytest.raises(ValueError, match="Missing required fields"):
            agent.execute({"user_id": "test_user"})


# ============================================================================
# Test PolicyAdvisorAgent
# ============================================================================

class TestPolicyAdvisorAgent:
    """Test PolicyAdvisorAgent functionality"""

    def test_policy_advisor_initialization(self):
        """Test PolicyAdvisorAgent initialization"""
        mock_llm = Mock()
        mock_retriever = Mock()

        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=mock_retriever
        )

        assert agent.name == "PolicyAdvisorAgent"
        assert agent.hybrid_retriever == mock_retriever

    def test_policy_advisor_execute_with_rag(self):
        """Test policy query with RAG"""
        mock_llm = Mock()
        mock_llm.predict.return_value = "Policy answer: ..."

        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            {
                "content": "Shanghai accommodation policy: 600 yuan/day",
                "source": "policy.txt",
                "score": 0.95
            }
        ]

        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=mock_retriever,
            config={"use_query_rewriting": False}
        )

        task = {
            "query": "What's the accommodation policy for Shanghai?",
            "user_id": "test_user"
        }

        result = agent.execute(task)

        assert "Policy answer" in result
        mock_retriever.retrieve.assert_called_once()

    def test_policy_advisor_fallback_no_rag(self):
        """Test policy query fallback when RAG fails"""
        mock_llm = Mock()
        mock_llm.predict.return_value = "Fallback answer"

        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=None  # No retriever
        )

        task = {
            "query": "What's the policy?",
            "user_id": "test_user"
        }

        result = agent.execute(task)

        assert "Fallback answer" in result or "unable to answer" in result.lower()

    def test_expense_validation(self):
        """Test expense validation"""
        mock_llm = Mock()

        agent = PolicyAdvisorAgent(llm=mock_llm)

        expense = {
            "amount": 800,
            "category": "accommodation",
            "city": "Shanghai"
        }

        validation = agent.validate_expense(expense)

        assert "valid" in validation
        assert "requires_approval" in validation


# ============================================================================
# Test ComplexityAssessor
# ============================================================================

class TestComplexityAssessor:
    """Test ComplexityAssessor functionality"""

    def test_complexity_assessor_simple_query(self):
        """Test SIMPLE query assessment"""
        mock_llm = Mock()

        assessor = ComplexityAssessor(llm=mock_llm)

        # Simple weather query
        complexity = assessor.assess("北京天气怎么样")

        assert complexity == QueryComplexity.SIMPLE

    def test_complexity_assessor_medium_query(self):
        """Test MEDIUM query assessment"""
        mock_llm = Mock()

        assessor = ComplexityAssessor(llm=mock_llm)

        # Weather comparison (2 cities)
        complexity = assessor.assess("北京和上海天气对比")

        assert complexity == QueryComplexity.MEDIUM

    def test_complexity_assessor_complex_query(self):
        """Test COMPLEX query assessment"""
        mock_llm = Mock()
        mock_llm.predict.return_value = "COMPLEX"

        assessor = ComplexityAssessor(llm=mock_llm)

        # Multi-step trip planning
        complexity = assessor.assess("去杭州出差，查天气、推荐酒店、找客户地址")

        # Should use LLM for complex queries
        assert complexity in [QueryComplexity.MEDIUM, QueryComplexity.COMPLEX]


# ============================================================================
# Test TaskDecomposer
# ============================================================================

class TestTaskDecomposer:
    """Test TaskDecomposer functionality"""

    def test_task_decomposer_initialization(self):
        """Test TaskDecomposer initialization"""
        mock_llm = Mock()

        decomposer = TaskDecomposer(llm=mock_llm)

        assert decomposer.llm == mock_llm

    def test_task_decomposition(self):
        """Test task decomposition"""
        mock_llm = Mock()
        mock_llm.predict.return_value = """[
            {
                "id": 0,
                "task_type": "QUERY_WEATHER",
                "description": "Check weather",
                "parameters": {"city": "Beijing"},
                "depends_on": [],
                "priority": 0
            }
        ]"""

        decomposer = TaskDecomposer(llm=mock_llm)

        tasks = decomposer.decompose("Check Beijing weather")

        assert len(tasks) == 1
        assert tasks[0].task_type == "QUERY_WEATHER"

    def test_topological_sort_no_dependencies(self):
        """Test topological sort with no dependencies"""
        mock_llm = Mock()
        decomposer = TaskDecomposer(llm=mock_llm)

        tasks = [
            SubTask(id=0, task_type="QUERY_WEATHER", description="Task 0", parameters={}, depends_on=[]),
            SubTask(id=1, task_type="QUERY_HOTEL", description="Task 1", parameters={}, depends_on=[])
        ]

        batches = decomposer.sort_tasks_by_dependency(tasks)

        # All tasks should be in one batch (parallel execution)
        assert len(batches) == 1
        assert len(batches[0]) == 2

    def test_topological_sort_with_dependencies(self):
        """Test topological sort with dependencies"""
        mock_llm = Mock()
        decomposer = TaskDecomposer(llm=mock_llm)

        tasks = [
            SubTask(id=0, task_type="QUERY_WEATHER", description="Task 0", parameters={}, depends_on=[]),
            SubTask(id=1, task_type="QUERY_HOTEL", description="Task 1", parameters={}, depends_on=[]),
            SubTask(id=2, task_type="QUERY_ROUTE", description="Task 2", parameters={}, depends_on=[0, 1])
        ]

        batches = decomposer.sort_tasks_by_dependency(tasks)

        # Should have 2 batches: [0,1] then [2]
        assert len(batches) == 2
        assert len(batches[0]) == 2  # Tasks 0 and 1
        assert len(batches[1]) == 1  # Task 2


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
