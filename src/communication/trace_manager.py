# -*- coding: utf-8 -*-
"""
TraceID管理器
负责生成和管理全局追踪ID
"""
import uuid
from contextvars import ContextVar
from typing import Optional
from src.communication.protocol import RequestContext


# 使用contextvars实现协程安全的上下文传递
_trace_context: ContextVar[Optional[RequestContext]] = ContextVar('trace_context', default=None)


class TraceManager:
    """TraceID管理器"""

    @staticmethod
    def generate_trace_id() -> str:
        """生成TraceID"""
        return f"trace_{uuid.uuid4().hex[:16]}"

    @staticmethod
    def generate_correlation_id() -> str:
        """生成关联ID"""
        return f"corr_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def set_context(context: RequestContext):
        """设置当前请求上下文"""
        _trace_context.set(context)

    @staticmethod
    def get_context() -> Optional[RequestContext]:
        """获取当前请求上下文"""
        return _trace_context.get()

    @staticmethod
    def get_trace_id() -> str:
        """获取当前TraceID"""
        context = _trace_context.get()
        return context.trace_id if context else "unknown"

    @staticmethod
    def get_user_id() -> str:
        """获取当前用户ID"""
        context = _trace_context.get()
        return context.user_id if context else "unknown"

    @staticmethod
    def get_conversation_id() -> Optional[str]:
        """获取当前会话ID"""
        context = _trace_context.get()
        return context.conversation_id if context else None

    @staticmethod
    def clear_context():
        """清理当前请求上下文"""
        _trace_context.set(None)
