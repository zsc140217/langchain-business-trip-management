"""
Unit Tests for PolicyAdvisorAgent

Tests:
- Policy query execution
- Query rewriting
- Document retrieval
- Answer generation
- Fallback mechanism
- Expense validation
"""
import pytest
from unittest.mock import Mock, MagicMock
from src.agents.policy_advisor_agent import PolicyAdvisorAgent


class TestPolicyAdvisorAgent:
    """Test suite for PolicyAdvisorAgent"""

    @pytest.fixture
    def mock_retriever(self):
        """Mock hybrid retriever"""
        mock = Mock()
        mock.retrieve = Mock(return_value=[
            {
                "content": "Accommodation policy: Maximum 500 RMB per night for tier-1 cities",
                "source": "policy_doc_001.pdf",
                "score": 0.95
            },
            {
                "content": "Meals policy: Maximum 200 RMB per day",
                "source": "policy_doc_002.pdf",
                "score": 0.87
            }
        ])
        return mock

    @pytest.fixture
    def mock_query_rewriter(self):
        """Mock query rewriter"""
        mock = Mock()
        mock.rewrite = Mock(side_effect=lambda q: f"{q} (rewritten)")
        return mock

    def test_agent_initialization(self, mock_llm, mock_retriever):
        """Test agent initialization"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=mock_retriever,
            config={"top_k": 5}
        )

        assert agent.name == "PolicyAdvisorAgent"
        assert agent.hybrid_retriever == mock_retriever
        assert agent.top_k == 5

    def test_execute_policy_query(self, mock_llm, mock_retriever, sample_policy_task):
        """Test executing policy query"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=mock_retriever
        )

        result = agent.execute(sample_policy_task)

        assert result is not None
        assert isinstance(result, str)
        mock_retriever.retrieve.assert_called_once()

    def test_execute_missing_query(self, mock_llm, mock_retriever):
        """Test execution with missing query field"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=mock_retriever
        )

        with pytest.raises(ValueError) as exc_info:
            agent.execute({"user_id": "test"})

        assert "Missing required fields" in str(exc_info.value)

    def test_execute_with_query_rewriting(self, mock_llm, mock_retriever, mock_query_rewriter):
        """Test execution with query rewriting enabled"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=mock_retriever,
            query_rewriter=mock_query_rewriter,
            config={"use_query_rewriting": True}
        )

        task = {
            "query": "accommodation policy",
            "user_id": "test"
        }

        result = agent.execute(task)

        assert result is not None
        mock_query_rewriter.rewrite.assert_called_once_with("accommodation policy")
        mock_retriever.retrieve.assert_called_once()

    def test_execute_without_query_rewriting(self, mock_llm, mock_retriever, mock_query_rewriter):
        """Test execution with query rewriting disabled"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=mock_retriever,
            query_rewriter=mock_query_rewriter,
            config={"use_query_rewriting": False}
        )

        task = {
            "query": "accommodation policy",
            "user_id": "test"
        }

        result = agent.execute(task)

        assert result is not None
        mock_query_rewriter.rewrite.assert_not_called()

    def test_rewrite_query_success(self, mock_llm, mock_query_rewriter):
        """Test successful query rewriting"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            query_rewriter=mock_query_rewriter
        )

        rewritten = agent._rewrite_query("original query")

        assert rewritten == "original query (rewritten)"
        mock_query_rewriter.rewrite.assert_called_once()

    def test_rewrite_query_failure(self, mock_llm):
        """Test query rewriting failure fallback"""
        mock_rewriter = Mock()
        mock_rewriter.rewrite = Mock(side_effect=Exception("Rewrite error"))

        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            query_rewriter=mock_rewriter
        )

        rewritten = agent._rewrite_query("original query")

        # Should fallback to original query
        assert rewritten == "original query"

    def test_retrieve_documents_success(self, mock_llm, mock_retriever):
        """Test successful document retrieval"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=mock_retriever
        )

        documents = agent._retrieve_documents("test query", "test query rewritten")

        assert len(documents) == 2
        assert documents[0]["score"] == 0.95
        mock_retriever.retrieve.assert_called_once()

    def test_retrieve_documents_no_retriever(self, mock_llm):
        """Test document retrieval without retriever"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=None
        )

        documents = agent._retrieve_documents("test query", "test query")

        assert documents == []

    def test_retrieve_documents_failure(self, mock_llm):
        """Test document retrieval failure"""
        mock_retriever = Mock()
        mock_retriever.retrieve = Mock(side_effect=Exception("Retrieval error"))

        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=mock_retriever
        )

        documents = agent._retrieve_documents("test query", "test query")

        assert documents == []

    def test_generate_answer_with_documents(self, mock_llm, mock_retriever):
        """Test answer generation with retrieved documents"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=mock_retriever
        )

        documents = [
            {
                "content": "Policy content",
                "source": "doc1.pdf",
                "score": 0.9
            }
        ]

        answer = agent._generate_answer("test query", documents, {})

        assert answer is not None
        assert "Sources:" in answer
        mock_llm.predict.assert_called_once()

    def test_generate_answer_without_documents(self, mock_llm):
        """Test answer generation without documents (fallback)"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm
        )

        answer = agent._generate_answer("test query", [], {})

        assert answer is not None
        assert "⚠️" in answer or "not based on" in answer.lower()

    def test_generate_answer_with_context(self, mock_llm):
        """Test answer generation with additional context"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm
        )

        documents = [{"content": "Policy", "source": "doc.pdf", "score": 0.9}]
        context = {"user_level": "senior", "department": "sales"}

        answer = agent._generate_answer("test query", documents, context)

        assert answer is not None

    def test_format_documents(self, mock_llm):
        """Test document formatting"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm
        )

        documents = [
            {"content": "Document 1 content", "source": "doc1.pdf", "score": 0.95},
            {"content": "Document 2 content", "source": "doc2.pdf", "score": 0.87}
        ]

        formatted = agent._format_documents(documents)

        assert "Document 1" in formatted
        assert "Document 2" in formatted
        assert "doc1.pdf" in formatted
        assert "doc2.pdf" in formatted
        assert "0.95" in formatted

    def test_fallback_answer(self, mock_llm):
        """Test fallback answer generation"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm
        )

        answer = agent._fallback_answer("What is the policy?")

        assert answer is not None
        assert "⚠️" in answer or "not based on" in answer.lower()

    def test_fallback_answer_llm_failure(self, mock_llm):
        """Test fallback answer when LLM also fails"""
        mock_llm.predict = Mock(side_effect=Exception("LLM error"))

        agent = PolicyAdvisorAgent(
            llm=mock_llm
        )

        answer = agent._fallback_answer("test query")

        assert answer is not None
        assert "unable to answer" in answer.lower()

    def test_validate_expense_simple(self, mock_llm, sample_expense):
        """Test expense validation"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm
        )

        validation = agent.validate_expense(sample_expense)

        assert "valid" in validation
        assert "violations" in validation
        assert "requires_approval" in validation
        assert isinstance(validation["valid"], bool)

    def test_validate_expense_high_amount(self, mock_llm):
        """Test expense validation with high amount"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm
        )

        expense = {
            "amount": 1000,
            "category": "accommodation",
            "city": "Beijing",
            "date": "2024-06-01",
            "description": "Hotel"
        }

        validation = agent.validate_expense(expense)

        assert validation["requires_approval"] is True

    def test_validate_expense_low_amount(self, mock_llm):
        """Test expense validation with low amount"""
        agent = PolicyAdvisorAgent(
            llm=mock_llm
        )

        expense = {
            "amount": 200,
            "category": "meals",
            "city": "Beijing",
            "date": "2024-06-01",
            "description": "Lunch"
        }

        validation = agent.validate_expense(expense)

        assert validation["requires_approval"] is False

    def test_execution_with_reranker(self, mock_llm, mock_retriever):
        """Test execution with reranker enabled"""
        mock_reranker = Mock()
        mock_reranker.rerank = Mock(side_effect=lambda q, docs: docs)

        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=mock_retriever,
            reranker=mock_reranker,
            config={"use_reranker": True}
        )

        task = {"query": "test query", "user_id": "test"}

        result = agent.execute(task)

        assert result is not None
        mock_reranker.rerank.assert_called_once()

    def test_execution_failure_fallback(self, mock_llm):
        """Test execution failure with fallback"""
        mock_retriever = Mock()
        mock_retriever.retrieve = Mock(side_effect=Exception("Retrieval error"))

        agent = PolicyAdvisorAgent(
            llm=mock_llm,
            hybrid_retriever=mock_retriever
        )

        task = {"query": "test query", "user_id": "test"}

        result = agent.execute(task)

        # Should fallback and still return a result
        assert result is not None
        assert "⚠️" in result or "not based on" in result.lower()
