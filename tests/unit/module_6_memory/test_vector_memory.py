"""
Tests for VectorMemory - 向量记忆测试
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from src.modules.module_6_memory.vector_memory import VectorMemory


class TestVectorMemory:
    """VectorMemory 测试类"""

    @pytest.fixture
    def mock_embeddings(self):
        """创建模拟的嵌入模型"""
        from langchain.embeddings.base import Embeddings

        class MockEmbeddings(Embeddings):
            def embed_documents(self, texts):
                return [[0.1] * 768 for _ in texts]

            def embed_query(self, text):
                return [0.1] * 768

        return MockEmbeddings()

    def test_initialization_with_embeddings(self, mock_embeddings):
        """测试使用提供的嵌入模型初始化"""
        memory = VectorMemory(embeddings=mock_embeddings, k=5, score_threshold=0.6)
        assert memory.embeddings == mock_embeddings
        assert memory.k == 5
        assert memory.score_threshold == 0.6
        assert memory.vector_store is None

    def test_initialization_without_embeddings(self):
        """测试不提供嵌入模型时的初始化"""
        # 没有API key应该抛出异常
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="DASHSCOPE_API_KEY not found"):
                VectorMemory()

    @patch.dict(os.environ, {'DASHSCOPE_API_KEY': 'test_key'})
    @patch('src.modules.module_6_memory.vector_memory.DashScopeEmbeddings')
    def test_initialization_with_env_key(self, mock_dashscope):
        """测试使用环境变量中的API key初始化"""
        memory = VectorMemory()
        assert memory.embeddings is not None

    def test_add_memory(self, mock_embeddings):
        """测试添加记忆"""
        memory = VectorMemory(embeddings=mock_embeddings)

        memory.add_memory("This is a test memory", {'type': 'test'})

        assert memory.get_memory_count() == 1
        assert memory.vector_store is not None

    def test_add_exchange(self, mock_embeddings):
        """测试添加对话交互"""
        memory = VectorMemory(embeddings=mock_embeddings)

        memory.add_exchange("Hello", "Hi there!", {'session': '001'})

        assert memory.get_memory_count() == 1

    def test_search(self, mock_embeddings):
        """测试搜索记忆"""
        memory = VectorMemory(embeddings=mock_embeddings, k=2)

        # 添加多条记忆
        memory.add_memory("Python programming", {'topic': 'code'})
        memory.add_memory("Machine learning", {'topic': 'ai'})
        memory.add_memory("Web development", {'topic': 'code'})

        # 搜索
        results = memory.search("programming", k=2)

        assert len(results) <= 2

    def test_search_with_score(self, mock_embeddings):
        """测试带分数的搜索"""
        memory = VectorMemory(embeddings=mock_embeddings, score_threshold=0.5)

        memory.add_memory("Test memory 1")
        memory.add_memory("Test memory 2")

        results = memory.search_with_score("test query")

        assert isinstance(results, list)
        # 结果可能为空，因为模拟的嵌入可能不满足阈值

    def test_get_context(self, mock_embeddings):
        """测试获取上下文"""
        memory = VectorMemory(embeddings=mock_embeddings)

        # 空记忆
        context = memory.get_context("query")
        assert "暂无相关历史记忆" in context

        # 添加记忆后
        memory.add_memory("Important information")
        context = memory.get_context("information")

        # 由于模拟嵌入，可能无法通过阈值
        assert isinstance(context, str)

    def test_clear(self, mock_embeddings):
        """测试清空记忆"""
        memory = VectorMemory(embeddings=mock_embeddings)

        memory.add_memory("Test")
        assert memory.get_memory_count() == 1

        memory.clear()

        assert memory.get_memory_count() == 0
        assert memory.vector_store is None

    def test_save_and_load_local(self, mock_embeddings):
        """测试保存和加载"""
        temp_dir = tempfile.mkdtemp()

        try:
            # 创建并保存
            memory = VectorMemory(embeddings=mock_embeddings, k=3)
            memory.add_memory("Test memory 1")
            memory.add_memory("Test memory 2")

            memory.save_local(temp_dir, "test_index")

            # 加载
            loaded_memory = VectorMemory.load_local(
                temp_dir,
                embeddings=mock_embeddings,
                index_name="test_index"
            )

            assert loaded_memory.k == 3
            assert loaded_memory.get_memory_count() == 2

        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)

    def test_to_dict(self, mock_embeddings):
        """测试导出为字典"""
        memory = VectorMemory(embeddings=mock_embeddings, k=4, score_threshold=0.7)

        memory.add_memory("Test")

        data = memory.to_dict()

        assert data['k'] == 4
        assert data['score_threshold'] == 0.7
        assert data['memory_count'] == 1
        assert data['has_vector_store'] is True

    def test_empty_search(self, mock_embeddings):
        """测试在空向量存储上搜索"""
        memory = VectorMemory(embeddings=mock_embeddings)

        results = memory.search("query")
        assert results == []

        results_with_score = memory.search_with_score("query")
        assert results_with_score == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
