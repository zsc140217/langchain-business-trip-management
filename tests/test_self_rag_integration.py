"""
Self-RAG集成测试

测试实际的LLM调用和完整流程（需要.env配置）
"""
import pytest
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 如果没有API密钥，跳过集成测试
skip_integration = not os.getenv("DASHSCOPE_API_KEY") or not os.getenv("DASHSCOPE_BASE_URL")


@pytest.mark.skipif(skip_integration, reason="需要配置DASHSCOPE_API_KEY和DASHSCOPE_BASE_URL")
class TestQueryClassifierIntegration:
    """查询分类器集成测试"""

    def test_classify_with_real_llm(self):
        """使用真实LLM测试分类"""
        from src.rag.query_classifier import QueryClassifier

        classifier = QueryClassifier()

        # 测试闲聊
        result = classifier.classify("你好")
        assert result["type"] in ["CHITCHAT", "FACTUAL"]
        assert 0 <= result["confidence"] <= 1

        # 测试事实性查询
        result = classifier.classify("去上海出差住宿能报多少钱")
        assert result["type"] in ["CHITCHAT", "FACTUAL"]
        assert 0 <= result["confidence"] <= 1

    def test_fallback_classify(self):
        """测试启发式规则后备方案"""
        from src.rag.query_classifier import QueryClassifier

        classifier = QueryClassifier()

        # 测试启发式规则
        result = classifier._fallback_classify("你好")
        assert result["type"] == "CHITCHAT"

        result = classifier._fallback_classify("北京出差住宿标准")
        assert result["type"] == "FACTUAL"

        result = classifier._fallback_classify("随机文本xyz123")
        assert result["type"] == "CHITCHAT"  # 默认返回CHITCHAT


@pytest.mark.skipif(skip_integration, reason="需要配置API密钥和文档")
class TestSelfRAGIntegration:
    """Self-RAG集成测试"""

    @pytest.mark.skip(reason="需要真实的retriever对象支持LCEL管道操作")
    def test_full_rag_flow(self):
        """测试完整的RAG流程"""
        from src.rag.self_rag import SelfRAG
        from langchain_core.documents import Document
        from unittest.mock import Mock

        # 准备测试文档 - 使用mock的retriever避免依赖loader
        mock_retriever = Mock()
        mock_retriever.invoke.return_value = [
            Document(page_content="一线城市住宿标准500元/晚")
        ]

        # 创建Self-RAG
        self_rag = SelfRAG(retriever=mock_retriever)

        # 测试闲聊
        result = self_rag.query("你好")
        assert result["answer"] is not None
        assert isinstance(result["retrieved"], bool)
        assert "classification" in result

        # 测试事实性查询
        result = self_rag.query("去上海出差住宿标准是多少")
        assert result["answer"] is not None
        assert isinstance(result["retrieved"], bool)
        assert "classification" in result


class TestQueryClassifierEdgeCases:
    """查询分类器边界情况测试（无需LLM）"""

    def test_fallback_with_various_queries(self):
        """测试各种查询的启发式分类"""
        from src.rag.query_classifier import QueryClassifier

        classifier = QueryClassifier()

        # 测试问候语
        test_cases = [
            ("你好", "CHITCHAT"),
            ("谢谢", "CHITCHAT"),
            ("再见", "CHITCHAT"),
            ("今天天气怎么样", "CHITCHAT"),
            ("住宿标准", "FACTUAL"),
            ("报销多少", "FACTUAL"),
            ("北京差旅", "FACTUAL"),
            ("上海出差", "FACTUAL"),
        ]

        for query, expected_type in test_cases:
            result = classifier._fallback_classify(query)
            assert result["type"] == expected_type, f"查询'{query}'应该是{expected_type}"

    def test_json_parsing_edge_cases(self):
        """测试JSON解析边界情况"""
        from src.rag.query_classifier import QueryClassifier
        from unittest.mock import Mock, patch

        with patch('src.rag.query_classifier.get_llm') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm

            # 测试格式错误的JSON - 应该fallback到启发式规则
            mock_response = Mock()
            mock_response.content = '这不是JSON'
            mock_llm.invoke.return_value = mock_response

            classifier = QueryClassifier()
            result = classifier.classify("住宿标准")  # 使用会触发FACTUAL的关键词
            assert result["type"] in ["FACTUAL", "CHITCHAT"]

            # 测试部分JSON
            mock_response2 = Mock()
            mock_response2.content = '一些文本 {"type": "FACTUAL", "confidence": 0.8, "reason": "测试"} 更多文本'
            mock_llm.invoke.return_value = mock_response2

            result = classifier.classify("测试")
            assert result["type"] == "FACTUAL"


class TestSelfRAGErrorHandling:
    """Self-RAG错误处理测试"""

    def test_invalid_query_types(self):
        """测试各种无效查询类型"""
        from src.rag.self_rag import SelfRAG
        from unittest.mock import Mock

        mock_llm = Mock()
        mock_classifier = Mock()
        mock_retriever = Mock()

        self_rag = SelfRAG(retriever=mock_retriever, llm=mock_llm, classifier=mock_classifier)

        # 测试None
        with pytest.raises(ValueError):
            self_rag.query(None)

        # 测试空字符串
        with pytest.raises(ValueError):
            self_rag.query("")

        # 测试只有空格
        with pytest.raises(ValueError):
            self_rag.query("   ")

    def test_missing_classification_fields(self):
        """测试分类结果缺少字段的处理"""
        from src.rag.self_rag import SelfRAG
        from unittest.mock import Mock

        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="回答")

        mock_classifier = Mock()
        # 返回不完整的分类结果
        mock_classifier.classify.return_value = {
            "type": "CHITCHAT"
            # 缺少confidence和reason
        }

        mock_retriever = Mock()

        self_rag = SelfRAG(retriever=mock_retriever, llm=mock_llm, classifier=mock_classifier)

        # 应该能正常处理
        result = self_rag.query("测试")
        assert "answer" in result
        assert "classification" in result
