"""
Module 6: Memory System - 记忆系统

提供记忆管理功能
"""

# 优先使用简化版实现
try:
    from .memory_simple import SimpleBufferMemory as BufferMemory
    from .composite_memory import CompositeMemory
    __all__ = ['BufferMemory', 'CompositeMemory']
except ImportError:
    try:
        from .buffer_memory import BufferMemory
        from .composite_memory import CompositeMemory
        __all__ = ['BufferMemory', 'CompositeMemory']
    except ImportError:
        __all__ = []

__version__ = "0.1.0"
