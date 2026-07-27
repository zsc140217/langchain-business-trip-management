"""
Tool Plugin Loader
动态发现和加载工具插件

Features:
- 扫描tools目录下的工具模块
- 通过反射机制动态导入工具类
- 缓存工具类定义
- 支持自定义插件目录
"""
import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Type, Optional
from dataclasses import dataclass
from src.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str
    description: str
    module_path: str
    class_name: str
    tool_class: Type[BaseTool]
    has_async: bool = False


class ToolPluginLoader:
    """
    工具插件加载器

    负责发现和加载工具插件
    """

    def __init__(self):
        """初始化插件加载器"""
        self._tool_classes: Dict[str, ToolMetadata] = {}
        self._scan_completed = False

    def discover_tools(self, scan_dirs: Optional[List[Path]] = None) -> Dict[str, ToolMetadata]:
        """
        发现所有可用的工具

        Args:
            scan_dirs: 要扫描的目录列表，默认为src/tools

        Returns:
            工具元数据字典 {tool_name: ToolMetadata}
        """
        if scan_dirs is None:
            # 默认扫描src/tools目录
            project_root = Path(__file__).parent.parent.parent
            scan_dirs = [project_root / "src" / "tools"]

        logger.info(f"[PluginLoader] 开始扫描工具目录: {scan_dirs}")

        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                logger.warning(f"[PluginLoader] 目录不存在: {scan_dir}")
                continue

            self._scan_directory(scan_dir)

        self._scan_completed = True
        logger.info(f"[PluginLoader] 发现 {len(self._tool_classes)} 个工具")
        return self._tool_classes.copy()

    def _scan_directory(self, directory: Path) -> None:
        """
        扫描目录下的工具模块

        Args:
            directory: 要扫描的目录
        """
        # 查找所有Python文件
        for file_path in directory.glob("*.py"):
            # 跳过特殊文件
            if file_path.name.startswith("_"):
                continue
            if file_path.name in ["base_tool.py", "mcp_client.py"]:
                continue

            # 只扫描包含 _tool.py 或 _adapter.py 的文件
            if not (file_path.name.endswith("_tool.py") or file_path.name.endswith("_adapter.py")):
                continue

            try:
                self._load_module(file_path)
            except Exception as e:
                logger.warning(f"[PluginLoader] 加载模块失败 {file_path}: {e}")

    def _load_module(self, file_path: Path) -> None:
        """
        加载模块并提取工具类

        Args:
            file_path: 模块文件路径
        """
        # 构建模块路径 (例如: src.tools.weather_tool)
        module_name = file_path.stem
        module_path = f"src.tools.{module_name}"

        try:
            # 动态导入模块
            module = importlib.import_module(module_path)

            # 查找模块中的工具类
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # 跳过导入的BaseTool基类
                if obj is BaseTool:
                    continue

                # 检查是否是BaseTool的子类
                if issubclass(obj, BaseTool) and obj != BaseTool:
                    # 提取工具元数据
                    tool_metadata = self._extract_metadata(obj, module_path, name)

                    if tool_metadata:
                        self._tool_classes[tool_metadata.name] = tool_metadata
                        logger.debug(f"[PluginLoader] 发现工具: {tool_metadata.name}")

        except Exception as e:
            logger.error(f"[PluginLoader] 导入模块失败 {module_path}: {e}")
            raise

    def _extract_metadata(
        self,
        tool_class: Type[BaseTool],
        module_path: str,
        class_name: str
    ) -> Optional[ToolMetadata]:
        """
        提取工具元数据

        Args:
            tool_class: 工具类
            module_path: 模块路径
            class_name: 类名

        Returns:
            工具元数据或None
        """
        try:
            # 获取工具名称和描述
            # 尝试从类的__annotations__获取，如果失败则实例化获取
            tool_name = None
            tool_description = None

            # 方法1: 尝试直接访问类属性
            if hasattr(tool_class, '__fields__'):
                # Pydantic模型
                fields = tool_class.__fields__
                if 'name' in fields:
                    tool_name = fields['name'].default
                if 'description' in fields:
                    tool_description = fields['description'].default

            # 方法2: 尝试从类字典获取
            if not tool_name:
                tool_name = tool_class.__dict__.get('name', None)
            if not tool_description:
                tool_description = tool_class.__dict__.get('description', None)

            # 方法3: 如果还是没有，尝试实例化（作为最后手段）
            if not tool_name:
                try:
                    instance = tool_class()
                    tool_name = getattr(instance, 'name', None)
                    tool_description = getattr(instance, 'description', None)
                except Exception:
                    pass

            if not tool_name:
                logger.warning(f"[PluginLoader] 工具类 {class_name} 缺少name属性")
                return None

            # 检查是否支持异步
            has_async = hasattr(tool_class, '_arun') and callable(getattr(tool_class, '_arun'))

            return ToolMetadata(
                name=tool_name,
                description=tool_description or "",
                module_path=module_path,
                class_name=class_name,
                tool_class=tool_class,
                has_async=has_async
            )

        except Exception as e:
            logger.error(f"[PluginLoader] 提取元数据失败 {class_name}: {e}")
            return None

    def load_tool_class(self, module_path: str, class_name: str) -> Type[BaseTool]:
        """
        加载指定的工具类

        Args:
            module_path: 模块路径 (例如: src.tools.weather_tool)
            class_name: 类名 (例如: WeatherTool)

        Returns:
            工具类

        Raises:
            ImportError: 模块导入失败
            AttributeError: 类不存在
        """
        try:
            # 动态导入模块
            module = importlib.import_module(module_path)

            # 获取类
            tool_class = getattr(module, class_name)

            # 验证是BaseTool的子类
            if not issubclass(tool_class, BaseTool):
                raise TypeError(f"{class_name} 不是 BaseTool 的子类")

            logger.debug(f"[PluginLoader] 加载工具类: {module_path}.{class_name}")
            return tool_class

        except Exception as e:
            logger.error(f"[PluginLoader] 加载工具类失败 {module_path}.{class_name}: {e}")
            raise

    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """
        获取工具元数据

        Args:
            tool_name: 工具名称

        Returns:
            工具元数据或None
        """
        if not self._scan_completed:
            self.discover_tools()

        return self._tool_classes.get(tool_name)

    def list_tool_names(self) -> List[str]:
        """
        列出所有发现的工具名称

        Returns:
            工具名称列表
        """
        if not self._scan_completed:
            self.discover_tools()

        return list(self._tool_classes.keys())

    def reload_module(self, module_path: str) -> None:
        """
        重新加载模块（用于开发时热重载）

        Args:
            module_path: 模块路径
        """
        try:
            module = importlib.import_module(module_path)
            importlib.reload(module)
            logger.info(f"[PluginLoader] 重新加载模块: {module_path}")
        except Exception as e:
            logger.error(f"[PluginLoader] 重新加载模块失败 {module_path}: {e}")
            raise

    def clear_cache(self) -> None:
        """清空工具类缓存"""
        self._tool_classes.clear()
        self._scan_completed = False
        logger.info("[PluginLoader] 已清空工具类缓存")


# 全局插件加载器实例
_plugin_loader_instance: Optional[ToolPluginLoader] = None


def get_plugin_loader() -> ToolPluginLoader:
    """
    获取全局插件加载器实例

    Returns:
        ToolPluginLoader实例
    """
    global _plugin_loader_instance

    if _plugin_loader_instance is None:
        _plugin_loader_instance = ToolPluginLoader()
        logger.info("[PluginLoader] 创建插件加载器实例")

    return _plugin_loader_instance
