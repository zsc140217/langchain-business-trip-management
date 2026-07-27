# -*- coding: utf-8 -*-
"""
事件总线
实现发布/订阅模式，解耦组件通信
"""
import asyncio
import logging
from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型枚举"""
    
    # 审批事件
    APPROVAL_SUBMITTED = "approval.submitted"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"
    
    # Q&A事件
    QUERY_RECEIVED = "query.received"
    QUERY_ANSWERED = "query.answered"
    
    # 系统事件
    ERROR_OCCURRED = "system.error"
    PERFORMANCE_DEGRADED = "system.performance_degraded"


@dataclass
class Event:
    """事件数据结构"""
    event_type: EventType          # 事件类型
    payload: Dict[str, Any]        # 事件数据
    trace_id: str                  # 追踪ID
    timestamp: datetime            # 事件时间戳
    source: str                    # 事件来源组件


class EventBus:
    """事件总线
    
    简化版事件总线，生产环境可替换为Redis Pub/Sub或RabbitMQ
    
    使用示例:
        # 订阅事件
        async def on_approval_approved(event: Event):
            print(f"审批通过: {event.payload}")
        
        event_bus.subscribe(EventType.APPROVAL_APPROVED, on_approval_approved)
        
        # 发布事件
        await event_bus.publish(Event(
            event_type=EventType.APPROVAL_APPROVED,
            payload={"approval_id": "APV001"},
            trace_id="trace_123",
            timestamp=datetime.now(),
            source="approval_engine"
        ))
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        """订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数（可以是同步或异步函数）
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"[EventBus] 订阅事件: {event_type}, handler={handler.__name__}")
    
    async def publish(self, event: Event):
        """发布事件（异步）
        
        Args:
            event: 事件对象
        """
        logger.info(f"[EventBus] 发布事件: {event.event_type}, trace_id={event.trace_id}")
        
        handlers = self._subscribers.get(event.event_type, [])
        if not handlers:
            logger.warning(f"[EventBus] 无订阅者: {event.event_type}")
            return
        
        # 并发执行所有handler
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._execute_handler(handler, event))
            tasks.append(task)
        
        # 等待所有handler完成（不阻塞主流程）
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_handler(self, handler: Callable, event: Event):
        """执行事件处理器
        
        Args:
            handler: 处理函数
            event: 事件对象
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                # 在executor中执行同步函数
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler, event)
        except Exception as e:
            logger.error(
                f"[EventBus] Handler执行失败: {handler.__name__}, "
                f"event={event.event_type}, error={e}",
                exc_info=True
            )


# 全局事件总线实例
event_bus = EventBus()
