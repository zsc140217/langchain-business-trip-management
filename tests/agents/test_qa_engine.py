"""
测试 QAEngine - Q&A 域执行器
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.agents.qa_engine import QAEngine


class TestQAEngine:
    """测试 QAEngine 类"""

    @pytest.fixture
    def mock_llm(self):
        """创建 Mock LLM"""
        llm = Mock()
        response = Mock()
        response.content = '{"type": "simple", "tool": "search_policy", "reason": "单一政策查询"}'
        llm.invoke.return_value = response
        return llm

    @pytest.fixture
    def mock_tools(self):
        """创建 Mock 工具"""
        mock_tool = Mock()
        mock_tool.execute.return_value = "北京住宿标准：高管500元/天"
        return {
            "search_policy": mock_tool,
            "query_weather": mock_tool,
            "search_hotels": mock_tool,
        }

    @pytest.fixture
    def qa_engine(self, mock_llm, mock_tools):
        """创建 QAEngine 实例"""
        return QAEngine(llm=mock_llm, tools=mock_tools)

    def test_initialization(self, qa_engine):
        """测试初始化"""
        assert qa_engine.llm is not None
        assert qa_engine.tools is not None
        assert qa_engine.stats["total"] == 0
        assert qa_engine._complex_engine is None

    def test_execute_simple_query(self, qa_engine, mock_llm, mock_tools):
        """测试简单查询（simple 通道）"""
        response = Mock()
        response.content = '{"type": "simple", "tool": "search_policy", "reason": "单一查询"}'
        mock_llm.invoke.return_value = response

        result = qa_engine.execute("北京住宿标准")

        assert "北京住宿标准" in result or "500元" in result
        assert qa_engine.stats["simple"] == 1
        assert qa_engine.stats["total"] == 1

    def test_execute_complex_query(self, qa_engine, mock_llm):
        """测试复杂查询（complex 通道）"""
        response = Mock()
        response.content = '{"type": "complex", "reason": "多步骤查询"}'
        mock_llm.invoke.return_value = response

        mock_complex_engine = Mock()
        mock_complex_engine.execute.return_value = "复杂查询结果"
        qa_engine._complex_engine = mock_complex_engine

        result = qa_engine.execute("去杭州出差3天，查天气查酒店算费用")

        assert result == "复杂查询结果"
        assert qa_engine.stats["complex"] == 1

    def test_execute_planning_query(self, qa_engine, mock_llm):
        """测试规划查询（planning 通道）"""
        response = Mock()
        response.content = '{"type": "planning", "reason": "需要完整方案"}'
        mock_llm.invoke.return_value = response

        mock_planning_engine = Mock()
        mock_planning_engine.execute.return_value = "差旅规划方案"
        qa_engine._planning_engine = mock_planning_engine

        result = qa_engine.execute(
            "帮我安排下周去深圳出差",
            user_id="user_123",
            conversation_id="conv_456"
        )

        assert result == "差旅规划方案"
        assert qa_engine.stats["planning"] == 1

    def test_execute_open_query(self, qa_engine, mock_llm):
        """测试开放查询（open 通道）"""
        response = Mock()
        response.content = '{"type": "open", "reason": "比较推理"}'
        mock_llm.invoke.return_value = response

        mock_react_engine = Mock()
        mock_react_engine.execute.return_value = "飞机比高铁快但贵"
        qa_engine._react_engine = mock_react_engine

        result = qa_engine.execute("飞机和高铁哪个划算")

        assert result == "飞机比高铁快但贵"
        assert qa_engine.stats["open"] == 1

    def test_planning_query_without_user_id(self, qa_engine, mock_llm):
        """测试规划查询缺少 user_id（应降级到 complex）"""
        response = Mock()
        response.content = '{"type": "planning", "reason": "需要方案"}'
        mock_llm.invoke.return_value = response

        mock_complex_engine = Mock()
        mock_complex_engine.execute.return_value = "降级结果"
        qa_engine._complex_engine = mock_complex_engine

        result = qa_engine.execute("帮我安排出差")

        assert result == "降级结果"
        assert qa_engine.stats["complex"] == 1

    def test_get_stats(self, qa_engine):
        """测试获取统计信息"""
        qa_engine.stats = {"simple": 5, "complex": 3, "planning": 2, "open": 1, "total": 11}

        stats = qa_engine.get_stats()

        assert stats["simple"] == 5
        assert stats["total"] == 11

    def test_reset_stats(self, qa_engine):
        """测试重置统计信息"""
        qa_engine.stats = {"simple": 5, "complex": 3, "total": 8}

        qa_engine.reset_stats()

        assert qa_engine.stats["simple"] == 0
        assert qa_engine.stats["total"] == 0
