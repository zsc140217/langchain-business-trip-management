"""
工具注册表 - 统一管理所有工具

提供：
1. 工具注册和发现
2. 工具生命周期管理
3. 工具统计和监控
4. 动态工具加载/卸载
5. 工具状态管理
"""
from typing import Dict, List, Optional
from enum import Enum
from src.tools.base_tool import BaseTool
import logging

logger = logging.getLogger(__name__)


class ToolState(Enum):
    """工具状态枚举"""
    UNKNOWN = "unknown"           # 未加载
    LOADING = "loading"           # 加载中
    LOADED = "loaded"             # 已加载
    DISABLED = "disabled"         # 已禁用
    FAILED = "failed"             # 加载失败
    UNLOADING = "unloading"       # 卸载中


class ToolRegistry:
    """
    工具注册表

    管理系统中所有可用的工具
    """

    def __init__(self):
        """初始化工具注册表"""
        self._tools: Dict[str, BaseTool] = {}
        self._tool_states: Dict[str, ToolState] = {}  # 工具状态跟踪
        self._initialized = False
        self._health_check_enabled = False

    def register(self, tool: BaseTool) -> None:
        """
        注册工具

        Args:
            tool: 工具实例

        Raises:
            ValueError: 工具名称重复
        """
        if tool.name in self._tools:
            logger.warning(f"[ToolRegistry] 工具 '{tool.name}' 已存在，将被覆盖")

        self._tools[tool.name] = tool
        self._tool_states[tool.name] = ToolState.LOADED
        logger.info(f"[ToolRegistry] 注册工具: {tool.name}")

    def load_tool(self, tool_name: str) -> bool:
        """
        动态加载工具

        Args:
            tool_name: 工具名称

        Returns:
            加载成功返回True，否则返回False
        """
        # 检查是否已加载
        if tool_name in self._tools:
            logger.warning(f"[ToolRegistry] 工具 '{tool_name}' 已加载")
            return True

        # 检查配置是否启用
        try:
            from src.tools.config_loader import get_config_loader
            config_loader = get_config_loader()
            if not config_loader.is_tool_enabled(tool_name):
                logger.warning(f"[ToolRegistry] 工具 '{tool_name}' 在配置中被禁用")
                self._tool_states[tool_name] = ToolState.DISABLED
                return False
        except Exception as e:
            logger.warning(f"[ToolRegistry] 检查工具配置失败: {e}")

        # 设置加载状态
        self._tool_states[tool_name] = ToolState.LOADING
        logger.info(f"[ToolRegistry] 开始加载工具: {tool_name}")

        try:
            # 使用插件加载器发现工具
            from src.tools.plugin_loader import get_plugin_loader
            plugin_loader = get_plugin_loader()
            tool_metadata = plugin_loader.get_tool_metadata(tool_name)

            if tool_metadata is None:
                logger.error(f"[ToolRegistry] 未找到工具: {tool_name}")
                self._tool_states[tool_name] = ToolState.FAILED
                return False

            # 实例化工具
            tool_instance = tool_metadata.tool_class()

            # 注册工具
            self.register(tool_instance)
            logger.info(f"[ToolRegistry] 工具加载成功: {tool_name}")
            return True

        except Exception as e:
            logger.error(f"[ToolRegistry] 加载工具失败 {tool_name}: {e}")
            self._tool_states[tool_name] = ToolState.FAILED
            return False

    def unload_tool(self, tool_name: str) -> bool:
        """
        卸载工具

        Args:
            tool_name: 工具名称

        Returns:
            卸载成功返回True，否则返回False
        """
        if tool_name not in self._tools:
            logger.warning(f"[ToolRegistry] 工具 '{tool_name}' 未加载")
            return False

        # 设置卸载状态
        self._tool_states[tool_name] = ToolState.UNLOADING
        logger.info(f"[ToolRegistry] 开始卸载工具: {tool_name}")

        try:
            tool = self._tools[tool_name]

            # 清理资源
            if hasattr(tool, 'close'):
                tool.close()

            if hasattr(tool, 'clear_cache'):
                tool.clear_cache()

            # 从注册表移除
            del self._tools[tool_name]
            self._tool_states[tool_name] = ToolState.UNKNOWN

            logger.info(f"[ToolRegistry] 工具卸载成功: {tool_name}")
            return True

        except Exception as e:
            logger.error(f"[ToolRegistry] 卸载工具失败 {tool_name}: {e}")
            self._tool_states[tool_name] = ToolState.FAILED
            return False

    def reload_tool(self, tool_name: str) -> bool:
        """
        重新加载工具

        Args:
            tool_name: 工具名称

        Returns:
            重新加载成功返回True，否则返回False
        """
        logger.info(f"[ToolRegistry] 重新加载工具: {tool_name}")

        # 先卸载
        if tool_name in self._tools:
            if not self.unload_tool(tool_name):
                logger.error(f"[ToolRegistry] 卸载工具失败，无法重新加载: {tool_name}")
                return False

        # 重新加载模块（清除Python模块缓存）
        try:
            from src.tools.plugin_loader import get_plugin_loader
            plugin_loader = get_plugin_loader()
            tool_metadata = plugin_loader.get_tool_metadata(tool_name)

            if tool_metadata:
                plugin_loader.reload_module(tool_metadata.module_path)
                # 清除缓存，重新发现
                plugin_loader.clear_cache()
        except Exception as e:
            logger.warning(f"[ToolRegistry] 重新加载模块失败: {e}")

        # 再加载
        return self.load_tool(tool_name)

    def enable_tool(self, tool_name: str) -> bool:
        """
        启用工具

        Args:
            tool_name: 工具名称

        Returns:
            启用成功返回True，否则返回False
        """
        if tool_name in self._tools:
            self._tool_states[tool_name] = ToolState.LOADED
            logger.info(f"[ToolRegistry] 工具已启用: {tool_name}")
            return True

        # 如果未加载，尝试加载
        return self.load_tool(tool_name)

    def disable_tool(self, tool_name: str) -> bool:
        """
        禁用工具（不卸载，仅标记为禁用）

        Args:
            tool_name: 工具名称

        Returns:
            禁用成功返回True，否则返回False
        """
        if tool_name not in self._tools:
            logger.warning(f"[ToolRegistry] 工具 '{tool_name}' 未加载")
            return False

        self._tool_states[tool_name] = ToolState.DISABLED
        logger.info(f"[ToolRegistry] 工具已禁用: {tool_name}")
        return True

    def get_tool_state(self, tool_name: str) -> ToolState:
        """
        获取工具状态

        Args:
            tool_name: 工具名称

        Returns:
            工具状态
        """
        return self._tool_states.get(tool_name, ToolState.UNKNOWN)

    def get_all_tool_states(self) -> Dict[str, ToolState]:
        """
        获取所有工具的状态

        Returns:
            工具状态字典 {tool_name: ToolState}
        """
        return self._tool_states.copy()

    def discover_available_tools(self) -> List[str]:
        """
        发现所有可用的工具（不加载）

        Returns:
            可用工具名称列表
        """
        try:
            from src.tools.plugin_loader import get_plugin_loader
            plugin_loader = get_plugin_loader()
            return plugin_loader.list_tool_names()
        except Exception as e:
            logger.error(f"[ToolRegistry] 发现工具失败: {e}")
            return []

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取工具

        Args:
            tool_name: 工具名称

        Returns:
            工具实例，如果不存在返回 None
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """
        列出所有工具名称

        Returns:
            工具名称列表
        """
        return list(self._tools.keys())

    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        获取所有工具

        Returns:
            工具字典 {name: tool}
        """
        return self._tools.copy()

    def initialize_all(self) -> None:
        """
        初始化所有工具（延迟加载）

        注意：某些工具可能在首次使用时才真正初始化
        """
        if self._initialized:
            return

        logger.info("[ToolRegistry] 开始初始化所有工具")

        try:
            # 注册政策检索工具
            from src.tools.search_policy_tool import get_search_policy_tool
            self.register(get_search_policy_tool())

            # 注册图谱查询工具
            from src.tools.query_graph_tool import get_query_graph_tool
            self.register(get_query_graph_tool())

            # 注册天气查询工具
            from src.tools.weather_adapter import get_weather_tool
            self.register(get_weather_tool())

            # 注册酒店查询工具
            from src.tools.hotel_adapter import get_hotel_tool
            self.register(get_hotel_tool())

            # 注册航班查询工具
            from src.tools.flight_adapter import get_flight_tool
            self.register(get_flight_tool())

            # 注册审批状态查询工具
            from src.tools.check_approval_status_tool import get_check_approval_status_tool
            self.register(get_check_approval_status_tool())

            # 注册取消审批工具
            from src.tools.cancel_approval_tool import get_cancel_approval_tool
            self.register(get_cancel_approval_tool())

            # 注册记忆查询工具
            from src.tools.query_memory_tool import QueryMemoryTool
            from src.memory.memory_service import MemoryService
            memory_service = MemoryService()
            self.register(QueryMemoryTool(memory_service=memory_service))

            logger.info(f"[ToolRegistry] 工具初始化完成，共 {len(self._tools)} 个工具")
            self._initialized = True

        except Exception as e:
            logger.error(f"[ToolRegistry] 工具初始化失败: {e}")
            raise

    def get_stats(self) -> Dict[str, Dict]:
        """
        获取所有工具的统计数据

        Returns:
            统计数据字典
        """
        stats = {}
        for name, tool in self._tools.items():
            try:
                # 尝试获取工具统计（如果支持）
                if hasattr(tool, 'get_stats'):
                    stats[name] = tool.get_stats()
                else:
                    stats[name] = {"status": "active"}
            except Exception as e:
                logger.warning(f"[ToolRegistry] 获取工具 {name} 统计失败: {e}")
                stats[name] = {"status": "error", "error": str(e)}

        return stats

    def clear_all_caches(self) -> None:
        """清空所有工具的缓存"""
        logger.info("[ToolRegistry] 清空所有工具缓存")
        for tool in self._tools.values():
            if hasattr(tool, 'clear_cache'):
                try:
                    tool.clear_cache()
                except Exception as e:
                    logger.warning(f"[ToolRegistry] 清空工具 {tool.name} 缓存失败: {e}")

    def close_all(self) -> None:
        """关闭所有工具（清理资源）"""
        logger.info("[ToolRegistry] 关闭所有工具")

        # Stop health checking if enabled
        if self._health_check_enabled:
            self.disable_health_check()

        for tool in self._tools.values():
            if hasattr(tool, 'close'):
                try:
                    tool.close()
                except Exception as e:
                    logger.warning(f"[ToolRegistry] 关闭工具 {tool.name} 失败: {e}")

    def enable_health_check(self) -> None:
        """启用健康检查"""
        if self._health_check_enabled:
            logger.warning("[ToolRegistry] 健康检查已启用")
            return

        try:
            from src.tools.health_check import get_health_checker
            health_checker = get_health_checker()

            # Register all tools for health checking
            for tool_name, tool in self._tools.items():
                if hasattr(tool, 'health_check'):
                    health_checker.register_tool(tool_name, tool.health_check)

            # Start health checking
            health_checker.start()
            self._health_check_enabled = True
            logger.info("[ToolRegistry] 健康检查已启用")

        except Exception as e:
            logger.error(f"[ToolRegistry] 启用健康检查失败: {e}")
            raise

    def disable_health_check(self) -> None:
        """禁用健康检查"""
        if not self._health_check_enabled:
            return

        try:
            from src.tools.health_check import stop_health_checking
            stop_health_checking()
            self._health_check_enabled = False
            logger.info("[ToolRegistry] 健康检查已禁用")

        except Exception as e:
            logger.error(f"[ToolRegistry] 禁用健康检查失败: {e}")

    def get_health_status(self) -> Dict:
        """
        获取所有工具的健康状态

        Returns:
            健康状态字典
        """
        if not self._health_check_enabled:
            return {"error": "Health check not enabled"}

        try:
            from src.tools.health_check import get_health_checker
            health_checker = get_health_checker()
            health_status = health_checker.get_all_health_status()

            # Convert to serializable format
            result = {}
            for tool_name, status in health_status.items():
                result[tool_name] = {
                    "status": status.status.value,
                    "latency_ms": status.latency_ms,
                    "error": status.error,
                    "timestamp": status.timestamp.isoformat(),
                    "consecutive_failures": status.consecutive_failures,
                    "consecutive_successes": status.consecutive_successes
                }

            return result

        except Exception as e:
            logger.error(f"[ToolRegistry] 获取健康状态失败: {e}")
            return {"error": str(e)}


# 全局工具注册表单例
_registry_instance: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    获取工具注册表单例

    Returns:
        ToolRegistry 实例
    """
    global _registry_instance

    if _registry_instance is None:
        _registry_instance = ToolRegistry()
        logger.info("[ToolRegistry] 创建工具注册表单例")

    return _registry_instance


def get_all_tools() -> Dict[str, BaseTool]:
    """
    获取所有已注册的工具（便捷函数）

    Returns:
        工具字典 {name: tool}
    """
    registry = get_tool_registry()

    # 如果还未初始化，先初始化所有工具
    if not registry._initialized:
        registry.initialize_all()

    return registry.get_all_tools()
