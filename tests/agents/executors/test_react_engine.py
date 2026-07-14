"""
ReactEngine 测试

测试 ReAct 执行引擎的功能：
1. 循环推理
2. 工具调用
3. 最终答案生成
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestReactEngine:
    """ReactEngine 测试类"""

    @pytest.fixture
    def mock_llm(self):
        """模拟 LLM"""
        llm = Mock()
        llm.bind_tools = Mock(return_value=llm)
        return llm

    @pytest.fixture
    def mock_tools(self):
        """模拟工具"""
        weather_tool = Mock()
        weather_tool.name = "query_weather"
        weather_tool.description = "查询天气"

        policy_tool = Mock()
        policy_tool.name = "search_policy"
        policy_tool.description = "查询政策"

        return {
            "query_weather": weather_tool,
            "search_policy": policy_tool
        }

    @pytest.fixture
    def engine(self, mock_llm, mock_tools):
        """创建 ReactEngine 实例"""
        from src.agents.executors.react_engine import ReactEngine
        return ReactEngine(llm=mock_llm, tools=mock_tools)

    def test_init(self, engine, mock_llm, mock_tools):
        """测试初始化"""
        assert engine.llm == mock_llm
        assert engine.tools == mock_tools
        assert engine.max_iterations == 5

    def test_execute_simple_query(self, engine, mock_llm):
        """测试执行简单查询（直接返回答案，无需工具）"""
        mock_response = Mock()
        mock_response.content = "北京天气晴朗"
        mock_response.tool_calls = []
        mock_llm.invoke = Mock(return_value=mock_response)

        result = engine.execute("北京天气怎么样")

        assert result is not None
        assert "北京天气晴朗" in result
        mock_llm.invoke.assert_called_once()

    def test_execute_with_tool_calls(self, engine, mock_llm, mock_tools):
        """测试执行需要工具调用的查询"""
        tool_call_response = Mock()
        tool_call_response.content = ""
        tool_call_response.tool_calls = [
            {
                "id": "call_1",
                "name": "query_weather",
                "args": {"city": "北京"}
            }
        ]

        final_response = Mock()
        final_response.content = "北京天气晴天，20-30度"
        final_response.tool_calls = []

        mock_llm.invoke = Mock(side_effect=[tool_call_response, final_response])
        mock_tools["query_weather"].invoke = Mock(return_value="晴天，20-30度")

        result = engine.execute("北京天气怎么样")

        mock_tools["query_weather"].invoke.assert_called_once_with({"city": "北京"})
        assert "北京天气晴天" in result or "20-30度" in result

    def test_max_iterations_limit(self, engine, mock_llm, mock_tools):
        """测试最大迭代次数限制"""
        tool_call_response = Mock()
        tool_call_response.content = ""
        tool_call_response.tool_calls = [
            {
                "id": f"call_1",
                "name": "query_weather",
                "args": {"city": "北京"}
            }
        ]

        mock_llm.invoke = Mock(return_value=tool_call_response)
        mock_tools["query_weather"].invoke = Mock(return_value="晴天")

        result = engine.execute("测试查询", max_iterations=3)

        assert mock_llm.invoke.call_count <= 3
        # 验证返回了降级答案（包含收集的信息）
        assert result is not None
        assert "query_weather" in result or "晴天" in result

    def test_tool_execution_error(self, engine, mock_llm, mock_tools):
        """测试工具执行错误的情况"""
        tool_call_response = Mock()
        tool_call_response.content = ""
        tool_call_response.tool_calls = [
            {
                "id": "call_1",
                "name": "query_weather",
                "args": {"city": "北京"}
            }
        ]

        final_response = Mock()
        final_response.content = "抱歉，无法查询天气"
        final_response.tool_calls = []

        mock_llm.invoke = Mock(side_effect=[tool_call_response, final_response])
        mock_tools["query_weather"].invoke = Mock(side_effect=Exception("服务不可用"))

        result = engine.execute("北京天气怎么样")

        assert result is not None
        assert "抱歉" in result or "无法" in result

    def test_unknown_tool(self, engine, mock_llm, mock_tools):
        """测试调用未知工具的情况"""
        tool_call_response = Mock()
        tool_call_response.content = ""
        tool_call_response.tool_calls = [
            {
                "id": "call_1",
                "name": "unknown_tool",
                "args": {}
            }
        ]

        final_response = Mock()
        final_response.content = "工具不可用"
        final_response.tool_calls = []

        mock_llm.invoke = Mock(side_effect=[tool_call_response, final_response])

        result = engine.execute("测试查询")

        assert result is not None
