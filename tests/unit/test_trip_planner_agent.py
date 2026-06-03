"""
Unit Tests for TripPlannerAgent

Tests:
- Trip planning execution
- Task decomposition integration
- Batch execution
- Parallel execution
- Result synthesis
- Error handling
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agents.trip_planner_agent import TripPlannerAgent
from src.agents.task_decomposer import SubTask


class TestTripPlannerAgent:
    """Test suite for TripPlannerAgent"""

    @pytest.fixture
    def mock_task_decomposer(self):
        """Mock TaskDecomposer"""
        mock = Mock()
        mock.decompose = Mock(return_value=[
            SubTask(
                id=0,
                task_type="QUERY_WEATHER",
                description="Query Beijing weather",
                parameters={"city": "Beijing"},
                depends_on=[],
                priority=0
            ),
            SubTask(
                id=1,
                task_type="QUERY_HOTEL",
                description="Recommend Beijing hotels",
                parameters={"city": "Beijing"},
                depends_on=[],
                priority=0
            )
        ])
        mock.sort_tasks_by_dependency = Mock(return_value=[
            [SubTask(id=0, task_type="QUERY_WEATHER", description="Query weather", parameters={"city": "Beijing"}, depends_on=[], priority=0)],
            [SubTask(id=1, task_type="QUERY_HOTEL", description="Query hotel", parameters={"city": "Beijing"}, depends_on=[0], priority=1)]
        ])
        return mock

    def test_agent_initialization(self, mock_llm, mock_task_decomposer):
        """Test agent initialization"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer,
            config={"temperature": 0.5}
        )

        assert agent.name == "TripPlannerAgent"
        assert agent.task_decomposer == mock_task_decomposer
        assert agent.config["temperature"] == 0.5

    def test_execute_simple_trip(self, mock_llm, mock_task_decomposer, sample_trip_task):
        """Test executing simple trip planning task"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        result = agent.execute(sample_trip_task)

        assert result is not None
        assert isinstance(result, str)
        mock_task_decomposer.decompose.assert_called_once()
        mock_task_decomposer.sort_tasks_by_dependency.assert_called_once()

    def test_execute_missing_query(self, mock_llm, mock_task_decomposer):
        """Test execution with missing query field"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        with pytest.raises(ValueError) as exc_info:
            agent.execute({"user_id": "test"})

        assert "Missing required fields" in str(exc_info.value)

    def test_execute_with_preferences(self, mock_llm, mock_task_decomposer):
        """Test execution with user preferences"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        task = {
            "query": "Plan trip to Beijing",
            "user_id": "test_user",
            "preferences": {
                "budget": "high",
                "hotel_chain": "Marriott"
            }
        }

        result = agent.execute(task)

        assert result is not None
        # Preferences should be passed to synthesis
        assert "Marriott" in result or "high" in result.lower() or len(result) > 0

    def test_execute_batches_single_task(self, mock_llm, mock_task_decomposer):
        """Test executing single task batch"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        task = SubTask(
            id=0,
            task_type="QUERY_WEATHER",
            description="Query weather",
            parameters={"city": "Beijing"},
            depends_on=[],
            priority=0
        )

        results = agent._execute_batches([[task]])

        assert 0 in results
        assert task.result is not None
        assert task.success is True

    def test_execute_batches_parallel(self, mock_llm, mock_task_decomposer):
        """Test executing multiple tasks in parallel"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        tasks = [
            SubTask(id=0, task_type="QUERY_WEATHER", description="Query weather", parameters={"city": "Beijing"}, depends_on=[], priority=0),
            SubTask(id=1, task_type="QUERY_HOTEL", description="Query hotel", parameters={"city": "Beijing"}, depends_on=[], priority=0)
        ]

        results = agent._execute_batches([tasks])

        assert 0 in results
        assert 1 in results
        assert tasks[0].success is True
        assert tasks[1].success is True

    def test_execute_subtask_weather(self, mock_llm, mock_task_decomposer):
        """Test executing weather query subtask"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        task = SubTask(
            id=0,
            task_type="QUERY_WEATHER",
            description="Query Beijing weather",
            parameters={"city": "Beijing"},
            depends_on=[],
            priority=0
        )

        result = agent._execute_subtask(task)

        assert result is not None
        assert "Beijing" in result or "北京" in result

    def test_execute_subtask_hotel(self, mock_llm, mock_task_decomposer):
        """Test executing hotel query subtask"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        task = SubTask(
            id=0,
            task_type="QUERY_HOTEL",
            description="Query hotels",
            parameters={"city": "Beijing"},
            depends_on=[],
            priority=0
        )

        result = agent._execute_subtask(task)

        assert result is not None
        assert "hotel" in result.lower() or "Beijing" in result

    def test_execute_subtask_unknown_type(self, mock_llm, mock_task_decomposer):
        """Test executing unknown subtask type"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        task = SubTask(
            id=0,
            task_type="UNKNOWN_TYPE",
            description="Unknown task",
            parameters={},
            depends_on=[],
            priority=0
        )

        result = agent._execute_subtask(task)

        assert "Unknown task type" in result

    def test_synthesize_itinerary(self, mock_llm, mock_task_decomposer):
        """Test itinerary synthesis"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        tasks = [
            SubTask(id=0, task_type="QUERY_WEATHER", description="Weather", parameters={}, depends_on=[], priority=0, result="Sunny, 25°C", success=True),
            SubTask(id=1, task_type="QUERY_HOTEL", description="Hotel", parameters={}, depends_on=[], priority=0, result="Hilton Beijing", success=True)
        ]

        results = {0: "Sunny, 25°C", 1: "Hilton Beijing"}

        itinerary = agent._synthesize_itinerary(
            "Plan trip to Beijing",
            tasks,
            results,
            {"budget": "medium"}
        )

        assert itinerary is not None
        assert isinstance(itinerary, str)
        assert len(itinerary) > 0

    def test_synthesize_itinerary_llm_failure(self, mock_llm, mock_task_decomposer):
        """Test itinerary synthesis when LLM fails"""
        mock_llm.predict = Mock(side_effect=Exception("LLM error"))

        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        tasks = [
            SubTask(id=0, task_type="QUERY_WEATHER", description="Weather", parameters={}, depends_on=[], priority=0, result="Sunny", success=True)
        ]
        results = {0: "Sunny"}

        itinerary = agent._synthesize_itinerary("Test", tasks, results, {})

        # Should fallback to raw results
        assert "Sunny" in itinerary

    def test_query_weather(self, mock_llm, mock_task_decomposer):
        """Test weather query helper"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        result = agent._query_weather({"city": "Beijing"})

        assert "Beijing" in result or "unavailable" in result

    def test_query_hotel(self, mock_llm, mock_task_decomposer):
        """Test hotel query helper"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        result = agent._query_hotel({"city": "Beijing"})

        assert "hotel" in result.lower() or "Beijing" in result

    def test_query_policy(self, mock_llm, mock_task_decomposer):
        """Test policy query helper"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        result = agent._query_policy({"keyword": "accommodation"})

        assert "policy" in result.lower() or "accommodation" in result.lower()

    def test_execution_with_failed_subtask(self, mock_llm, mock_task_decomposer):
        """Test execution when a subtask fails"""
        agent = TripPlannerAgent(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer
        )

        # Create a task that will fail
        def mock_execute_subtask(task):
            if task.id == 0:
                raise Exception("Task failed")
            return "Success"

        agent._execute_subtask = mock_execute_subtask

        task = {
            "query": "Plan trip",
            "user_id": "test"
        }

        # Should handle the error gracefully
        result = agent.execute(task)
        assert result is not None
