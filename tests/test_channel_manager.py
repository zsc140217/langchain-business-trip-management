"""
Test Channel Manager
通道管理器测试

测试通道注册、路由、健康检查和故障转移功能
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.tools.channels.channel_manager import ChannelManager, get_channel_manager
from src.tools.channels.base_channel import ChannelStatus, ChannelHealthStatus, ChannelError
from src.tools.channels.local_channel import LocalChannel

# 配置 pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


class TestChannelManager:
    """通道管理器测试"""

    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            "channels": {
                "local": {"enabled": True},
                "mcp": {"enabled": False}
            },
            "tools": {
                "test_tool": {
                    "enabled": True,
                    "channel": "local"
                },
                "test_tool_with_fallback": {
                    "enabled": True,
                    "channel": "local",
                    "fallback_channel": "mcp"
                }
            }
        }

    @pytest.mark.asyncio
    async def test_channel_manager_initialization(self, mock_config):
        """测试通道管理器初始化"""
        manager = ChannelManager()

        with patch('src.tools.config_loader.get_config_loader') as mock_loader:
            mock_loader.return_value.config = mock_config

            await manager.initialize(mock_config)

            assert manager._initialized
            assert "local" in manager.list_channels()

    @pytest.mark.asyncio
    async def test_register_channel(self):
        """测试通道注册"""
        manager = ChannelManager()
        mock_channel = Mock(spec=LocalChannel)
        mock_channel.initialize = AsyncMock(return_value=True)
        mock_channel.name = "test_channel"

        await manager.register_channel("test_channel", mock_channel)

        assert "test_channel" in manager.list_channels()
        assert manager.get_channel("test_channel") == mock_channel

    @pytest.mark.asyncio
    async def test_get_channel_for_tool(self, mock_config):
        """测试获取工具对应的通道"""
        manager = ChannelManager()

        with patch('src.tools.config_loader.get_config_loader') as mock_loader:
            mock_loader.return_value.config = mock_config
            await manager.initialize(mock_config)

            channel_name = manager.get_channel_for_tool("test_tool")
            assert channel_name == "local"

    @pytest.mark.asyncio
    async def test_route_tool_call_success(self, mock_config):
        """测试工具调用路由成功"""
        manager = ChannelManager()

        # 创建mock通道
        mock_channel = Mock(spec=LocalChannel)
        mock_channel.initialize = AsyncMock(return_value=True)
        mock_channel.is_healthy = Mock(return_value=True)
        mock_channel.call_tool = AsyncMock(return_value="success")
        mock_channel.name = "local"

        with patch('src.tools.config_loader.get_config_loader') as mock_loader:
            mock_loader.return_value.config = mock_config

            # 手动注册mock通道
            await manager.register_channel("local", mock_channel)
            manager._build_tool_channel_mapping(mock_config)
            manager._initialized = True

            result = await manager.route_tool_call("test_tool", {"param": "value"})

            assert result == "success"
            mock_channel.call_tool.assert_called_once_with("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_route_tool_call_fallback(self, mock_config):
        """测试通道故障转移"""
        manager = ChannelManager()

        # 主通道（不健康）
        primary_channel = Mock(spec=LocalChannel)
        primary_channel.initialize = AsyncMock(return_value=True)
        primary_channel.is_healthy = Mock(return_value=False)
        primary_channel.name = "local"

        # 备用通道（健康）
        fallback_channel = Mock(spec=LocalChannel)
        fallback_channel.initialize = AsyncMock(return_value=True)
        fallback_channel.is_healthy = Mock(return_value=True)
        fallback_channel.call_tool = AsyncMock(return_value="fallback_success")
        fallback_channel.name = "mcp"

        with patch('src.tools.config_loader.get_config_loader') as mock_loader:
            mock_loader.return_value.config = mock_config

            await manager.register_channel("local", primary_channel)
            await manager.register_channel("mcp", fallback_channel)
            manager._build_tool_channel_mapping(mock_config)
            manager._initialized = True

            result = await manager.route_tool_call(
                "test_tool_with_fallback",
                {"param": "value"}
            )

            assert result == "fallback_success"
            fallback_channel.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check(self, mock_config):
        """测试健康检查"""
        manager = ChannelManager()

        mock_channel = Mock(spec=LocalChannel)
        mock_channel.initialize = AsyncMock(return_value=True)
        mock_channel.get_health_status = Mock(return_value=ChannelHealthStatus(
            status=ChannelStatus.HEALTHY,
            latency_ms=10.0,
            error=None,
            timestamp=None
        ))
        mock_channel.name = "local"

        with patch('src.tools.config_loader.get_config_loader') as mock_loader:
            mock_loader.return_value.config = mock_config

            await manager.register_channel("local", mock_channel)
            manager._initialized = True

            health_status = manager.get_all_channel_health()

            assert "local" in health_status
            assert health_status["local"].status == ChannelStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_close_all_channels(self, mock_config):
        """测试关闭所有通道"""
        manager = ChannelManager()

        mock_channel = Mock(spec=LocalChannel)
        mock_channel.initialize = AsyncMock(return_value=True)
        mock_channel.close = AsyncMock()
        mock_channel.name = "local"

        with patch('src.tools.config_loader.get_config_loader') as mock_loader:
            mock_loader.return_value.config = mock_config

            await manager.register_channel("local", mock_channel)
            manager._initialized = True

            await manager.close_all()

            mock_channel.close.assert_called_once()
            assert not manager._initialized
            assert len(manager.list_channels()) == 0

    def test_get_channel_manager_singleton(self):
        """测试通道管理器单例"""
        manager1 = get_channel_manager()
        manager2 = get_channel_manager()

        assert manager1 is manager2


if __name__ == "__main__":
    print("=" * 70)
    print("Channel Manager Test Suite")
    print("=" * 70)

    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
