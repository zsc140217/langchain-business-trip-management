"""
Channel Manager
通道管理器

管理所有通道实例，负责：
1. 通道注册和生命周期管理
2. 工具调用路由到正确的通道
3. 通道健康监控
4. 自动故障转移（fallback）
"""
from typing import Dict, Any, Optional, List
import asyncio
import logging
from src.tools.channels.base_channel import (
    BaseChannel,
    ChannelStatus,
    ChannelHealthStatus,
    ChannelError,
)

logger = logging.getLogger(__name__)


class ChannelManager:
    """
    通道管理器

    统一管理所有工具调用通道
    """

    def __init__(self):
        """初始化通道管理器"""
        self._channels: Dict[str, BaseChannel] = {}
        self._tool_channel_map: Dict[str, str] = {}  # tool_name -> channel_name
        self._tool_fallback_map: Dict[str, str] = {}  # tool_name -> fallback_channel_name
        self._initialized = False
        self._health_check_task: Optional[asyncio.Task] = None

    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化通道管理器

        Args:
            config: 配置字典，包含通道配置和工具映射
        """
        if self._initialized:
            logger.warning("[ChannelManager] 已经初始化")
            return

        logger.info("[ChannelManager] 开始初始化")

        try:
            # 加载配置
            if config is None:
                from src.tools.config_loader import get_config_loader
                config_loader = get_config_loader()
                config = config_loader.config

            # 注册通道
            await self._register_channels(config)

            # 构建工具-通道映射
            self._build_tool_channel_mapping(config)

            self._initialized = True
            logger.info(f"[ChannelManager] 初始化完成，注册了 {len(self._channels)} 个通道")

        except Exception as e:
            logger.error(f"[ChannelManager] 初始化失败: {e}")
            raise

    async def _register_channels(self, config: Dict[str, Any]) -> None:
        """
        注册所有启用的通道

        Args:
            config: 配置字典
        """
        channels_config = config.get("channels", {})

        # 注册local通道
        if channels_config.get("local", {}).get("enabled", True):
            from src.tools.channels.local_channel import LocalChannel
            local_channel = LocalChannel("local", channels_config.get("local", {}))
            await self.register_channel("local", local_channel)

        # 注册mcp通道
        if channels_config.get("mcp", {}).get("enabled", False):
            from src.tools.channels.mcp_channel import MCPChannel
            mcp_channel = MCPChannel("mcp", channels_config.get("mcp", {}))
            await self.register_channel("mcp", mcp_channel)

    def _build_tool_channel_mapping(self, config: Dict[str, Any]) -> None:
        """
        构建工具到通道的映射

        Args:
            config: 配置字典
        """
        tools_config = config.get("tools", {})

        for tool_name, tool_config in tools_config.items():
            if not tool_config.get("enabled", True):
                continue

            # 主通道
            channel_name = tool_config.get("channel", "local")
            self._tool_channel_map[tool_name] = channel_name

            # 备用通道（可选）
            fallback_channel = tool_config.get("fallback_channel")
            if fallback_channel:
                self._tool_fallback_map[tool_name] = fallback_channel

            logger.debug(f"[ChannelManager] 工具 {tool_name} 映射到通道 {channel_name}")

    async def register_channel(self, name: str, channel: BaseChannel) -> None:
        """
        注册通道

        Args:
            name: 通道名称
            channel: 通道实例
        """
        if name in self._channels:
            logger.warning(f"[ChannelManager] 通道 {name} 已存在，将被覆盖")

        # 初始化通道
        success = await channel.initialize()
        if not success:
            logger.error(f"[ChannelManager] 通道 {name} 初始化失败")
            raise ChannelError(f"通道 {name} 初始化失败")

        self._channels[name] = channel
        logger.info(f"[ChannelManager] 注册通道: {name}")

    def get_channel(self, name: str) -> Optional[BaseChannel]:
        """
        获取通道

        Args:
            name: 通道名称

        Returns:
            通道实例或None
        """
        return self._channels.get(name)

    def get_channel_for_tool(self, tool_name: str) -> Optional[str]:
        """
        获取工具对应的通道名称

        Args:
            tool_name: 工具名称

        Returns:
            通道名称或None
        """
        return self._tool_channel_map.get(tool_name)

    async def route_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        路由工具调用到正确的通道

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            工具执行结果

        Raises:
            ChannelError: 通道不可用或调用失败
        """
        if not self._initialized:
            raise ChannelError("通道管理器未初始化")

        # 获取主通道
        channel_name = self._tool_channel_map.get(tool_name)
        if not channel_name:
            # 如果没有配置，默认使用local通道
            channel_name = "local"
            logger.warning(f"[ChannelManager] 工具 {tool_name} 未配置通道，使用默认local通道")

        channel = self._channels.get(channel_name)
        if not channel:
            raise ChannelError(f"通道 {channel_name} 不存在")

        # 检查通道健康状态
        if not channel.is_healthy():
            logger.warning(f"[ChannelManager] 主通道 {channel_name} 不健康，尝试fallback")

            # 尝试使用备用通道
            fallback_channel_name = self._tool_fallback_map.get(tool_name)
            if fallback_channel_name:
                fallback_channel = self._channels.get(fallback_channel_name)
                if fallback_channel and fallback_channel.is_healthy():
                    logger.info(f"[ChannelManager] 使用备用通道 {fallback_channel_name}")
                    channel = fallback_channel
                    channel_name = fallback_channel_name
                else:
                    raise ChannelError(f"主通道和备用通道都不可用")
            else:
                raise ChannelError(f"通道 {channel_name} 不健康且没有配置备用通道")

        # 调用工具
        try:
            logger.debug(f"[ChannelManager] 通过通道 {channel_name} 调用工具 {tool_name}")
            result = await channel.call_tool(tool_name, params)
            return result

        except Exception as e:
            logger.error(f"[ChannelManager] 工具调用失败 {tool_name} via {channel_name}: {e}")

            # 如果主通道失败，尝试备用通道
            fallback_channel_name = self._tool_fallback_map.get(tool_name)
            if fallback_channel_name and fallback_channel_name != channel_name:
                fallback_channel = self._channels.get(fallback_channel_name)
                if fallback_channel and fallback_channel.is_healthy():
                    logger.info(f"[ChannelManager] 主通道失败，重试备用通道 {fallback_channel_name}")
                    try:
                        result = await fallback_channel.call_tool(tool_name, params)
                        return result
                    except Exception as fallback_error:
                        logger.error(f"[ChannelManager] 备用通道也失败: {fallback_error}")

            raise

    def enable_health_check(self, interval_seconds: int = 60) -> None:
        """
        启用健康检查

        Args:
            interval_seconds: 检查间隔（秒）
        """
        if self._health_check_task and not self._health_check_task.done():
            logger.warning("[ChannelManager] 健康检查已启用")
            return

        logger.info(f"[ChannelManager] 启用健康检查，间隔: {interval_seconds}秒")
        self._health_check_task = asyncio.create_task(
            self._health_check_loop(interval_seconds)
        )

    def disable_health_check(self) -> None:
        """禁用健康检查"""
        if self._health_check_task:
            self._health_check_task.cancel()
            self._health_check_task = None
            logger.info("[ChannelManager] 健康检查已禁用")

    async def _health_check_loop(self, interval_seconds: int) -> None:
        """
        健康检查循环

        Args:
            interval_seconds: 检查间隔（秒）
        """
        while True:
            try:
                await asyncio.sleep(interval_seconds)

                for name, channel in self._channels.items():
                    try:
                        status = await channel.health_check()
                        logger.debug(
                            f"[ChannelManager] 通道 {name} 健康状态: "
                            f"{status.status.value}, 延迟: {status.latency_ms:.2f}ms"
                        )
                    except Exception as e:
                        logger.error(f"[ChannelManager] 通道 {name} 健康检查失败: {e}")

            except asyncio.CancelledError:
                logger.info("[ChannelManager] 健康检查任务被取消")
                break
            except Exception as e:
                logger.error(f"[ChannelManager] 健康检查循环出错: {e}")

    def get_all_channel_health(self) -> Dict[str, ChannelHealthStatus]:
        """
        获取所有通道的健康状态

        Returns:
            通道健康状态字典
        """
        health_status = {}
        for name, channel in self._channels.items():
            health_status[name] = channel.get_health_status()

        return health_status

    def list_channels(self) -> List[str]:
        """
        列出所有通道名称

        Returns:
            通道名称列表
        """
        return list(self._channels.keys())

    async def close_all(self) -> None:
        """关闭所有通道"""
        logger.info("[ChannelManager] 关闭所有通道")

        # 停止健康检查
        self.disable_health_check()

        # 关闭所有通道
        for name, channel in self._channels.items():
            try:
                await channel.close()
            except Exception as e:
                logger.error(f"[ChannelManager] 关闭通道 {name} 失败: {e}")

        self._channels.clear()
        self._tool_channel_map.clear()
        self._tool_fallback_map.clear()
        self._initialized = False


_channel_manager_instance: Optional[ChannelManager] = None


def get_channel_manager() -> ChannelManager:
    """获取通道管理器单例"""
    global _channel_manager_instance

    if _channel_manager_instance is None:
        _channel_manager_instance = ChannelManager()
        logger.info("[ChannelManager] 创建通道管理器单例")

    return _channel_manager_instance
