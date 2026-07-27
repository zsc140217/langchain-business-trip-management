"""
Tool Configuration Loader
Loads and validates tool configurations from YAML files

Features:
- YAML configuration loading
- Environment-specific configs (dev/prod)
- Configuration validation
- Hot reload support
- Configuration change detection
- Callback mechanism for config changes
"""
import yaml
import os
from typing import Dict, Any, Optional, Callable, Set
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConfigDiff:
    """配置差异"""
    added_tools: Set[str]           # 新增的工具
    removed_tools: Set[str]         # 移除的工具
    modified_tools: Set[str]        # 修改的工具
    enabled_tools: Set[str]         # 启用的工具
    disabled_tools: Set[str]        # 禁用的工具


class ToolConfigLoader:
    """
    Tool configuration loader

    Loads tool configurations from YAML files and provides
    access to tool settings
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader

        Args:
            config_path: Path to configuration file (defaults to config/tools.yaml)
        """
        if config_path is None:
            # Default to config/tools.yaml
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "tools.yaml"

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._loaded = False
        self._callbacks: list[Callable[[ConfigDiff], None]] = []  # 配置变更回调

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: Configuration file not found
            yaml.YAMLError: Invalid YAML syntax
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)

            logger.info(f"[ConfigLoader] Loaded configuration from {self.config_path}")
            self._loaded = True
            return self._config

        except yaml.YAMLError as e:
            logger.error(f"[ConfigLoader] Failed to parse YAML: {e}")
            raise
        except Exception as e:
            logger.error(f"[ConfigLoader] Failed to load configuration: {e}")
            raise

    def reload(self) -> Dict[str, Any]:
        """
        Reload configuration from file

        Returns:
            Updated configuration dictionary
        """
        logger.info("[ConfigLoader] Reloading configuration")

        # 保存旧配置
        old_config = self._config.copy()

        # 重新加载
        new_config = self.load()

        # 计算差异
        if old_config:
            diff = self.get_config_diff(old_config, new_config)

            # 触发回调
            if diff and self._callbacks:
                logger.info(f"[ConfigLoader] 配置变更: 新增{len(diff.added_tools)}个, "
                           f"移除{len(diff.removed_tools)}个, "
                           f"修改{len(diff.modified_tools)}个工具")
                for callback in self._callbacks:
                    try:
                        callback(diff)
                    except Exception as e:
                        logger.error(f"[ConfigLoader] 配置变更回调失败: {e}")

        return new_config

    def get_tool_config(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific tool

        Args:
            tool_name: Tool name

        Returns:
            Tool configuration dictionary or None if not found
        """
        if not self._loaded:
            self.load()

        tools = self._config.get('tools', {})
        return tools.get(tool_name)

    def get_global_timeout(self) -> int:
        """
        Get global default timeout

        Returns:
            Timeout in seconds
        """
        if not self._loaded:
            self.load()

        return self._config.get('timeouts', {}).get('global', {}).get('default', 30)

    def get_tool_timeout(self, tool_name: str) -> Dict[str, int]:
        """
        Get timeout settings for a specific tool

        Args:
            tool_name: Tool name

        Returns:
            Dictionary with 'call' and 'total' timeout values
        """
        if not self._loaded:
            self.load()

        tool_timeouts = self._config.get('timeouts', {}).get('tools', {}).get(tool_name, {})
        global_default = self.get_global_timeout()

        return {
            'call': tool_timeouts.get('call', global_default),
            'total': tool_timeouts.get('total', global_default)
        }

    def get_health_check_config(self) -> Dict[str, Any]:
        """
        Get health check configuration

        Returns:
            Health check configuration dictionary
        """
        if not self._loaded:
            self.load()

        return self._config.get('health_check', {
            'enabled': True,
            'interval': 60,
            'failure_threshold': 3,
            'success_threshold': 2
        })

    def get_channel_config(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific channel

        Args:
            channel_name: Channel name (mcp/http/grpc/local)

        Returns:
            Channel configuration dictionary or None if not found
        """
        if not self._loaded:
            self.load()

        channels = self._config.get('channels', {})
        return channels.get(channel_name)

    def is_tool_enabled(self, tool_name: str) -> bool:
        """
        Check if a tool is enabled

        Args:
            tool_name: Tool name

        Returns:
            True if tool is enabled, False otherwise
        """
        tool_config = self.get_tool_config(tool_name)
        if tool_config is None:
            return False

        return tool_config.get('enabled', True)

    def get_all_enabled_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all enabled tools and their configurations

        Returns:
            Dictionary of enabled tools {tool_name: config}
        """
        if not self._loaded:
            self.load()

        tools = self._config.get('tools', {})
        enabled_tools = {}

        for tool_name, tool_config in tools.items():
            if tool_config.get('enabled', True):
                enabled_tools[tool_name] = tool_config

        return enabled_tools

    def validate_config(self) -> bool:
        """
        Validate configuration structure and values

        Returns:
            True if configuration is valid

        Raises:
            ValueError: Configuration validation failed
        """
        if not self._loaded:
            self.load()

        # Check required top-level keys
        required_keys = ['tools']
        for key in required_keys:
            if key not in self._config:
                raise ValueError(f"Missing required configuration key: {key}")

        # Validate each tool configuration
        tools = self._config.get('tools', {})
        for tool_name, tool_config in tools.items():
            self._validate_tool_config(tool_name, tool_config)

        logger.info("[ConfigLoader] Configuration validation passed")
        return True

    def _validate_tool_config(self, tool_name: str, config: Dict[str, Any]) -> None:
        """
        Validate a single tool configuration

        Args:
            tool_name: Tool name
            config: Tool configuration dictionary

        Raises:
            ValueError: Tool configuration is invalid
        """
        # Check cache_ttl is non-negative
        cache_ttl = config.get('cache_ttl', 0)
        if cache_ttl < 0:
            raise ValueError(f"Tool {tool_name}: cache_ttl must be non-negative")

        # Check max_retries is positive
        max_retries = config.get('max_retries', 1)
        if max_retries < 1:
            raise ValueError(f"Tool {tool_name}: max_retries must be at least 1")

        # Check timeout is positive
        timeout = config.get('timeout', 30)
        if timeout <= 0:
            raise ValueError(f"Tool {tool_name}: timeout must be positive")

        # Check channel is valid
        valid_channels = ['mcp', 'http', 'grpc', 'local']
        channel = config.get('channel', 'local')
        if channel not in valid_channels:
            raise ValueError(f"Tool {tool_name}: invalid channel '{channel}', must be one of {valid_channels}")

    def watch_config_changes(self, callback: Callable[[ConfigDiff], None]) -> None:
        """
        注册配置变更回调

        Args:
            callback: 回调函数，接收 ConfigDiff 参数
        """
        self._callbacks.append(callback)
        logger.info(f"[ConfigLoader] 注册配置变更回调，当前共 {len(self._callbacks)} 个")

    def get_config_diff(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> ConfigDiff:
        """
        计算配置差异

        Args:
            old_config: 旧配置
            new_config: 新配置

        Returns:
            配置差异对象
        """
        old_tools = old_config.get('tools', {})
        new_tools = new_config.get('tools', {})

        old_tool_names = set(old_tools.keys())
        new_tool_names = set(new_tools.keys())

        # 新增和移除的工具
        added_tools = new_tool_names - old_tool_names
        removed_tools = old_tool_names - new_tool_names

        # 修改的工具（配置发生变化）
        modified_tools = set()
        for tool_name in old_tool_names & new_tool_names:
            if old_tools[tool_name] != new_tools[tool_name]:
                modified_tools.add(tool_name)

        # 启用和禁用的工具
        enabled_tools = set()
        disabled_tools = set()

        for tool_name in old_tool_names & new_tool_names:
            old_enabled = old_tools[tool_name].get('enabled', True)
            new_enabled = new_tools[tool_name].get('enabled', True)

            if not old_enabled and new_enabled:
                enabled_tools.add(tool_name)
            elif old_enabled and not new_enabled:
                disabled_tools.add(tool_name)

        return ConfigDiff(
            added_tools=added_tools,
            removed_tools=removed_tools,
            modified_tools=modified_tools,
            enabled_tools=enabled_tools,
            disabled_tools=disabled_tools
        )


# Global configuration loader instance
_config_loader_instance: Optional[ToolConfigLoader] = None


def get_config_loader() -> ToolConfigLoader:
    """
    Get global configuration loader instance

    Returns:
        ToolConfigLoader instance
    """
    global _config_loader_instance

    if _config_loader_instance is None:
        _config_loader_instance = ToolConfigLoader()
        _config_loader_instance.load()

    return _config_loader_instance


def reload_config() -> Dict[str, Any]:
    """
    Reload configuration from file

    Returns:
        Updated configuration dictionary
    """
    loader = get_config_loader()
    return loader.reload()
