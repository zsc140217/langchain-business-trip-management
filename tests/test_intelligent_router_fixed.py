"""
测试修正后的三层路由架构

测试重点：
1. Layer 0: 工具调用保存结果而不返回
2. Layer 1: 所有查询都执行RAG检索
3. Layer 2: LLM综合分析决定是否需要更多工具

作者：Claude
创建时间：2026-06-28
"""
import pytest
import os
from unittest.mock import Mock, MagicMock, patch
from langchain_core.documents import Document

# Mock 环境变量以避免测试失败
os.environ.setdefault("DASHSCOPE_API_KEY", "test_key")
os.environ.setdefault("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

from src.agents.intelligent_router import IntelligentRouter
from src.agents.context_accumulator import ContextAccumulator
from src.agents.synthesis_layer import SynthesisLayer


class TestContextAccumulator:
    """测试上下文累积器"""

    def test_initialization(self):
        """测试初始化"""
        ctx = ContextAccumulator()
        assert ctx.query == ""
        assert len(ctx.tool_results) == 0
        assert len(ctx.rag_documents) == 0
        assert len(ctx.layer_history) == 0

    def test_set_query(self):
        """测试设置查询"""
        ctx = ContextAccumulator()
        ctx.set_query("北京天气怎么样")
        assert ctx.query == "北京天气怎么样"
        assert len(ctx.layer_history) == 1

    def test_add_tool_result(self):
        """测试添加工具结果"""
        ctx = ContextAccumulator()
        ctx.add_tool_result("weather", "北京晴天", {"city": "北京"})

        assert "weather" in ctx.tool_results
        assert ctx.tool_results["weather"]["result"] == "北京晴天"
        assert ctx.tool_results["weather"]["entities"]["city"] == "北京"
        assert ctx.has_tool_results()

    def test_add_rag_documents(self):
        """测试添加RAG文档"""
        ctx = ContextAccumulator()
        docs = [
            Document(page_content="一线城市住宿标准500元", metadata={"source": "policy.txt"})
        ]
        ctx.add_rag_documents(docs)

        assert len(ctx.rag_documents) == 1
        assert ctx.has_rag_documents()

    def test_get_synthesis_context(self):
        """测试获取综合上下文"""
        ctx = ContextAccumulator()
        ctx.set_query("北京天气和住宿标准")
        ctx.add_tool_result("weather", "北京晴天", {"city": "北京"})
        ctx.add_rag_documents([
            Document(page_content="一线城市住宿标准500元")
        ])

        context_str = ctx.get_synthesis_context()
        assert "北京天气和住宿标准" in context_str
        assert "weather" in context_str
        assert "北京晴天" in context_str
        assert "一线城市住宿标准500元" in context_str

    def test_clear(self):
        """测试清空上下文"""
        ctx = ContextAccumulator()
        ctx.set_query("test")
        ctx.add_tool_result("weather", "result", {})
        ctx.clear()

        assert ctx.query == ""
        assert len(ctx.tool_results) == 0
        assert len(ctx.rag_documents) == 0


class TestSynthesisLayer:
    """测试综合分析层"""

    def test_initialization(self):
        """测试初始化"""
        mock_llm = Mock()
        layer = SynthesisLayer(mock_llm)
        assert layer.llm == mock_llm
        # synthesis_chain 已在 API 迁移中移除，不再需要此属性

    def test_fallback_analysis_with_both(self):
        """测试降级分析：有工具结果和RAG文档"""
        mock_llm = Mock()
        layer = SynthesisLayer(mock_llm)

        ctx = ContextAccumulator()
        ctx.set_query("test")
        ctx.add_tool_result("weather", "晴天", {})
        ctx.add_rag_documents([Document(page_content="test doc")])

        result = layer._fallback_analysis(ctx)
        assert result["complete"] is True
        assert result["answer"] is not None
        assert "weather" in result["reasoning"]

    def test_fallback_analysis_with_tool_only(self):
        """测试降级分析：只有工具结果"""
        mock_llm = Mock()
        layer = SynthesisLayer(mock_llm)

        ctx = ContextAccumulator()
        ctx.set_query("test")
        ctx.add_tool_result("weather", "晴天", {})

        result = layer._fallback_analysis(ctx)
        assert result["complete"] is True
        assert "weather" in result["answer"]

    def test_fallback_analysis_with_rag_only(self):
        """测试降级分析：只有RAG文档"""
        mock_llm = Mock()
        layer = SynthesisLayer(mock_llm)

        ctx = ContextAccumulator()
        ctx.set_query("test")
        ctx.add_rag_documents([Document(page_content="test doc")])

        result = layer._fallback_analysis(ctx)
        assert result["complete"] is True

    def test_fallback_analysis_with_nothing(self):
        """测试降级分析：无工具结果也无RAG文档"""
        mock_llm = Mock()
        layer = SynthesisLayer(mock_llm)

        ctx = ContextAccumulator()
        ctx.set_query("test")

        result = layer._fallback_analysis(ctx)
        assert result["complete"] is False
        assert result["next_action"] is not None


class TestIntelligentRouterFixed:
    """测试修正后的智能路由器"""

    @pytest.fixture
    def mock_components(self):
        """创建模拟组件"""
        mock_llm = Mock()
        mock_retriever = Mock()
        mock_rag_chain = Mock()
        mock_tools = {}

        return mock_llm, mock_retriever, mock_rag_chain, mock_tools

    def test_layer0_saves_tool_result(self, mock_components):
        """测试Layer 0保存工具结果（不返回）"""
        mock_llm, mock_retriever, mock_rag_chain, mock_tools = mock_components

        # Mock retriever返回空文档
        mock_retriever.get_relevant_documents.return_value = []

        router = IntelligentRouter(
            llm=mock_llm,
            retriever=mock_retriever,
            rag_chain=mock_rag_chain,
            tools=mock_tools
        )

        # Mock工具调用
        with patch.object(router, '_handle_tool_call', return_value="北京晴天"):
            # Mock synthesis返回完整答案
            with patch.object(router.synthesis_layer, 'synthesize', return_value={
                "complete": True,
                "confidence": 0.9,
                "answer": "北京今天晴天，温度18-25℃",
                "reasoning": "基于工具结果",
                "next_action": None
            }):
                result = router.route("北京天气怎么样")

        # 验证：应该走到综合分析层而不是直接返回
        assert result["route"] == "synthesis"
        assert "answer" in result

        # 验证：上下文中保存了工具结果
        assert router.context.has_tool_results()

    def test_layer1_retrieves_for_all_queries(self, mock_components):
        """测试Layer 1对所有查询都执行RAG检索"""
        mock_llm, mock_retriever, mock_rag_chain, mock_tools = mock_components

        # Mock retriever返回文档
        mock_retriever.get_relevant_documents.return_value = [
            Document(page_content="北京住宿标准500元")
        ]

        router = IntelligentRouter(
            llm=mock_llm,
            retriever=mock_retriever,
            rag_chain=mock_rag_chain,
            tools=mock_tools
        )

        # Mock synthesis返回完整答案
        with patch.object(router.synthesis_layer, 'synthesize', return_value={
            "complete": True,
            "confidence": 0.9,
            "answer": "北京住宿标准是500元/晚",
            "reasoning": "基于RAG文档",
            "next_action": None
        }):
            result = router.route("北京住宿标准")

        # 验证：调用了retriever
        mock_retriever.get_relevant_documents.assert_called_once_with("北京住宿标准")

        # 验证：上下文中保存了文档
        assert router.context.has_rag_documents()
        assert len(router.context.rag_documents) == 1

    def test_layer2_synthesis_complete(self, mock_components):
        """测试Layer 2综合分析：信息充足"""
        mock_llm, mock_retriever, mock_rag_chain, mock_tools = mock_components

        mock_retriever.get_relevant_documents.return_value = [
            Document(page_content="北京住宿标准500元")
        ]

        router = IntelligentRouter(
            llm=mock_llm,
            retriever=mock_retriever,
            rag_chain=mock_rag_chain,
            tools=mock_tools
        )

        # Mock synthesis返回完整答案
        with patch.object(router.synthesis_layer, 'synthesize', return_value={
            "complete": True,
            "confidence": 0.95,
            "answer": "根据政策，北京住宿标准是500元/晚",
            "reasoning": "RAG文档提供了明确答案",
            "next_action": None
        }):
            result = router.route("北京住宿标准")

        # 验证：路由到synthesis
        assert result["route"] == "synthesis"
        assert result["answer"] == "根据政策，北京住宿标准是500元/晚"
        assert "synthesis_confidence" in result
        assert result["synthesis_confidence"] == 0.95

    def test_layer2_orchestration_fallback(self, mock_components):
        """测试Layer 2综合分析：信息不足，调用编排器兜底"""
        mock_llm, mock_retriever, mock_rag_chain, mock_tools = mock_components

        mock_retriever.get_relevant_documents.return_value = []

        router = IntelligentRouter(
            llm=mock_llm,
            retriever=mock_retriever,
            rag_chain=mock_rag_chain,
            tools=mock_tools
        )

        # Mock synthesis返回需要更多工具
        with patch.object(router.synthesis_layer, 'synthesize', return_value={
            "complete": False,
            "confidence": 0.3,
            "answer": None,
            "reasoning": "需要查询天气和酒店信息",
            "next_action": "需要weather和hotel工具"
        }):
            # Mock orchestrator返回结果
            with patch.object(router.workflow_orchestrator, 'route', return_value="综合答案"):
                result = router.route("去杭州出差，查天气并推荐酒店")

        # 验证：路由到orchestration_fallback
        assert result["route"] == "orchestration_fallback"
        assert result["answer"] == "综合答案"
        assert "synthesis_reasoning" in result

    def test_statistics_updated(self, mock_components):
        """测试统计数据正确更新"""
        mock_llm, mock_retriever, mock_rag_chain, mock_tools = mock_components

        mock_retriever.get_relevant_documents.return_value = []

        router = IntelligentRouter(
            llm=mock_llm,
            retriever=mock_retriever,
            rag_chain=mock_rag_chain,
            tools=mock_tools
        )

        # 执行一次综合查询
        with patch.object(router.synthesis_layer, 'synthesize', return_value={
            "complete": True,
            "confidence": 0.9,
            "answer": "答案",
            "reasoning": "测试",
            "next_action": None
        }):
            router.route("测试查询")

        # 验证统计
        assert router.stats["total_queries"] == 1
        assert router.stats["synthesis_queries"] == 1
        assert router.stats["avg_synthesis_latency"] >= 0  # Mock 场景下延迟可能为0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
