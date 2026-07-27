# -*- coding: utf-8 -*-
"""
统一通信层核心类
集成所有通信层组件，提供统一的请求处理入口
"""
import logging
from typing import List, Callable, Dict, Any, Optional
from datetime import datetime

from src.communication.protocol import RequestContext, StandardRequest, StandardResponse
from src.communication.trace_manager import TraceManager
from src.communication.event_bus import EventBus, event_bus
from src.communication.middleware import (
    Middleware,
    TracingMiddleware,
    LoggingMiddleware,
    MetricsMiddleware,
    ErrorHandlingMiddleware
)
from src.communication.error_codes import ErrorCode

logger = logging.getLogger(__name__)


class CommunicationLayer:
    """统一通信层
    
    核心职责:
    - 生成TraceID和请求上下文
    - 构建标准请求/响应
    - 执行中间件链
    - 路由到业务域
    
    使用示例:
        comm_layer = CommunicationLayer(event_bus)
        
        response = await comm_layer.handle_request(
            action="chat.query",
            payload={"query": "北京住宿标准是多少？"},
            user_id="user_001",
            source="http"
        )
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.middlewares: List[Middleware] = []
        self._domain_handlers: Dict[str, Callable] = {}
        self._setup_default_middlewares()
    
    def _setup_default_middlewares(self):
        """设置默认中间件链
        
        执行顺序（从外到内）:
        1. TracingMiddleware - 设置追踪上下文
        2. LoggingMiddleware - 记录日志
        3. MetricsMiddleware - 采集指标
        4. ErrorHandlingMiddleware - 错误处理
        """
        self.middlewares = [
            TracingMiddleware(),
            LoggingMiddleware(),
            MetricsMiddleware(),
            ErrorHandlingMiddleware()
        ]
    
    def add_middleware(self, middleware: Middleware):
        """添加自定义中间件
        
        Args:
            middleware: 中间件实例
        """
        self.middlewares.insert(0, middleware)  # 插入到最前面
        logger.info(f"[CommunicationLayer] 添加中间件: {middleware.__class__.__name__}")
    
    def register_domain_handler(self, domain: str, handler: Callable):
        """注册业务域处理器
        
        Args:
            domain: 域名（如 "chat", "approval"）
            handler: 处理函数
        """
        self._domain_handlers[domain] = handler
        logger.info(f"[CommunicationLayer] 注册域处理器: domain={domain}")
    
    async def handle_request(
        self,
        action: str,
        payload: Dict[str, Any],
        user_id: str,
        source: str = "http",
        conversation_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> StandardResponse:
        """处理请求
        
        Args:
            action: 操作类型（如 "chat.query", "approval.submit"）
            payload: 业务数据
            user_id: 用户ID
            source: 请求来源（http/websocket/feishu）
            conversation_id: 会话ID（可选）
            trace_id: 追踪ID（可选，如果未提供则自动生成）
        
        Returns:
            标准响应
        """
        # 1. 创建请求上下文
        context = RequestContext(
            trace_id=trace_id or TraceManager.generate_trace_id(),
            correlation_id=TraceManager.generate_correlation_id(),
            user_id=user_id,
            conversation_id=conversation_id,
            source=source,
            timestamp=datetime.now(),
            metadata={}
        )
        
        # 2. 构建标准请求
        request = StandardRequest(
            context=context,
            action=action,
            payload=payload
        )
        
        logger.debug(
            f"[{context.trace_id}] CommunicationLayer.handle_request: "
            f"action={action}, user_id={user_id}"
        )
        
        # 3. 执行中间件链
        handler = self._build_handler_chain()
        response = await handler(request)
        
        return response
    
    def _build_handler_chain(self) -> Callable:
        """构建中间件处理链
        
        采用洋葱模型：
        TracingMiddleware -> LoggingMiddleware -> MetricsMiddleware -> ErrorHandlingMiddleware -> 业务处理
        """
        # 最终处理器（路由到业务层）
        async def final_handler(request: StandardRequest) -> StandardResponse:
            return await self._route_to_domain(request)
        
        # 从后往前构建中间件链
        handler = final_handler
        for middleware in reversed(self.middlewares):
            current_handler = handler
            # 使用闭包捕获当前handler
            async def make_handler(mw=middleware, h=current_handler):
                async def wrapped(req):
                    return await mw.process(req, h)
                return wrapped
            handler = lambda req, mw=middleware, h=current_handler: mw.process(req, h)
        
        return handler
    
    async def _route_to_domain(self, request: StandardRequest) -> StandardResponse:
        """路由到业务域
        
        从action中提取domain（格式: domain.operation）
        例如: "chat.query" -> domain="chat"
        
        Args:
            request: 标准请求
        
        Returns:
            标准响应
        """
        # 从action提取domain
        parts = request.action.split('.')
        if len(parts) < 2:
            logger.error(f"[{request.context.trace_id}] 无效的action格式: {request.action}")
            return StandardResponse.error_response(
                code=ErrorCode.BAD_REQUEST,
                message=f"Invalid action format: {request.action}",
                trace_id=request.context.trace_id
            )
        
        domain = parts[0]
        
        # 查找域处理器
        handler = self._domain_handlers.get(domain)
        if not handler:
            logger.error(
                f"[{request.context.trace_id}] 未注册的域: {domain}, "
                f"已注册: {list(self._domain_handlers.keys())}"
            )
            return StandardResponse.error_response(
                code=ErrorCode.NOT_FOUND,
                message=f"Domain not found: {domain}",
                trace_id=request.context.trace_id
            )
        
        # 调用域处理器
        try:
            logger.debug(f"[{request.context.trace_id}] 路由到域: {domain}")
            response = await handler(request)
            return response
        except Exception as e:
            logger.error(
                f"[{request.context.trace_id}] 域处理器异常: domain={domain}, error={e}",
                exc_info=True
            )
            return StandardResponse.error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Domain handler error: {str(e)}",
                trace_id=request.context.trace_id
            )
