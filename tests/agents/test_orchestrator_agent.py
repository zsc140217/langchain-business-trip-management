"""
测试 OrchestratorAgent - 统一入口 Agent
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.agents.orchestrator_agent import OrchestratorAgent


class TestOrchestratorAgent:
    """测试 OrchestratorAgent 类"""

    @pytest.fixture
    def mock_llm(self):
        """创建 Mock LLM"""
        return Mock()

    @pytest.fixture
    def mock_tools(self):
        """创建 Mock 工具"""
        mock_tool = Mock()
        mock_tool.execute.return_value = "工具执行结果"
        return {
            "query_weather": mock_tool,
            "search_flights": mock_tool,
            "search_hotels": mock_tool,
            "search_policy": mock_tool,
        }

    @pytest.fixture
    def orchestrator(self, mock_llm, mock_tools):
        """创建 OrchestratorAgent 实例"""
        return OrchestratorAgent(llm=mock_llm, tools=mock_tools)

    def test_initialization(self, orchestrator):
        """测试初始化"""
        assert orchestrator.llm is not None
        assert orchestrator.tools is not None
        assert orchestrator.stats["total"] == 0
        assert orchestrator._qa_engine is None

    def test_fast_path_weather(self, orchestrator, mock_tools):
        """测试快路径：天气查询"""
        result = orchestrator.route("北京今天天气怎么样")

        assert result == "工具执行结果"
        assert orchestrator.stats["fast_path"] == 1
        assert orchestrator.stats["total"] == 1
        mock_tools["query_weather"].execute.assert_called_once()

    def test_fast_path_hotel(self, orchestrator, mock_tools):
        """测试快路径：酒店查询"""
        result = orchestrator.route("推荐杭州的酒店")

        assert result == "工具执行结果"
        assert orchestrator.stats["fast_path"] == 1
        mock_tools["search_hotels"].execute.assert_called_once()

    def test_fast_path_policy(self, orchestrator, mock_tools):
        """测试快路径：政策查询"""
        result = orchestrator.route("北京出差住宿标准")

        assert result == "工具执行结果"
        assert orchestrator.stats["fast_path"] == 1
        mock_tools["search_policy"].execute.assert_called_once()

    def test_qa_domain_routing(self, orchestrator):
        """测试 Q&A 域路由"""
        mock_qa_engine = Mock()
        mock_qa_engine.execute.return_value = "Q&A 答案"
        orchestrator._qa_engine = mock_qa_engine

        result = orchestrator.route("副总和总监的关系是什么")

        assert result == "Q&A 答案"
        assert orchestrator.stats["qa_domain"] == 1
        mock_qa_engine.execute.assert_called_once()

    def test_approval_domain_detection(self, orchestrator):
        """测试审批域检测"""
        result = orchestrator.route("我要提交报销申请")

        assert orchestrator.stats["approval_domain"] == 1
        assert "审批功能暂未开放" in result

    def test_approval_domain_with_engine(self, orchestrator):
        """测试审批域路由（有审批引擎）"""
        mock_approval_engine = Mock()
        mock_approval_engine.execute.return_value = "审批结果"
        orchestrator._approval_engine = mock_approval_engine

        result = orchestrator.route("查询我的审批进度")

        assert result == "审批结果"
        assert orchestrator.stats["approval_domain"] == 1

    def test_is_approval_query(self, orchestrator):
        """测试审批查询识别"""
        assert orchestrator._is_approval_query("提交报销申请") is True
        assert orchestrator._is_approval_query("我的申请") is True
        assert orchestrator._is_approval_query("审批进度") is True
        assert orchestrator._is_approval_query("审批状态") is True
        assert orchestrator._is_approval_query("北京天气") is False
        assert orchestrator._is_approval_query("报销标准") is False  # 这是政策查询，不是审批

    def test_fast_path_tool_not_found(self, orchestrator, mock_tools):
        """测试快路径工具不存在（应走 Q&A 域）"""
        # 移除 query_weather 工具
        del mock_tools["query_weather"]

        mock_qa_engine = Mock()
        mock_qa_engine.execute.return_value = "Q&A 答案"
        orchestrator._qa_engine = mock_qa_engine

        result = orchestrator.route("北京天气")

        # 快路径失败，走 Q&A 域
        assert result == "Q&A 答案"
        assert orchestrator.stats["qa_domain"] == 1

    def test_memory_integration(self, orchestrator):
        """测试记忆服务集成"""
        mock_memory = Mock()
        mock_memory.build_enhanced_prompt.return_value = "用户是高管"
        orchestrator.memory_service = mock_memory

        mock_qa_engine = Mock()
        mock_qa_engine.execute.return_value = "答案"
        orchestrator._qa_engine = mock_qa_engine

        orchestrator.route("查询", user_id="user_123", conversation_id="conv_456")

        # 验证加载上下文
        mock_memory.build_enhanced_prompt.assert_called_once_with(
            user_id="user_123",
            conversation_id="conv_456"
        )

        # 验证传递上下文到 QAEngine
        call_args = mock_qa_engine.execute.call_args
        assert call_args[1]["context"] == "用户是高管"

    def test_get_stats(self, orchestrator):
        """测试获取统计信息"""
        orchestrator.stats = {"fast_path": 5, "qa_domain": 3, "approval_domain": 2, "total": 10}

        stats = orchestrator.get_stats()

        assert stats["fast_path"] == 5
        assert stats["qa_domain"] == 3
        assert stats["total"] == 10

    def test_get_stats_with_qa_engine(self, orchestrator):
        """测试获取统计信息（包含 QAEngine）"""
        mock_qa_engine = Mock()
        mock_qa_engine.get_stats.return_value = {"simple": 2, "complex": 1}
        orchestrator._qa_engine = mock_qa_engine

        stats = orchestrator.get_stats()

        assert "qa_engine" in stats
        assert stats["qa_engine"]["simple"] == 2

    def test_reset_stats(self, orchestrator):
        """测试重置统计信息"""
        orchestrator.stats = {"fast_path": 5, "qa_domain": 3, "total": 8}

        orchestrator.reset_stats()

        assert orchestrator.stats["fast_path"] == 0
        assert orchestrator.stats["total"] == 0
