"""
Self-RAG测试套件

测试查询分类器和自适应RAG检索功能
"""
import pytest
from unittest.mock import Mock, patch
from langchain_core.documents import Document


class TestQueryClassifier:
    """查询分类器测试"""

    @patch('src.rag.query_classifier.get_llm')
    def test_classify_chitchat_greeting(self, mock_get_llm):
        """测试问候语分类为CHITCHAT"""
        from src.rag.query_classifier import QueryClassifier

        # Mock LLM响应
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"type": "CHITCHAT", "confidence": 0.9, "reason": "问候语"}'
        )
        mock_get_llm.return_value = mock_llm

        classifier = QueryClassifier()
        result = classifier.classify("你好")

        assert result["type"] == "CHITCHAT"
        assert "confidence" in result
        assert "reason" in result
        assert result["confidence"] > 0.5

    @patch('src.rag.query_classifier.get_llm')
    def test_classify_factual_policy(self, mock_get_llm):
        """测试政策查询分类为FACTUAL"""
        from src.rag.query_classifier import QueryClassifier

        # Mock LLM响应
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"type": "FACTUAL", "confidence": 0.95, "reason": "询问具体政策和数值"}'
        )
        mock_get_llm.return_value = mock_llm

        classifier = QueryClassifier()
        result = classifier.classify("去上海出差住宿能报多少钱")

        assert result["type"] == "FACTUAL"
        assert result["confidence"] > 0.5
        assert "reason" in result

    @patch('src.rag.query_classifier.get_llm')
    def test_classify_chitchat_general(self, mock_get_llm):
        """测试通用知识查询分类为CHITCHAT"""
        from src.rag.query_classifier import QueryClassifier

        # Mock LLM响应
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"type": "CHITCHAT", "confidence": 0.85, "reason": "通用常识问题"}'
        )
        mock_get_llm.return_value = mock_llm

        classifier = QueryClassifier()
        result = classifier.classify("今天天气怎么样")

        assert result["type"] == "CHITCHAT"
        assert result["confidence"] > 0.5

    @patch('src.rag.query_classifier.get_llm')
    def test_classify_factual_with_location(self, mock_get_llm):
        """测试带地点的政策查询分类为FACTUAL"""
        from src.rag.query_classifier import QueryClassifier

        # Mock LLM响应
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"type": "FACTUAL", "confidence": 0.92, "reason": "询问具体地点的差旅标准"}'
        )
        mock_get_llm.return_value = mock_llm

        classifier = QueryClassifier()
        result = classifier.classify("北京出差住宿标准")

        assert result["type"] == "FACTUAL"
        assert result["confidence"] > 0.5

    @patch('src.rag.query_classifier.get_llm')
    def test_classify_factual_with_number(self, mock_get_llm):
        """测试带数值的查询分类为FACTUAL"""
        from src.rag.query_classifier import QueryClassifier

        # Mock LLM响应
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"type": "FACTUAL", "confidence": 0.9, "reason": "询问具体数值"}'
        )
        mock_get_llm.return_value = mock_llm

        classifier = QueryClassifier()
        result = classifier.classify("出差能报销多少钱")

        assert result["type"] == "FACTUAL"
        assert result["confidence"] > 0.5

    @patch('src.rag.query_classifier.get_llm')
    def test_classify_empty_query(self, mock_get_llm):
        """测试空查询应抛出异常"""
        from src.rag.query_classifier import QueryClassifier

        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm

        classifier = QueryClassifier()
        with pytest.raises(ValueError, match="查询不能为空"):
            classifier.classify("")

    @patch('src.rag.query_classifier.get_llm')
    def test_classify_returns_valid_structure(self, mock_get_llm):
        """测试返回结构包含所有必需字段"""
        from src.rag.query_classifier import QueryClassifier

        # Mock LLM响应
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"type": "CHITCHAT", "confidence": 0.8, "reason": "测试"}'
        )
        mock_get_llm.return_value = mock_llm

        classifier = QueryClassifier()
        result = classifier.classify("测试查询")

        assert "type" in result
        assert "confidence" in result
        assert "reason" in result
        assert result["type"] in ["FACTUAL", "CHITCHAT"]
        assert 0 <= result["confidence"] <= 1


