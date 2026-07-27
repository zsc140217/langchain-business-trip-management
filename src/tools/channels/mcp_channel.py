"""
MCP Channel
MCP协议工具调用通道

通过MCP (Model Context Protocol) 调用远程工具服务器
基于现有的MCPClientManager实现
"""
from typing import Dict, Any, Optional
from datetime import datetime
import time
import asyncio
import logging
from src.tools.channels.base_channel import (
    BaseChannel,
    ChannelStatus,
    ChannelHealthStatus,
    ChannelError,
    ChannelTimeoutError,
    ChannelConnectionError,
)

logger = logging.getLogger(__name__)


class MCPChannel(BaseChannel):
    """
    MCP通道实现

    通过MCP协议调用远程工具
    """

    def __init__(self, name: str = "mcp", config: Optional[Dict[str, Any]] = None):
        """
        初始化MCP通道

        Args:
            name: 通道名称
            config: 通道配置
                - server_script: MCP服务器脚本路径
                - startup_timeout: 启动超时时间（秒）
        """
        super().__init__(name, config)
        self._client = None
        self._server_script = config.get("server_script") if config else None
        self._startup_timeout = config.get("startup_timeout", 10) if config else 10

    async def initialize(self) -> bool:
        """
        初始化通道（启动MCP客户端）

        Returns:
            初始化成功返回True
        """
        try:
            logger.info(f"[{self.name}] 初始化MCP通道")
            self._health_status.status = ChannelStatus.INITIALIZING

            # 导入MCP客户端
            from src.tools.mcp_client import MCPClientManager

            # 创建并启动MCP客户端
            self._client = MCPClientManager(server_script=self._server_script)
            self._client.start()

            # 等待连接就绪
            max_wait = self._startup_timeout
            for _ in range(max_wait * 10):
                if self._client._session:
                    break
                await asyncio.sleep(0.1)
            else:
                raise ChannelConnectionError("MCP客户端启动超时")

            self._initialized = True
            self._health_status.status = ChannelStatus.HEALTHY
            self._health_status.timestamp = datetime.now()

            logger.info(f"[{self.name}] MCP通道初始化成功")
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
            ChannelTimeoutError: 调用超时
        """
        if not self._initialized or not self._client:
            raise ChannelError(f"通道 {self.name} 未初始化")

        start_time = time.time()

        try:
            logger.debug(f"[{self.name}] 调用工具: {tool_name}, 参数: {params}")

            # 调用MCP工具（同步调用，在executor中执行）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._client.call_tool,
                tool_name,
                params
            )

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

        except asyncio.TimeoutError as e:
            # 超时错误
            latency_ms = (time.time() - start_time) * 1000
            self._health_status.latency_ms = latency_ms
            self._health_status.error = "调用超时"
            self._health_status.consecutive_failures += 1
            self._health_status.consecutive_successes = 0
            self._health_status.timestamp = datetime.now()

            if self._health_status.consecutive_failures >= 3:
                self._health_status.status = ChannelStatus.DOWN
            else:
                self._health_status.status = ChannelStatus.DEGRADED

            logger.error(f"[{self.name}] 工具调用超时 {tool_name}")
            raise ChannelTimeoutError(f"MCP工具调用超时: {tool_name}") from e

        except Exception as e:
            # 其他错误
            latency_ms = (time.time() - start_time) * 1000
            self._health_status.latency_ms = latency_ms
            self._health_status.error = str(e)
            self._health_status.consecutive_failures += 1
            self._health_status.consecutive_successes = 0
            self._health_status.timestamp = datetime.now()

            if self._health_status.consecutive_failures >= 3:
                self._health_status.status = ChannelStatus.DOWN
            else:
                self._health_status.status = ChannelStatus.DEGRADED

            logger.error(f"[{self.name}] 工具调用失败 {tool_name}: {e}")
            raise ChannelError(f"MCP工具调用失败: {e}") from e

    async def health_check(self) -> ChannelHealthStatus:
        """
        健康检查

        Returns:
            通道健康状态
        """
        if not self._initialized or not self._client:
            self._health_status.status = ChannelStatus.UNKNOWN
            self._health_status.error = "通道未初始化"
            return self._health_status

        start_time = time.time()

        try:
            # 检查MCP客户端连接状态
            if not self._client._session or not self._client._loop:
                raise ChannelConnectionError("MCP客户端未连接")

            # 尝试列出工具（健康检查）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client._session if self._client._session else None
            )

            latency_ms = (time.time() - start_time) * 1000

            self._health_status.status = ChannelStatus.HEALTHY
            self._health_status.latency_ms = latency_ms
            self._health_status.error = None
            self._health_status.timestamp = datetime.now()

            logger.debug(f"[{self.name}] 健康检查通过, 耗时: {latency_ms:.2f}ms")

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
        关闭通道（停止MCP客户端）
        """
        logger.info(f"[{self.name}] 关闭MCP通道")

        if self._client:
            try:
                self._client.stop()
            except Exception as e:
                logger.warning(f"[{self.name}] 停止MCP客户端时出错: {e}")

        self._client = None
        self._initialized = False
        self._health_status.status = ChannelStatus.UNKNOWN


def get_mcp_channel(name: str = "mcp", config: Optional[Dict[str, Any]] = None) -> MCPChannel:
    """
    获取MCP通道实例（便捷函数）

    Args:
        name: 通道名称
        config: 通道配置

    Returns:
        MCPChannel实例
    """
    return MCPChannel(name, config)
