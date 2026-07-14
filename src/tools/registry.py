"""
工具注册表 - 统一管理所有工具

提供：
1. 工具注册和发现
2. 工具生命周期管理
3. 工具统计和监控
"""
from typing import Dict, List, Optional
from src.tools.base_tool import BaseTool
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册表

    管理系统中所有可用的工具
    """

    def __init__(self):
        """初始化工具注册表"""
        self._tools: Dict[str, BaseTool] = {}
        self._initialized = False

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
        logger.info(f"[ToolRegistry] 注册工具: {tool.name}")

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
        for tool in self._tools.values():
            if hasattr(tool, 'close'):
                try:
                    tool.close()
                except Exception as e:
                    logger.warning(f"[ToolRegistry] 关闭工具 {tool.name} 失败: {e}")


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
