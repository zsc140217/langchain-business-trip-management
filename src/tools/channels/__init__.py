"""
Tool Channels Package
工具调用通道包

提供多种工具调用通道实现：
- LocalChannel: 直接调用本地工具
- MCPChannel: 通过MCP协议调用远程工具
- HTTPChannel: 通过REST API调用远程工具

所有通道都实现统一的BaseChannel接口
"""
from src.tools.channels.base_channel import (
    BaseChannel,
    ChannelStatus,
    ChannelHealthStatus,
    ChannelError,
    ChannelTimeoutError,
    ChannelConnectionError,
)
from src.tools.channels.local_channel import LocalChannel, get_local_channel
from src.tools.channels.mcp_channel import MCPChannel, get_mcp_channel
from src.tools.channels.channel_manager import ChannelManager, get_channel_manager

__all__ = [
    # Base classes and types
    "BaseChannel",
    "ChannelStatus",
    "ChannelHealthStatus",

    # Exceptions
    "ChannelError",
    "ChannelTimeoutError",
    "ChannelConnectionError",

    # Channel implementations
    "LocalChannel",
    "MCPChannel",
    "get_local_channel",
    "get_mcp_channel",

    # Manager
    "ChannelManager",
    "get_channel_manager",
]
