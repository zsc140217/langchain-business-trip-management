# -*- coding: utf-8 -*-
"""
中间件基类和实现
提供请求处理链的中间件机制
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import Callable, Any
from src.communication.protocol import StandardRequest, StandardResponse
from src.communication.trace_manager import TraceManager
from src.communication.error_codes import ErrorCode

logger = logging.getLogger(__name__)


class Middleware(ABC):
    """中间件抽象基类"""
    
    @abstractmethod
    async def process(
        self, 
        request: StandardRequest, 
        next_handler: Callable[[StandardRequest], Any]
    ) -> StandardResponse:
        """处理请求
        
        Args:
            request: 标准请求
            next_handler: 下一个处理器
            
        Returns:
            标准响应
        """
        pass


class LoggingMiddleware(Middleware):
    """日志中间件"""
    
    async def process(
        self, 
        request: StandardRequest, 
        next_handler: Callable
    ) -> StandardResponse:
        trace_id = request.context.trace_id
        logger.info(
            f"[{trace_id}] Request: action={request.action}, "
            f"user={request.context.user_id}, source={request.context.source}"
        )
        
        response = await next_handler(request)
        
        logger.info(
            f"[{trace_id}] Response: success={response.success}, "
            f"code={response.code}, duration={response.duration_ms:.2f}ms"
        )
        return response


class MetricsMiddleware(Middleware):
    """指标采集中间件"""
    
    async def process(
        self, 
        request: StandardRequest, 
        next_handler: Callable
    ) -> StandardResponse:
        start_time = time.time()
        
        response = await next_handler(request)
        
        duration = (time.time() - start_time) * 1000
        response.duration_ms = duration
        
        # 记录Prometheus指标
        try:
            from src.monitoring.prometheus_exporter import track_unified_metric
            
            domain = request.action.split('.')[0]  # 从action提取domain
            track_unified_metric(
                domain=domain,
                channel=request.context.source,
                duration_seconds=duration / 1000,
                success=response.success
            )
        except Exception as e:
            logger.warning(f"[{request.context.trace_id}] 指标记录失败: {e}")
        
        return response


class ErrorHandlingMiddleware(Middleware):
    """错误处理中间件"""
    
    async def process(
        self, 
        request: StandardRequest, 
        next_handler: Callable
    ) -> StandardResponse:
        try:
            return await next_handler(request)
        except ValueError as e:
            logger.warning(f"[{request.context.trace_id}] 参数验证错误: {e}")
            return StandardResponse.error_response(
                code=ErrorCode.INVALID_INPUT,
                message=str(e),
                trace_id=request.context.trace_id
            )
        except Exception as e:
            logger.error(
                f"[{request.context.trace_id}] 未处理的异常: {e}", 
                exc_info=True
            )
            return StandardResponse.error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                trace_id=request.context.trace_id,
                details={"error": str(e)}
            )


class TracingMiddleware(Middleware):
    """链路追踪中间件"""
    
    async def process(
        self, 
        request: StandardRequest, 
        next_handler: Callable
    ) -> StandardResponse:
        # 设置当前请求上下文
        TraceManager.set_context(request.context)

        try:
            # 记录Prometheus指标（不使用LangSmith上下文管理器，因为trace_operation是装饰器）
            import time
            start_time = time.time()
            success = True

            try:
                response = await next_handler(request)
            except Exception as e:
                success = False
                raise
            finally:
                # 手动记录指标
                try:
                    from src.monitoring import track_unified_metric
                    duration = time.time() - start_time
                    domain = request.action.split('.')[0]
                    track_unified_metric(
                        domain=domain,
                        channel=request.context.source,
                        duration_seconds=duration,
                        success=success
                    )
                except ImportError:
                    pass  # 监控模块不可用时忽略
        finally:
            # 清理上下文
            TraceManager.clear_context()

        return response
