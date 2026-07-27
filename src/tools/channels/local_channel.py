"""
Local Channel
本地工具调用通道

直接调用本地工具实例，无网络开销，最快执行路径
适用于本地部署的工具（如RAG、数据库查询等）
"""
from typing import Dict, Any, Optional
from datetime import datetime
import time
import logging
from src.tools.channels.base_channel import (
    BaseChannel,
    ChannelStatus,
    ChannelHealthStatus,
    ChannelError,
)

logger = logging.getLogger(__name__)


class LocalChannel(BaseChannel):
    """
    本地工具调用通道

    直接调用本地注册的工具实例
    """

    def __init__(self, name: str = "local", config: Optional[Dict[str, Any]] = None):
        """
        初始化本地通道

        Args:
            name: 通道名称
            config: 通道配置（本地通道无需配置）
        """
        super().__init__(name, config)
        self._registry = None

    async def initialize(self) -> bool:
        """
        初始化通道

        Returns:
            初始化成功返回True
        """
        try:
            logger.info(f"[{self.name}] 初始化本地通道")

            # 本地通道无需特殊初始化
            self._initialized = True
            self._health_status.status = ChannelStatus.HEALTHY
            self._health_status.timestamp = datetime.now()

            logger.info(f"[{self.name}] 本地通道初始化成功")
            return True

        except Exception as e:
            logger.error(f"[{self.name}] 初始化失败: {e}")
            self._health_status.status = ChannelStatus.DOWN
            self._health_status.error = str(e)
            return False

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        调用工具

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            工具执行结果

        Raises:
            ChannelError: 工具调用失败
        """
        if not self._initialized:
            raise ChannelError(f"通道 {self.name} 未初始化")

        start_time = time.time()

        try:
            logger.debug(f"[{self.name}] 调用工具: {tool_name}, 参数: {params}")

            # 懒加载registry（避免循环导入）
            if self._registry is None:
                from src.tools.registry import get_tool_registry
                self._registry = get_tool_registry()

            # 从registry获取工具实例
            tool = self._registry.get(tool_name)
            if tool is None:
                raise ChannelError(f"工具 {tool_name} 未找到")

            # 直接调用工具
            result = tool.invoke(params)

            # 更新健康状态
            latency_ms = (time.time() - start_time) * 1000
            self._health_status.status = ChannelStatus.HEALTHY
            self._health_status.latency_ms = latency_ms
            self._health_status.error = None
            self._health_status.consecutive_failures = 0
            self._health_status.consecutive_successes += 1
            self._health_status.timestamp = datetime.now()

            logger.debug(f"[{self.name}] 工具调用成功: {tool_name}, 耗时: {latency_ms:.2f}ms")
            return result

        except Exception as e:
            # 更新健康状态
            latency_ms = (time.time() - start_time) * 1000
            self._health_status.latency_ms = latency_ms
            self._health_status.error = str(e)
            self._health_status.consecutive_failures += 1
            self._health_status.consecutive_successes = 0
            self._health_status.timestamp = datetime.now()

            # 根据连续失败次数调整状态
            if self._health_status.consecutive_failures >= 3:
                self._health_status.status = ChannelStatus.DOWN
            elif self._health_status.consecutive_failures >= 1:
                self._health_status.status = ChannelStatus.DEGRADED

            logger.error(f"[{self.name}] 工具调用失败 {tool_name}: {e}")
            raise ChannelError(f"本地工具调用失败: {e}") from e

    async def health_check(self) -> ChannelHealthStatus:
        """
        健康检查

        Returns:
            通道健康状态
        """
        if not self._initialized:
            self._health_status.status = ChannelStatus.UNKNOWN
            self._health_status.error = "通道未初始化"
            return self._health_status

        start_time = time.time()

        try:
            # 本地通道健康检查：验证registry可用
            if self._registry is None:
                from src.tools.registry import get_tool_registry
                self._registry = get_tool_registry()

            # 检查registry是否有工具
            tools = self._registry.list_tools()

            latency_ms = (time.time() - start_time) * 1000

            self._health_status.status = ChannelStatus.HEALTHY
            self._health_status.latency_ms = latency_ms
            self._health_status.error = None
            self._health_status.timestamp = datetime.now()

            logger.debug(f"[{self.name}] 健康检查通过, 可用工具数: {len(tools)}, 耗时: {latency_ms:.2f}ms")

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            self._health_status.status = ChannelStatus.DOWN
            self._health_status.latency_ms = latency_ms
            self._health_status.error = str(e)
            self._health_status.timestamp = datetime.now()

            logger.error(f"[{self.name}] 健康检查失败: {e}")

        return self._health_status

    async def close(self) -> None:
        """
        关闭通道

        本地通道无需清理资源
        """
        logger.info(f"[{self.name}] 关闭本地通道")
        self._initialized = False
        self._registry = None
        self._health_status.status = ChannelStatus.UNKNOWN


def get_local_channel(name: str = "local", config: Optional[Dict[str, Any]] = None) -> LocalChannel:
    """
    获取本地通道实例（便捷函数）

    Args:
        name: 通道名称
        config: 通道配置

    Returns:
        LocalChannel实例
    """
    return LocalChannel(name, config)
