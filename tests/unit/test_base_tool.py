"""
Unit Tests for BaseTool

Tests:
- Tool initialization
- Tool execution
- Caching mechanism
- Retry logic
- Error handling
- Timeout handling
"""
import pytest
import time
from unittest.mock import Mock, patch
from src.tools.base_tool import BaseTool, ToolExecutionError


class TestTool(BaseTool):
    """Concrete implementation for testing"""

    name: str = "test_tool"
    description: str = "Test tool"

    def __init__(self, should_fail=False, **kwargs):
        super().__init__(**kwargs)
        self.should_fail = should_fail
        self.call_count = 0

    def _run(self, param1: str = "default") -> str:
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("Tool execution failed")
        return f"Result for: {param1}"


class TestBaseTool:
    """Test suite for BaseTool"""

    def test_tool_initialization(self):
        """Test tool initialization"""
        tool = TestTool()

        assert tool.name == "test_tool"
        assert tool.description == "Test tool"
        assert tool.cache_enabled is False
        assert tool.max_retries == 3

    def test_tool_execution_success(self):
        """Test successful tool execution"""
        tool = TestTool()

        result = tool.invoke({"param1": "test_value"})

        assert result == "Result for: test_value"
        assert tool.call_count == 1

    def test_tool_execution_with_default_params(self):
        """Test tool execution with default parameters"""
        tool = TestTool()

        result = tool.invoke({})

        assert result == "Result for: default"
        assert tool.call_count == 1

    def test_tool_execution_failure(self):
        """Test tool execution that fails"""
        tool = TestTool(should_fail=True)

        with pytest.raises(RuntimeError) as exc_info:
            tool.invoke({"param1": "test"})

        assert "Tool execution failed" in str(exc_info.value)

    def test_retry_logic(self):
        """Test retry logic on failure"""
        tool = TestTool(should_fail=True)
        tool.max_retries = 3

        with pytest.raises(RuntimeError):
            tool.invoke({"param1": "test"})

        # Should retry 3 times
        assert tool.call_count == 3

    def test_retry_logic_eventual_success(self):
        """Test retry logic with eventual success"""
        tool = TestTool()
        call_count = 0

        def failing_run(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("Temporary failure")
            return "Success"

        tool._run = failing_run
        tool.max_retries = 3

        result = tool.invoke({"param1": "test"})

        assert result == "Success"
        assert call_count == 2  # Failed once, succeeded on second try

    def test_caching_disabled(self):
        """Test that caching is disabled by default"""
        tool = TestTool()
        tool.cache_enabled = False

        result1 = tool.invoke({"param1": "test"})
        result2 = tool.invoke({"param1": "test"})

        assert result1 == result2
        assert tool.call_count == 2  # Called twice, no caching

    def test_caching_enabled(self):
        """Test caching when enabled"""
        tool = TestTool()
        tool.cache_enabled = True

        result1 = tool.invoke({"param1": "test"})
        result2 = tool.invoke({"param1": "test"})

        assert result1 == result2
        assert tool.call_count == 1  # Called once, second from cache

    def test_cache_key_generation(self):
        """Test cache key generation"""
        tool = TestTool()

        key1 = tool._make_cache_key({"param1": "test", "param2": "value"})
        key2 = tool._make_cache_key({"param2": "value", "param1": "test"})

        # Keys should be the same regardless of parameter order
        assert key1 == key2

    def test_cache_expiration(self):
        """Test cache expiration"""
        tool = TestTool()
        tool.cache_enabled = True
        tool.cache_ttl_seconds = 1  # 1 second TTL

        result1 = tool.invoke({"param1": "test"})
        assert tool.call_count == 1

        # Wait for cache to expire
        time.sleep(1.1)

        result2 = tool.invoke({"param1": "test"})
        assert tool.call_count == 2  # Cache expired, called again

    def test_clear_cache(self):
        """Test cache clearing"""
        tool = TestTool()
        tool.cache_enabled = True

        result1 = tool.invoke({"param1": "test"})
        assert tool.call_count == 1

        tool.clear_cache()

        result2 = tool.invoke({"param1": "test"})
        assert tool.call_count == 2  # Cache cleared, called again

    def test_different_params_no_cache_hit(self):
        """Test that different parameters don't hit cache"""
        tool = TestTool()
        tool.cache_enabled = True

        result1 = tool.invoke({"param1": "test1"})
        result2 = tool.invoke({"param1": "test2"})

        assert result1 != result2
        assert tool.call_count == 2

    def test_tool_repr(self):
        """Test tool string representation"""
        tool = TestTool()

        repr_str = repr(tool)

        assert "TestTool" in repr_str
        assert "test_tool" in repr_str


class TestToolExecutionError:
    """Test ToolExecutionError exception"""

    def test_tool_execution_error(self):
        """Test ToolExecutionError"""
        error = ToolExecutionError("Tool failed")
        assert str(error) == "Tool failed"
        assert isinstance(error, Exception)
