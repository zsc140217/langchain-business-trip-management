"""
Tests for BufferMemory - 对话缓冲记忆测试
"""

import pytest
from src.modules.module_6_memory.buffer_memory import BufferMemory


class TestBufferMemory:
    """BufferMemory 测试类"""

    def test_initialization(self):
        """测试初始化"""
        memory = BufferMemory(max_turns=3)
        assert memory.max_turns == 3
        assert memory.get_turn_count() == 0
        assert not memory.is_full()

    def test_add_single_message(self):
        """测试添加单条消息"""
        memory = BufferMemory(max_turns=2)

        memory.add_message('human', 'Hello')
        memory.add_message('ai', 'Hi there!')

        messages = memory.get_messages()
        assert len(messages) == 2
        assert memory.get_turn_count() == 1

    def test_add_exchange(self):
        """测试添加对话交互"""
        memory = BufferMemory(max_turns=2)

        memory.add_exchange('What is Python?', 'Python is a programming language.')

        messages = memory.get_messages()
        assert len(messages) == 2
        assert memory.get_turn_count() == 1

    def test_max_turns_enforcement(self):
        """测试最大轮次限制"""
        memory = BufferMemory(max_turns=2)

        # 添加3轮对话
        memory.add_exchange('Question 1', 'Answer 1')
        memory.add_exchange('Question 2', 'Answer 2')
        memory.add_exchange('Question 3', 'Answer 3')

        messages = memory.get_messages()
        # 应该只保留最近2轮（4条消息）
        assert len(messages) == 4
        assert memory.get_turn_count() == 3

        # 验证保留的是最近的消息
        assert 'Question 2' in messages[0].content
        assert 'Question 3' in messages[2].content

    def test_is_full(self):
        """测试缓冲区满状态检测"""
        memory = BufferMemory(max_turns=2)

        assert not memory.is_full()

        memory.add_exchange('Q1', 'A1')
        assert not memory.is_full()

        memory.add_exchange('Q2', 'A2')
        assert memory.is_full()

    def test_get_context(self):
        """测试获取格式化上下文"""
        memory = BufferMemory(max_turns=2)

        memory.add_exchange('Hello', 'Hi there!')
        memory.add_exchange('How are you?', 'I am doing well.')

        context = memory.get_context()

        assert '用户: Hello' in context
        assert '助手: Hi there!' in context
        assert '用户: How are you?' in context
        assert '助手: I am doing well.' in context

    def test_clear(self):
        """测试清空记忆"""
        memory = BufferMemory(max_turns=2)

        memory.add_exchange('Question', 'Answer')
        assert memory.get_turn_count() > 0

        memory.clear()

        assert memory.get_turn_count() == 0
        assert len(memory.get_messages()) == 0

    def test_to_dict(self):
        """测试导出为字典"""
        memory = BufferMemory(max_turns=3)

        memory.add_exchange('Hello', 'Hi')

        data = memory.to_dict()

        assert data['max_turns'] == 3
        assert data['turn_count'] == 1
        assert len(data['messages']) == 2
        assert data['messages'][0]['role'] == 'human'
        assert data['messages'][1]['role'] == 'ai'

    def test_from_dict(self):
        """测试从字典恢复"""
        original = BufferMemory(max_turns=2)
        original.add_exchange('Q1', 'A1')
        original.add_exchange('Q2', 'A2')

        data = original.to_dict()
        restored = BufferMemory.from_dict(data)

        assert restored.max_turns == original.max_turns
        assert restored.get_turn_count() == original.get_turn_count()
        assert len(restored.get_messages()) == len(original.get_messages())

    def test_empty_context(self):
        """测试空记忆的上下文"""
        memory = BufferMemory(max_turns=2)

        context = memory.get_context()
        assert context == ""


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
