"""
Base Channel
工具调用通道抽象基类

提供统一的工具调用接口，支持多种通道实现：
- MCP通道：通过MCP协议调用远程工具
- HTTP通道：通过REST API调用远程工具
- gRPC通道：通过gRPC调用远程工具
- Local通道：直接调用本地工具实例
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ChannelStatus(Enum):
    """通道状态枚举"""
    UNKNOWN = "unknown"         # 未知
    INITIALIZING = "initializing"  # 初始化中
    HEALTHY = "healthy"         # 健康
    DEGRADED = "degraded"       # 降级
    DOWN = "down"               # 不可用


@dataclass
class ChannelHealthStatus:
    """通道健康状态"""
    status: ChannelStatus       # 状态
    latency_ms: float          # 延迟（毫秒）
    error: Optional[str]       # 错误信息
    timestamp: datetime        # 时间戳
    consecutive_failures: int = 0   # 连续失败次数
    consecutive_successes: int = 0  # 连续成功次数


class BaseChannel(ABC):
    """
    工具调用通道抽象基类

    所有通道实现必须继承此类
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化通道

        Args:
            name: 通道名称
            config: 通道配置
        """
        self.name = name
        self.config = config or {}
        self._initialized = False
        self._health_status = ChannelHealthStatus(
            status=ChannelStatus.UNKNOWN,
            latency_ms=0.0,
            error=None,
            timestamp=datetime.now()
        )

    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化通道

        Returns:
            初始化成功返回True，否则返回False
        """
        pass

    @abstractmethod
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        调用工具

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            工具执行结果

        Raises:
            ChannelError: 通道调用失败
        """
        pass

    @abstractmethod
    async def health_check(self) -> ChannelHealthStatus:
        """
        健康检查

        Returns:
            通道健康状态
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        关闭通道，清理资源
        """
        pass

    def is_initialized(self) -> bool:
        """
        检查通道是否已初始化

        Returns:
            已初始化返回True
        """
        return self._initialized

    def get_health_status(self) -> ChannelHealthStatus:
        """
        获取最近的健康状态

        Returns:
            健康状态
        """
        return self._health_status

    def is_healthy(self) -> bool:
        """
        检查通道是否健康

        Returns:
            健康返回True
        """
        return self._health_status.status in [ChannelStatus.HEALTHY, ChannelStatus.DEGRADED]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', status={self._health_status.status.value})"


class ChannelError(Exception):
    """通道调用错误"""
    pass


class ChannelTimeoutError(ChannelError):
    """通道超时错误"""
    pass


class ChannelConnectionError(ChannelError):
    """通道连接错误"""
    pass