class TestSelfRAG:
    """自适应RAG测试"""

    def test_chitchat_no_retrieval(self):
        """测试闲聊查询不触发检索"""
        # Mock LLM实例
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="你好！我是企业差旅助手。")

        # Mock分类器
        mock_classifier = Mock()
        mock_classifier.classify.return_value = {
            "type": "CHITCHAT",
            "confidence": 0.9,
            "reason": "问候语"
        }

        from src.rag.self_rag import SelfRAG

        mock_retriever = Mock()
        # 直接传入mock的llm和classifier，避免自动创建
        self_rag = SelfRAG(retriever=mock_retriever, llm=mock_llm, classifier=mock_classifier)

        # 执行查询
        result = self_rag.query("你好")

        # 验证结果
        assert result["answer"] is not None
        assert result["retrieved"] is False
        assert result["sources"] is not None
        assert len(result["sources"]) == 0
        assert result["classification"]["type"] == "CHITCHAT"

    def test_factual_with_retrieval(self):
        """测试事实性查询触发检索"""
        with patch('src.rag.self_rag.create_rag_chain') as mock_create_rag_chain:
            # Mock LLM
            mock_llm = Mock()

            # Mock分类器
            mock_classifier = Mock()
            mock_classifier.classify.return_value = {
                "type": "FACTUAL",
                "confidence": 0.95,
                "reason": "询问具体政策"
            }

            # Mock RAG链响应
            mock_rag_chain = Mock()
            mock_rag_chain.invoke.return_value = {
                "result": "一线城市（上海）住宿标准为不超过500元/晚",
                "source_documents": [
                    Document(page_content="一线城市住宿标准500元/晚")
                ]
            }
            mock_create_rag_chain.return_value = mock_rag_chain

            from src.rag.self_rag import SelfRAG

            mock_retriever = Mock()
            self_rag = SelfRAG(retriever=mock_retriever, llm=mock_llm, classifier=mock_classifier)

            # 执行查询
            result = self_rag.query("去上海出差住宿能报多少钱")

            # 验证结果
            assert result["answer"] is not None
            assert result["retrieved"] is True
            assert result["sources"] is not None
            assert len(result["sources"]) > 0
            assert result["classification"]["type"] == "FACTUAL"

            # 验证调用了RAG链
            mock_create_rag_chain.assert_called_once()

    def test_answer_structure(self):
        """测试返回结构正确"""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="测试回答")

        # Mock分类器
        mock_classifier = Mock()
        mock_classifier.classify.return_value = {
            "type": "CHITCHAT",
            "confidence": 0.8,
            "reason": "问候"
        }

        from src.rag.self_rag import SelfRAG

        mock_retriever = Mock()
        self_rag = SelfRAG(retriever=mock_retriever, llm=mock_llm, classifier=mock_classifier)
        result = self_rag.query("你好")

        # 验证结构
        assert "answer" in result
        assert "retrieved" in result
        assert "sources" in result
        assert "classification" in result
        assert isinstance(result["retrieved"], bool)

    def test_sources_present_when_retrieved(self):
        """测试检索时包含来源文档"""
        with patch('src.rag.self_rag.create_rag_chain') as mock_create_rag_chain:
            # Mock LLM
            mock_llm = Mock()

            # Mock分类器
            mock_classifier = Mock()
            mock_classifier.classify.return_value = {
                "type": "FACTUAL",
                "confidence": 0.9,
                "reason": "政策查询"
            }

            # Mock RAG链返回源文档
            mock_doc = Document(
                page_content="住宿标准相关内容",
                metadata={"source": "policy.txt"}
            )
            mock_rag_chain = Mock()
            mock_rag_chain.invoke.return_value = {
                "result": "住宿标准答案",
                "source_documents": [mock_doc]
            }
            mock_create_rag_chain.return_value = mock_rag_chain

            from src.rag.self_rag import SelfRAG

            mock_retriever = Mock()
            self_rag = SelfRAG(retriever=mock_retriever, llm=mock_llm, classifier=mock_classifier)

            result = self_rag.query("北京出差住宿标准")

            # 验证源文档存在
            assert result["retrieved"] is True
            assert result["sources"] is not None
            assert len(result["sources"]) > 0
            assert result["sources"][0].page_content == "住宿标准相关内容"

    def test_empty_query_raises_error(self):
        """测试空查询抛出异常"""
        mock_llm = Mock()
        mock_classifier = Mock()

        from src.rag.self_rag import SelfRAG

        mock_retriever = Mock()
        self_rag = SelfRAG(retriever=mock_retriever, llm=mock_llm, classifier=mock_classifier)

        with pytest.raises(ValueError, match="查询不能为空"):
            self_rag.query("")

    def test_none_query_raises_error(self):
        """测试None查询抛出异常"""
        mock_llm = Mock()
        mock_classifier = Mock()

        from src.rag.self_rag import SelfRAG

        mock_retriever = Mock()
        self_rag = SelfRAG(retriever=mock_retriever, llm=mock_llm, classifier=mock_classifier)

        with pytest.raises(ValueError, match="查询不能为空"):
            self_rag.query(None)


class TestSelfRAGEdgeCases:
    """Self-RAG边界情况测试"""

    def test_low_confidence_classification(self):
        """测试低置信度分类的处理"""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="回答内容")

        # Mock分类器返回低置信度
        mock_classifier = Mock()
        mock_classifier.classify.return_value = {
            "type": "CHITCHAT",
            "confidence": 0.4,
            "reason": "不确定"
        }

        from src.rag.self_rag import SelfRAG

        mock_retriever = Mock()
        self_rag = SelfRAG(retriever=mock_retriever, llm=mock_llm, classifier=mock_classifier)

        # 对于模糊查询，系统应该能处理
        result = self_rag.query("这个")

        assert "answer" in result
        assert "classification" in result

    def test_retrieval_returns_empty_documents(self):
        """测试检索返回空文档的处理"""
        with patch('src.rag.self_rag.create_rag_chain') as mock_create_rag_chain:
            # Mock LLM
            mock_llm = Mock()

            # Mock分类器
            mock_classifier = Mock()
            mock_classifier.classify.return_value = {
                "type": "FACTUAL",
                "confidence": 0.85,
                "reason": "查询政策"
            }

            # Mock RAG链返回空文档
            mock_rag_chain = Mock()
            mock_rag_chain.invoke.return_value = {
                "result": "抱歉，我没有找到相关信息",
                "source_documents": []
            }
            mock_create_rag_chain.return_value = mock_rag_chain

            from src.rag.self_rag import SelfRAG

            mock_retriever = Mock()
            self_rag = SelfRAG(retriever=mock_retriever, llm=mock_llm, classifier=mock_classifier)

            result = self_rag.query("火星出差住宿标准")

            # 即使没有找到文档，也应该返回结果
            assert result["answer"] is not None
            assert result["retrieved"] is True
            assert len(result["sources"]) == 0
