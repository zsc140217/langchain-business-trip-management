"""
Tests for SummaryMemory - 摘要记忆测试
"""

import pytest
import os
from unittest.mock import Mock, patch
from langchain.llms.fake import FakeListLLM
from src.modules.module_6_memory.summary_memory import SummaryMemory


class TestSummaryMemory:
    """SummaryMemory 测试类"""

    @pytest.fixture
    def mock_llm(self):
        """创建模拟的LLM"""
        # 使用FakeListLLM来创建一个真实的LLM对象
        return FakeListLLM(responses=["这是对话的摘要"] * 100)

    def test_initialization_with_llm(self, mock_llm):
        """测试使用提供的LLM初始化"""
        memory = SummaryMemory(llm=mock_llm)
        assert memory.llm == mock_llm
        assert memory.memory_key == "history_summary"

    def test_initialization_without_llm(self):
        """测试不提供LLM时的初始化"""
        # 没有API key应该抛出异常
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="DASHSCOPE_API_KEY not found"):
                SummaryMemory()

    @patch.dict(os.environ, {'DASHSCOPE_API_KEY': 'test_key'})
    @patch('src.modules.module_6_memory.summary_memory.ChatTongyi')
    def test_initialization_with_env_key(self, mock_tongyi):
        """测试使用环境变量中的API key初始化"""
        memory = SummaryMemory()
        assert memory.llm is not None

    def test_add_message(self, mock_llm):
        """测试添加消息"""
        memory = SummaryMemory(llm=mock_llm)

        memory.add_message('human', 'Hello')
        memory.add_message('ai', 'Hi there!')

        messages = memory.memory.chat_memory.messages
        assert len(messages) == 2

    def test_add_exchange(self, mock_llm):
        """测试添加对话交互"""
        memory = SummaryMemory(llm=mock_llm)

        memory.add_exchange('Question', 'Answer')

        messages = memory.memory.chat_memory.messages
        assert len(messages) == 2

    def test_get_summary(self, mock_llm):
        """测试获取摘要"""
        memory = SummaryMemory(llm=mock_llm)

        memory.add_exchange('Q1', 'A1')

        # get_summary 会触发摘要生成
        summary = memory.get_summary()

        # 由于ConversationSummaryMemory的行为，可能返回空或生成的摘要
        assert isinstance(summary, str)

    def test_get_context(self, mock_llm):
        """测试获取上下文"""
        memory = SummaryMemory(llm=mock_llm)

        # 空记忆
        context = memory.get_context()
        assert "暂无对话历史摘要" in context or "对话历史摘要" in context

    def test_predict_new_summary(self, mock_llm):
        """测试预测新摘要"""
        memory = SummaryMemory(llm=mock_llm)

        memory.add_exchange('Q1', 'A1')

        new_summary = memory.predict_new_summary('Q2', 'A2')

        assert new_summary == "这是对话的摘要"
        mock_llm.invoke.assert_called_once()

    def test_clear(self, mock_llm):
        """测试清空记忆"""
        memory = SummaryMemory(llm=mock_llm)

        memory.add_exchange('Question', 'Answer')
        memory.clear()

        messages = memory.memory.chat_memory.messages
        assert len(messages) == 0

    def test_to_dict(self, mock_llm):
        """测试导出为字典"""
        memory = SummaryMemory(llm=mock_llm, max_token_limit=3000)

        memory.add_exchange('Q1', 'A1')

        data = memory.to_dict()

        assert data['memory_key'] == 'history_summary'
        assert data['max_token_limit'] == 3000
        assert 'message_count' in data

    def test_from_dict(self, mock_llm):
        """测试从字典恢复"""
        data = {
            'memory_key': 'custom_key',
            'max_token_limit': 3000
        }

        memory = SummaryMemory.from_dict(data, llm=mock_llm)

        assert memory.memory_key == 'custom_key'
        assert memory.max_token_limit == 3000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
