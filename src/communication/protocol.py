# -*- coding: utf-8 -*-
"""
统一通信协议
定义标准请求和响应格式
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class RequestContext:
    """请求上下文

    包含请求的元数据信息，用于追踪、日志、监控等
    """
    trace_id: str                      # 全局追踪ID（贯穿整个请求链路）
    correlation_id: str                # 关联ID（用于关联请求-响应）
    user_id: str                       # 用户ID
    conversation_id: Optional[str]     # 会话ID（可选）
    source: str                        # 请求来源（http/websocket/feishu）
    timestamp: datetime                # 请求时间戳
    metadata: Dict[str, Any] = field(default_factory=dict)  # 扩展元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        # 将datetime转换为ISO格式字符串
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class StandardRequest:
    """统一请求封装

    所有进入系统的请求都应该封装为StandardRequest

    示例:
        request = StandardRequest(
            context=RequestContext(
                trace_id="trace_abc123",
                user_id="user_001",
                ...
            ),
            action="chat.query",
            payload={"query": "北京住宿标准是多少？"}
        )
    """
    context: RequestContext            # 请求上下文
    action: str                        # 操作类型（chat.query / approval.submit 等）
    payload: Dict[str, Any]            # 业务数据

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "context": self.context.to_dict(),
            "action": self.action,
            "payload": self.payload
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StandardRequest":
        """从字典反序列化"""
        context_data = data["context"]
        context_data['timestamp'] = datetime.fromisoformat(context_data['timestamp'])

        return cls(
            context=RequestContext(**context_data),
            action=data["action"],
            payload=data["payload"]
        )


@dataclass
class StandardResponse:
    """统一响应封装

    所有系统的响应都应该封装为StandardResponse

    示例（成功）:
        response = StandardResponse.success_response(
            data={"answer": "北京住宿标准是500元/天"},
            trace_id="trace_abc123"
        )

    示例（失败）:
        response = StandardResponse.error_response(
            code="LLM_CALL_FAILED",
            message="LLM调用超时",
            trace_id="trace_abc123"
        )
    """
    success: bool                      # 是否成功
    code: str                          # 业务错误码（参考ErrorCode）
    message: str                       # 提示消息
    data: Optional[Dict[str, Any]]     # 业务数据（成功时返回）
    trace_id: str                      # 追踪ID
    duration_ms: float                 # 处理耗时（毫秒）

    # 元数据（可选）
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "success": self.success,
            "code": self.code,
            "message": self.message,
            "data": self.data,
            "trace_id": self.trace_id,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata
        }

    @staticmethod
    def success_response(
        data: Dict[str, Any],
        message: str = "Success",
        trace_id: str = "",
        duration_ms: float = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "StandardResponse":
        """创建成功响应

        Args:
            data: 业务数据
            message: 成功消息
            trace_id: 追踪ID
            duration_ms: 处理耗时
            metadata: 元数据

        Returns:
            StandardResponse实例
        """
        return StandardResponse(
            success=True,
            code="OK",
            message=message,
            data=data,
            trace_id=trace_id,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )

    @staticmethod
    def error_response(
        code: str,
        message: str,
        trace_id: str = "",
        duration_ms: float = 0,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "StandardResponse":
        """创建错误响应

        Args:
            code: 错误码（参考ErrorCode）
            message: 错误消息
            trace_id: 追踪ID
            duration_ms: 处理耗时
            details: 错误详情
            metadata: 元数据

        Returns:
            StandardResponse实例
        """
        return StandardResponse(
            success=False,
            code=code,
            message=message,
            data={"details": details} if details else None,
            trace_id=trace_id,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
