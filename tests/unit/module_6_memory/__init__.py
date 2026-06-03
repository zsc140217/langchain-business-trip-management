"""
Test __init__ for module_6_memory
"""

import pytest
from src.modules.module_6_memory import (
    BufferMemory,
    SummaryMemory,
    VectorMemory,
    CompositeMemory
)


def test_imports():
    """测试所有类都可以正确导入"""
    assert BufferMemory is not None
    assert SummaryMemory is not None
    assert VectorMemory is not None
    assert CompositeMemory is not None


def test_buffer_memory_instantiation():
    """测试BufferMemory可以实例化"""
    memory = BufferMemory(max_turns=3)
    assert memory.max_turns == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
