"""
Tests for CompositeMemory - 组合记忆测试
"""

import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch
from langchain.llms.fake import FakeListLLM
from src.modules.module_6_memory.composite_memory import CompositeMemory


class TestCompositeMemory:
    """CompositeMemory 测试类"""

    @pytest.fixture
    def mock_llm(self):
        """创建模拟的LLM"""
        return FakeListLLM(responses=["这是对话的摘要"] * 100)

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

    def test_initialization_all_enabled(self, mock_llm, mock_embeddings):
        """测试启用所有记忆层"""
        memory = CompositeMemory(
            llm=mock_llm,
            embeddings=mock_embeddings,
            enable_buffer=True,
            enable_summary=True,
            enable_vector=True
        )

        assert memory.buffer_memory is not None
        assert memory.summary_memory is not None
        assert memory.vector_memory is not None

    def test_initialization_selective_enable(self, mock_llm, mock_embeddings):
        """测试选择性启用记忆层"""
        memory = CompositeMemory(
            llm=mock_llm,
            embeddings=mock_embeddings,
            enable_buffer=True,
            enable_summary=False,
            enable_vector=True
        )

        assert memory.buffer_memory is not None
        assert memory.summary_memory is None
        assert memory.vector_memory is not None

    def test_add_exchange_all_layers(self, mock_llm, mock_embeddings):
        """测试向所有层添加对话"""
        memory = CompositeMemory(
            llm=mock_llm,
            embeddings=mock_embeddings
        )

        memory.add_exchange("Hello", "Hi there!", {'session': '001'})

        assert memory._total_exchanges == 1
        assert memory.buffer_memory.get_turn_count() == 1
        assert memory.vector_memory.get_memory_count() == 1

    def test_get_context_combined(self, mock_llm, mock_embeddings):
        """测试获取组合上下文"""
        memory = CompositeMemory(
            llm=mock_llm,
            embeddings=mock_embeddings
        )

        memory.add_exchange("Q1", "A1")
        memory.add_exchange("Q2", "A2")

        context = memory.get_context(query="Q1")

        # 应该包含各层的上下文
        assert isinstance(context, str)
        # 可能包含 "最近对话" 等标记
        assert len(context) > 0

    def test_get_layered_context(self, mock_llm, mock_embeddings):
        """测试获取分层上下文"""
        memory = CompositeMemory(
            llm=mock_llm,
            embeddings=mock_embeddings
        )

        memory.add_exchange("Question", "Answer")

        layered = memory.get_layered_context(query="Question")

        assert 'buffer' in layered
        assert 'summary' in layered
        assert 'vector' in layered

    def test_search_relevant_history(self, mock_llm, mock_embeddings):
        """测试搜索相关历史"""
        memory = CompositeMemory(
            llm=mock_llm,
            embeddings=mock_embeddings
        )

        memory.add_exchange("Python programming", "Python is great")
        memory.add_exchange("Web development", "HTML and CSS")

        results = memory.search_relevant_history("programming", k=1)

        assert isinstance(results, list)

    def test_clear_all(self, mock_llm, mock_embeddings):
        """测试清空所有记忆"""
        memory = CompositeMemory(
            llm=mock_llm,
            embeddings=mock_embeddings
        )

        memory.add_exchange("Q", "A")
        assert memory._total_exchanges == 1

        memory.clear_all()

        assert memory._total_exchanges == 0
        assert memory.buffer_memory.get_turn_count() == 0
        assert memory.vector_memory.get_memory_count() == 0

    def test_clear_buffer_only(self, mock_llm, mock_embeddings):
        """测试仅清空缓冲记忆"""
        memory = CompositeMemory(
            llm=mock_llm,
            embeddings=mock_embeddings
        )

        memory.add_exchange("Q", "A")

        memory.clear_buffer()

        assert memory.buffer_memory.get_turn_count() == 0
        # 向量记忆应该保留
        assert memory.vector_memory.get_memory_count() == 1

    def test_get_statistics(self, mock_llm, mock_embeddings):
        """测试获取统计信息"""
        memory = CompositeMemory(
            llm=mock_llm,
            embeddings=mock_embeddings,
            buffer_max_turns=2
        )

        memory.add_exchange("Q1", "A1")
        memory.add_exchange("Q2", "A2")

        stats = memory.get_statistics()

        assert stats['total_exchanges'] == 2
        assert 'buffer' in stats['enabled_layers']
        assert 'summary' in stats['enabled_layers']
        assert 'vector' in stats['enabled_layers']
        assert stats['buffer_turns'] == 2
        assert stats['buffer_full'] is True

    def test_save_and_load_vector_memory(self, mock_llm, mock_embeddings):
        """测试保存和加载向量记忆"""
        temp_dir = tempfile.mkdtemp()

        try:
            # 创建并保存
            memory = CompositeMemory(
                llm=mock_llm,
                embeddings=mock_embeddings
            )

            memory.add_exchange("Q1", "A1")
            memory.add_exchange("Q2", "A2")

            memory.save_vector_memory(temp_dir, "composite_test")

            # 加载
            loaded_memory = CompositeMemory.load_with_vector_memory(
                temp_dir,
                llm=mock_llm,
                embeddings=mock_embeddings,
                index_name="composite_test"
            )

            assert loaded_memory.vector_memory.get_memory_count() == 2

        finally:
            shutil.rmtree(temp_dir)

    def test_to_dict(self, mock_llm, mock_embeddings):
        """测试导出为字典"""
        memory = CompositeMemory(
            llm=mock_llm,
            embeddings=mock_embeddings,
            buffer_max_turns=3
        )

        memory.add_exchange("Q", "A")

        data = memory.to_dict()

        assert data['total_exchanges'] == 1
        assert data['enable_buffer'] is True
        assert data['enable_summary'] is True
        assert data['enable_vector'] is True
        assert 'buffer' in data
        assert 'summary' in data
        assert 'vector' in data

    def test_disabled_layers(self, mock_llm, mock_embeddings):
        """测试禁用某些层的情况"""
        memory = CompositeMemory(
            llm=mock_llm,
            embeddings=mock_embeddings,
            enable_buffer=False,
            enable_summary=False,
            enable_vector=True
        )

        memory.add_exchange("Q", "A")

        stats = memory.get_statistics()
        assert len(stats['enabled_layers']) == 1
        assert 'vector' in stats['enabled_layers']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
