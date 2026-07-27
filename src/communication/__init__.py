# -*- coding: utf-8 -*-
"""
统一通信层
提供标准化的请求/响应协议、TraceID管理、事件总线、中间件机制

核心组件:
- protocol.py: StandardRequest/Response
- error_codes.py: 统一错误码
- trace_manager.py: TraceID管理
- event_bus.py: 事件总线
- middleware.py: 中间件基类
- communication_layer.py: 统一通信层
"""

from src.communication.protocol import (
    RequestContext,
    StandardRequest,
    StandardResponse,
)
from src.communication.error_codes import ErrorCode
from src.communication.trace_manager import TraceManager
from src.communication.event_bus import EventBus, Event, EventType
from src.communication.middleware import Middleware
from src.communication.communication_layer import CommunicationLayer
from src.communication.adapters import LegacyAPIAdapter

# 创建全局事件总线实例
event_bus = EventBus()

__all__ = [
    # 协议
    "RequestContext",
    "StandardRequest",
    "StandardResponse",

    # 错误码
    "ErrorCode",

    # 追踪
    "TraceManager",

    # 事件
    "EventBus",
    "Event",
    "EventType",
    "event_bus",

    # 中间件
    "Middleware",

    # 通信层
    "CommunicationLayer",

    # 适配器
    "LegacyAPIAdapter",
]
