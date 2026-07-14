"""
GraphRAG 系统集成测试

测试 IntelligentRetriever 与 GraphRetriever 的集成：
1. 查询分类（GRAPH / FACTUAL / CHITCHAT）
2. 智能路由到不同检索器
3. 降级机制验证
4. 端到端检索流程
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from langchain_core.documents import Document

from src.rag.intelligent_retriever import IntelligentRetriever
from src.rag.query_classifier import QueryClassifier
from src.rag.graph_retriever import GraphRetriever


class TestQueryClassifierWithGraph:
    """测试查询分类器的 GRAPH 类型支持"""

    def test_graph_query_classification(self):
        """测试图谱查询分类（使用 Mock LLM）"""
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content='{"type": "GRAPH", "confidence": 0.90, "reason": "包含关系查询"}')

        classifier = QueryClassifier(llm=mock_llm)

        # 测试关系查询
        result = classifier.classify("副总和总监的汇报关系")
        assert result['type'] == 'GRAPH'
        assert result['confidence'] == 0.90

    def test_factual_query_classification(self):
        """测试事实性查询分类（使用 Mock LLM）"""
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content='{"type": "FACTUAL", "confidence": 0.92, "reason": "询问政策数值"}')

        classifier = QueryClassifier(llm=mock_llm)

        result = classifier.classify("北京的住宿标准是多少")
        assert result['type'] == 'FACTUAL'
        assert result['confidence'] > 0.5

    def test_chitchat_query_classification(self):
        """测试闲聊查询分类（使用 Mock LLM）"""
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content='{"type": "CHITCHAT", "confidence": 0.95, "reason": "问候语"}')

        classifier = QueryClassifier(llm=mock_llm)

        result = classifier.classify("你好")
        assert result['type'] == 'CHITCHAT'
        assert result['confidence'] > 0.5

    def test_fallback_classify_graph_keywords(self):
        """测试启发式规则识别图谱关键词"""
        mock_llm = Mock()
        classifier = QueryClassifier(llm=mock_llm)

        # 包含"关系"关键词
        result = classifier._fallback_classify("A 和 B 的关系")
        assert result['type'] == 'GRAPH'

        # 包含"汇报"关键词
        result = classifier._fallback_classify("谁向谁汇报")
        assert result['type'] == 'GRAPH'


class TestIntelligentRetriever:
    """测试智能路由检索器"""

    @pytest.fixture
    def mock_retrievers(self):
        """创建 Mock 检索器"""
        vector_retriever = Mock()
        vector_retriever.get_relevant_documents.return_value = [
            Document(page_content="向量检索结果", metadata={'source': 'vector'})
        ]

        bm25_retriever = Mock()
        bm25_retriever.get_relevant_documents.return_value = [
            Document(page_content="BM25检索结果", metadata={'source': 'bm25'})
        ]

        graph_retriever = Mock(spec=GraphRetriever)
        graph_retriever.retrieve.return_value = [
            Document(page_content="图谱检索结果", metadata={'source': 'graph'})
        ]

        return vector_retriever, bm25_retriever, graph_retriever

    def test_initialization(self, mock_retrievers):
        """测试初始化"""
        vector_retriever, bm25_retriever, graph_retriever = mock_retrievers

        # Mock 分类器以避免 LLM 依赖
        mock_classifier = Mock()

        retriever = IntelligentRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            graph_retriever=graph_retriever,
            classifier=mock_classifier,
            enable_graph=True
        )

        assert retriever.vector_retriever == vector_retriever
        assert retriever.bm25_retriever == bm25_retriever
        assert retriever.graph_retriever == graph_retriever
        assert retriever.enable_graph is True
        assert retriever.stats['total_queries'] == 0

    def test_chitchat_query_skips_retrieval(self, mock_retrievers):
        """测试 CHITCHAT 查询跳过检索"""
        vector_retriever, bm25_retriever, graph_retriever = mock_retrievers

        # Mock 分类器返回 CHITCHAT
        mock_classifier = Mock()
        mock_classifier.classify.return_value = {
            'type': 'CHITCHAT',
            'confidence': 0.95,
            'reason': '问候语'
        }

        retriever = IntelligentRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            graph_retriever=graph_retriever,
            classifier=mock_classifier,
            enable_graph=True
        )

        # 执行查询
        results = retriever.get_relevant_documents("你好", top_k=5)

        # 验证
        assert results == []  # 应返回空列表
        assert retriever.stats['chitchat_queries'] == 1
        assert retriever.stats['total_queries'] == 1

        # 验证没有调用任何检索器
        vector_retriever.get_relevant_documents.assert_not_called()
        graph_retriever.retrieve.assert_not_called()

    def test_graph_query_uses_graph_retriever(self, mock_retrievers):
        """测试 GRAPH 查询使用图谱检索器"""
        vector_retriever, bm25_retriever, graph_retriever = mock_retrievers

        # Mock 分类器返回 GRAPH
        mock_classifier = Mock()
        mock_classifier.classify.return_value = {
            'type': 'GRAPH',
            'confidence': 0.90,
            'reason': '包含关系查询关键词'
        }

        retriever = IntelligentRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            graph_retriever=graph_retriever,
            classifier=mock_classifier,
            enable_graph=True
        )

        # 执行查询
        results = retriever.get_relevant_documents("副总和总监的关系", top_k=5)

        # 验证
        assert len(results) == 1
        assert results[0].page_content == "图谱检索结果"
        assert retriever.stats['graph_queries'] == 1

        # 验证调用了图谱检索器
        graph_retriever.retrieve.assert_called_once_with("副总和总监的关系", top_k=5)

    def test_factual_query_uses_fusion_retriever(self, mock_retrievers):
        """测试 FACTUAL 查询使用融合检索器"""
        vector_retriever, bm25_retriever, graph_retriever = mock_retrievers

        # Mock 分类器返回 FACTUAL
        mock_classifier = Mock()
        mock_classifier.classify.return_value = {
            'type': 'FACTUAL',
            'confidence': 0.92,
            'reason': '询问政策数值'
        }

        retriever = IntelligentRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            graph_retriever=graph_retriever,
            classifier=mock_classifier,
            enable_graph=True
        )

        # 执行查询
        results = retriever.get_relevant_documents("北京的住宿标准", top_k=5)

        # 验证
        assert len(results) > 0
        assert retriever.stats['factual_queries'] == 1

    def test_graph_retriever_fallback_to_fusion(self, mock_retrievers):
        """测试图谱检索失败时降级到融合检索"""
        vector_retriever, bm25_retriever, graph_retriever = mock_retrievers

        # Mock 图谱检索器返回空结果
        graph_retriever.retrieve.return_value = []

        # Mock 分类器返回 GRAPH
        mock_classifier = Mock()
        mock_classifier.classify.return_value = {
            'type': 'GRAPH',
            'confidence': 0.90,
            'reason': '包含关系查询关键词'
        }

        retriever = IntelligentRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            graph_retriever=graph_retriever,
            classifier=mock_classifier,
            enable_graph=True
        )

        # 执行查询
        results = retriever.get_relevant_documents("副总和总监的关系", top_k=5)

        # 验证：应该降级到融合检索
        assert len(results) > 0
        # 验证图谱检索器被调用了
        graph_retriever.retrieve.assert_called_once()

    def test_graph_retriever_exception_fallback(self, mock_retrievers):
        """测试图谱检索异常时降级"""
        vector_retriever, bm25_retriever, graph_retriever = mock_retrievers

        # Mock 图谱检索器抛出异常
        graph_retriever.retrieve.side_effect = Exception("Neo4j connection failed")

        # Mock 分类器返回 GRAPH
        mock_classifier = Mock()
        mock_classifier.classify.return_value = {
            'type': 'GRAPH',
            'confidence': 0.90,
            'reason': '包含关系查询关键词'
        }

        retriever = IntelligentRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            graph_retriever=graph_retriever,
            classifier=mock_classifier,
            enable_graph=True
        )

        # 执行查询（不应该抛出异常）
        results = retriever.get_relevant_documents("副总和总监的关系", top_k=5)

        # 验证：应该降级到融合检索
        assert len(results) > 0

    def test_graph_disabled_fallback_to_fusion(self, mock_retrievers):
        """测试禁用图谱时 GRAPH 查询降级到融合检索"""
        vector_retriever, bm25_retriever, graph_retriever = mock_retrievers

        # Mock 分类器返回 GRAPH
        mock_classifier = Mock()
        mock_classifier.classify.return_value = {
            'type': 'GRAPH',
            'confidence': 0.90,
            'reason': '包含关系查询关键词'
        }

        # 禁用图谱检索
        retriever = IntelligentRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            graph_retriever=graph_retriever,
            classifier=mock_classifier,
            enable_graph=False  # 禁用
        )

        # 执行查询
        results = retriever.get_relevant_documents("副总和总监的关系", top_k=5)

        # 验证：不应该调用图谱检索器
        graph_retriever.retrieve.assert_not_called()
        # 应该使用融合检索
        assert len(results) > 0

    def test_statistics_tracking(self, mock_retrievers):
        """测试统计信息追踪"""
        vector_retriever, bm25_retriever, graph_retriever = mock_retrievers

        mock_classifier = Mock()

        retriever = IntelligentRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            graph_retriever=graph_retriever,
            classifier=mock_classifier,
            enable_graph=True
        )

        # 模拟不同类型的查询
        mock_classifier.classify.return_value = {'type': 'CHITCHAT', 'confidence': 0.9, 'reason': ''}
        retriever.get_relevant_documents("你好", top_k=5)

        mock_classifier.classify.return_value = {'type': 'FACTUAL', 'confidence': 0.9, 'reason': ''}
        retriever.get_relevant_documents("住宿标准", top_k=5)

        mock_classifier.classify.return_value = {'type': 'GRAPH', 'confidence': 0.9, 'reason': ''}
        retriever.get_relevant_documents("关系查询", top_k=5)

        # 获取统计信息
        stats = retriever.get_statistics()

        assert stats['total_queries'] == 3
        assert stats['chitchat_queries'] == 1
        assert stats['factual_queries'] == 1
        assert stats['graph_queries'] == 1
        assert stats['chitchat_rate'] == pytest.approx(1/3)
        assert stats['factual_rate'] == pytest.approx(1/3)
        assert stats['graph_rate'] == pytest.approx(1/3)

    def test_reset_statistics(self, mock_retrievers):
        """测试重置统计信息"""
        vector_retriever, bm25_retriever, graph_retriever = mock_retrievers

        mock_classifier = Mock()
        mock_classifier.classify.return_value = {'type': 'FACTUAL', 'confidence': 0.9, 'reason': ''}

        retriever = IntelligentRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            graph_retriever=graph_retriever,
            classifier=mock_classifier,
            enable_graph=True
        )

        # 执行查询
        retriever.get_relevant_documents("测试", top_k=5)
        assert retriever.stats['total_queries'] == 1

        # 重置统计
        retriever.reset_statistics()
        assert retriever.stats['total_queries'] == 0
        assert retriever.stats['factual_queries'] == 0


class TestEndToEndIntegration:
    """端到端集成测试（需要真实环境）"""

    @pytest.mark.skip(reason="需要真实 LLM 和 Neo4j 环境")
    def test_full_graph_query_flow(self):
        """测试完整的图谱查询流程"""
        from src.rag.retriever import create_vectorstore, get_retriever
        from src.rag.loader import load_documents_from_text
        from src.rag.hybrid_retriever import ChineseBM25Retriever
        from src.rag.graph_retriever import GraphRetriever

        # 准备测试数据
        test_text = """
        企业差旅管理规章

        第一章 组织架构
        1. 副总向CEO汇报
        2. 总监向副总汇报
        3. 经理向总监汇报
        """

        docs = load_documents_from_text(test_text, chunk_size=200)

        # 创建检索器
        vectorstore = create_vectorstore(docs)
        vector_retriever = get_retriever(vectorstore, k=5)
        bm25_retriever = ChineseBM25Retriever.from_documents(docs)
        graph_retriever = GraphRetriever()

        # 创建智能检索器
        intelligent_retriever = IntelligentRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            graph_retriever=graph_retriever,
            enable_graph=True
        )

        # 测试图谱查询
        results = intelligent_retriever.get_relevant_documents(
            "副总和总监的汇报关系",
            top_k=3
        )

        assert len(results) > 0
        assert intelligent_retriever.stats['graph_queries'] >= 1


if __name__ == "__main__":
    """直接运行测试"""
    pytest.main([__file__, "-v", "--tb=short"])
