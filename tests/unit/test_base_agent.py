"""
Unit Tests for BaseAgent

Tests:
- Agent initialization
- Tool invocation
- LLM calls
- Task validation
- Error handling
- Configuration management
"""
import pytest
from unittest.mock import Mock, patch
from src.agents.base_agent import BaseAgent, AgentExecutionError, ToolInvocationError


class TestAgent(BaseAgent):
    """Concrete implementation for testing"""

    def execute(self, task):
        self.validate_task(task, required_fields=["query"])
        return self.call_llm(f"Test: {task['query']}")


class TestBaseAgent:
    """Test suite for BaseAgent"""

    def test_agent_initialization(self, mock_llm):
        """Test agent initialization with tools and config"""
        tool = Mock()
        tool.name = "test_tool"

        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm,
            tools=[tool],
            config={"temperature": 0.5}
        )

        assert agent.name == "TestAgent"
        assert agent.llm == mock_llm
        assert "test_tool" in agent.tools
        assert agent.config["temperature"] == 0.5

    def test_agent_initialization_without_tools(self, mock_llm):
        """Test agent initialization without tools"""
        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm
        )

        assert agent.name == "TestAgent"
        assert len(agent.tools) == 0
        assert agent.config == {}

    def test_tool_invocation_success(self, mock_llm):
        """Test successful tool invocation"""
        tool = Mock()
        tool.name = "test_tool"
        tool.invoke = Mock(return_value="Tool result")

        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm,
            tools=[tool]
        )

        result = agent.invoke_tool("test_tool", {"param": "value"})

        assert result == "Tool result"
        tool.invoke.assert_called_once_with({"param": "value"})

    def test_tool_invocation_not_found(self, mock_llm):
        """Test tool invocation with non-existent tool"""
        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm,
            tools=[]
        )

        with pytest.raises(ValueError) as exc_info:
            agent.invoke_tool("nonexistent_tool", {})

        assert "Tool 'nonexistent_tool' not found" in str(exc_info.value)

    def test_tool_invocation_failure(self, mock_llm):
        """Test tool invocation that fails"""
        tool = Mock()
        tool.name = "test_tool"
        tool.invoke = Mock(side_effect=Exception("Tool error"))

        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm,
            tools=[tool]
        )

        with pytest.raises(RuntimeError) as exc_info:
            agent.invoke_tool("test_tool", {"param": "value"})

        assert "Tool execution failed" in str(exc_info.value)

    def test_call_llm_success(self, mock_llm):
        """Test successful LLM call"""
        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm,
            config={"temperature": 0.3}
        )

        result = agent.call_llm("Test prompt")

        assert result is not None
        mock_llm.predict.assert_called_once()

    def test_call_llm_with_custom_temperature(self, mock_llm):
        """Test LLM call with custom temperature"""
        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm,
            config={"temperature": 0.3}
        )

        result = agent.call_llm("Test prompt", temperature=0.8)

        assert result is not None
        mock_llm.predict.assert_called_with("Test prompt", temperature=0.8)

    def test_call_llm_failure(self, mock_llm):
        """Test LLM call that fails"""
        mock_llm.predict = Mock(side_effect=Exception("LLM error"))

        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm
        )

        with pytest.raises(RuntimeError) as exc_info:
            agent.call_llm("Test prompt")

        assert "LLM call failed" in str(exc_info.value)

    def test_validate_task_success(self, mock_llm):
        """Test successful task validation"""
        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm
        )

        task = {"query": "test", "user_id": "user123"}
        agent.validate_task(task, required_fields=["query"])
        # Should not raise

    def test_validate_task_missing_fields(self, mock_llm):
        """Test task validation with missing required fields"""
        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm
        )

        task = {"user_id": "user123"}

        with pytest.raises(ValueError) as exc_info:
            agent.validate_task(task, required_fields=["query", "city"])

        assert "Missing required fields" in str(exc_info.value)
        assert "query" in str(exc_info.value)
        assert "city" in str(exc_info.value)

    def test_get_config(self, mock_llm):
        """Test get configuration value"""
        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm,
            config={"temperature": 0.5, "max_tokens": 1000}
        )

        assert agent.get_config("temperature") == 0.5
        assert agent.get_config("max_tokens") == 1000
        assert agent.get_config("nonexistent") is None
        assert agent.get_config("nonexistent", "default") == "default"

    def test_execute_with_valid_task(self, mock_llm):
        """Test execute method with valid task"""
        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm
        )

        result = agent.execute({"query": "test query"})

        assert result is not None
        assert "Mock" in result or "test query" in result.lower()

    def test_execute_with_invalid_task(self, mock_llm):
        """Test execute method with invalid task"""
        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm
        )

        with pytest.raises(ValueError):
            agent.execute({})  # Missing required "query" field

    def test_agent_repr(self, mock_llm):
        """Test agent string representation"""
        tool = Mock()
        tool.name = "test_tool"

        agent = TestAgent(
            name="TestAgent",
            llm=mock_llm,
            tools=[tool]
        )

        repr_str = repr(agent)

        assert "TestAgent" in repr_str
        assert "test_tool" in repr_str


class TestCustomExceptions:
    """Test custom exceptions"""

    def test_agent_execution_error(self):
        """Test AgentExecutionError"""
        error = AgentExecutionError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_tool_invocation_error(self):
        """Test ToolInvocationError"""
        error = ToolInvocationError("Tool failed")
        assert str(error) == "Tool failed"
        assert isinstance(error, Exception)
