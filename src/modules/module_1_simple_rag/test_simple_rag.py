"""
Module 1: Simple RAG - Unit Tests
单元测试模块

测试覆盖：
1. 文档加载和切分
2. 向量存储创建和检索
3. RAG链问答功能
"""
import unittest
import os
import sys
from unittest.mock import Mock, patch
from langchain_core.documents import Document

# Add module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestLoader(unittest.TestCase):
    """测试文档加载模块"""

    def test_load_documents_from_text(self):
        """测试从文本加载文档"""
        from loader import load_documents_from_text

        text = "这是第一段。\n\n这是第二段。"
        docs = load_documents_from_text(text, chunk_size=50, chunk_overlap=10)

        self.assertIsInstance(docs, list)
        self.assertTrue(len(docs) > 0)
        self.assertIsInstance(docs[0], Document)

    def test_chunk_size(self):
        """测试块大小限制"""
        from loader import load_documents_from_text

        text = "a" * 1000
        docs = load_documents_from_text(text, chunk_size=200, chunk_overlap=0)

        for doc in docs:
            self.assertLessEqual(len(doc.page_content), 220)  # 允许少量超出

    def test_empty_text(self):
        """测试空文本"""
        from loader import load_documents_from_text

        text = ""
        docs = load_documents_from_text(text, chunk_size=100)

        # 空文本应该返回空列表或包含一个空文档
        self.assertIsInstance(docs, list)


class TestRetriever(unittest.TestCase):
    """测试检索器模块"""

    @patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test_key"})
    @patch("retriever.DashScopeEmbeddings")
    @patch("retriever.FAISS")
    def test_create_vectorstore(self, mock_faiss, mock_embeddings):
        """测试向量存储创建"""
        from retriever import create_faiss_vectorstore

        # Mock数据
        docs = [Document(page_content="测试文档")]
        mock_faiss.from_documents.return_value = Mock()

        # 调用函数
        vectorstore = create_faiss_vectorstore(docs)

        # 验证
        self.assertIsNotNone(vectorstore)
        mock_embeddings.assert_called_once()
        mock_faiss.from_documents.assert_called_once()

    def test_create_vectorstore_no_api_key(self):
        """测试缺少API Key的情况"""
        from retriever import create_faiss_vectorstore

        # 清除环境变量
        with patch.dict(os.environ, {}, clear=True):
            docs = [Document(page_content="测试文档")]

            with self.assertRaises(ValueError) as context:
                create_faiss_vectorstore(docs)

            self.assertIn("DASHSCOPE_API_KEY", str(context.exception))

    @patch("retriever.FAISS")
    def test_create_retriever(self, mock_faiss):
        """测试检索器创建"""
        from retriever import create_retriever

        # Mock向量存储
        mock_vectorstore = Mock()
        mock_vectorstore.as_retriever.return_value = Mock()

        # 创建检索器
        retriever = create_retriever(mock_vectorstore, k=3)

        # 验证
        self.assertIsNotNone(retriever)
        mock_vectorstore.as_retriever.assert_called_once()


class TestChain(unittest.TestCase):
    """测试RAG链模块"""

    @patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test_key"})
    @patch("chain.Tongyi")
    def test_create_rag_chain_lcel(self, mock_tongyi):
        """测试LCEL链创建"""
        from chain import create_rag_chain_lcel

        # Mock检索器和LLM
        mock_retriever = Mock()
        mock_llm = Mock()
        mock_tongyi.return_value = mock_llm

        # 创建链
        chain = create_rag_chain_lcel(mock_retriever)

        # 验证链对象存在
        self.assertIsNotNone(chain)

    def test_format_docs(self):
        """测试文档格式化"""
        from chain import format_docs

        docs = [
            Document(page_content="文档1"),
            Document(page_content="文档2"),
        ]

        result = format_docs(docs)

        self.assertIn("文档1", result)
        self.assertIn("文档2", result)
        self.assertEqual(result, "文档1\n\n文档2")


class TestIntegration(unittest.TestCase):
    """集成测试"""

    @unittest.skipIf(not os.getenv("DASHSCOPE_API_KEY"), "需要API Key进行集成测试")
    def test_end_to_end(self):
        """端到端测试（需要真实API Key）"""
        from loader import load_documents_from_text
        from retriever import create_faiss_vectorstore, create_retriever
        from chain import create_rag_chain_lcel

        # 准备测试数据
        text = """
        企业差旅管理规章
        第一章 住宿标准
        1. 一线城市：标准间不超过500元/晚
        2. 二线城市：标准间不超过400元/晚
        """

        # 完整流程
        docs = load_documents_from_text(text, chunk_size=100)
        self.assertTrue(len(docs) > 0)

        vectorstore = create_faiss_vectorstore(docs)
        self.assertIsNotNone(vectorstore)

        retriever = create_retriever(vectorstore, k=2)
        self.assertIsNotNone(retriever)

        rag_chain = create_rag_chain_lcel(retriever)
        self.assertIsNotNone(rag_chain)

        # 测试问答
        answer = rag_chain.invoke("一线城市住宿标准是多少？")
        self.assertIsInstance(answer, str)
        self.assertTrue(len(answer) > 0)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestRetriever))
    suite.addTests(loader.loadTestsFromTestCase(TestChain))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("=" * 60)
    print("Module 1: Simple RAG - 单元测试")
    print("=" * 60 + "\n")

    success = run_tests()

    print("\n" + "=" * 60)
    if success:
        print("[OK] 所有测试通过！")
    else:
        print("[FAIL] 部分测试失败")
    print("=" * 60)
