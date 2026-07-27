"""
Tests for Tool Plugin Loader
测试工具插件加载器的功能
"""
import unittest
from pathlib import Path
from src.tools.plugin_loader import ToolPluginLoader, get_plugin_loader, ToolMetadata
from src.tools.base_tool import BaseTool


class TestPluginLoader(unittest.TestCase):
    """测试插件加载器"""

    def setUp(self):
        """测试前准备"""
        self.loader = ToolPluginLoader()

    def test_discover_tools(self):
        """测试工具发现"""
        print("\n[TEST] 测试工具发现...")
        tools = self.loader.discover_tools()

        self.assertIsInstance(tools, dict)
        self.assertGreater(len(tools), 0, "应该发现至少一个工具")

        print(f"[PASS] 发现 {len(tools)} 个工具")
        for tool_name in list(tools.keys())[:3]:
            print(f"  - {tool_name}")

    def test_tool_metadata(self):
        """测试工具元数据提取"""
        print("\n[TEST] 测试工具元数据...")
        tools = self.loader.discover_tools()

        # 取第一个工具测试
        if tools:
            tool_name = list(tools.keys())[0]
            metadata = tools[tool_name]

            self.assertIsInstance(metadata, ToolMetadata)
            self.assertEqual(metadata.name, tool_name)
            self.assertIsNotNone(metadata.description)
            self.assertIsNotNone(metadata.module_path)
            self.assertIsNotNone(metadata.class_name)
            self.assertTrue(issubclass(metadata.tool_class, BaseTool))

            print(f"[PASS] 工具元数据提取成功: {tool_name}")
            print(f"  - 模块路径: {metadata.module_path}")
            print(f"  - 类名: {metadata.class_name}")
            print(f"  - 支持异步: {metadata.has_async}")

    def test_get_tool_metadata(self):
        """测试获取指定工具的元数据"""
        print("\n[TEST] 测试获取指定工具元数据...")

        # 先发现工具
        self.loader.discover_tools()

        # 尝试获取 query_weather 工具
        metadata = self.loader.get_tool_metadata("query_weather")

        if metadata:
            self.assertEqual(metadata.name, "query_weather")
            print(f"[PASS] 获取工具元数据成功: query_weather")
        else:
            print(f"[INFO] 工具 query_weather 未找到，跳过测试")

    def test_list_tool_names(self):
        """测试列出所有工具名称"""
        print("\n[TEST] 测试列出所有工具名称...")

        tool_names = self.loader.list_tool_names()

        self.assertIsInstance(tool_names, list)
        self.assertGreater(len(tool_names), 0)

        print(f"[PASS] 列出 {len(tool_names)} 个工具名称")
        for name in tool_names[:5]:
            print(f"  - {name}")

    def test_load_tool_class(self):
        """测试加载工具类"""
        print("\n[TEST] 测试加载工具类...")

        # 先发现工具
        tools = self.loader.discover_tools()

        if tools:
            # 取第一个工具
            tool_name = list(tools.keys())[0]
            metadata = tools[tool_name]

            # 尝试加载工具类
            tool_class = self.loader.load_tool_class(
                metadata.module_path,
                metadata.class_name
            )

            self.assertIsNotNone(tool_class)
            self.assertTrue(issubclass(tool_class, BaseTool))

            # 尝试实例化
            tool_instance = tool_class()
            self.assertIsInstance(tool_instance, BaseTool)
            self.assertEqual(tool_instance.name, tool_name)

            print(f"[PASS] 加载并实例化工具成功: {tool_name}")

    def test_clear_cache(self):
        """测试清空缓存"""
        print("\n[TEST] 测试清空缓存...")

        # 先发现工具
        tools = self.loader.discover_tools()
        initial_count = len(tools)
        self.assertGreater(initial_count, 0)

        # 清空缓存
        self.loader.clear_cache()

        # 验证缓存已清空
        self.assertEqual(len(self.loader._tool_classes), 0)
        self.assertFalse(self.loader._scan_completed)

        # 再次发现应该重新扫描
        tools = self.loader.discover_tools()
        self.assertEqual(len(tools), initial_count)

        print(f"[PASS] 缓存清空并重新加载成功")

    def test_singleton_instance(self):
        """测试单例模式"""
        print("\n[TEST] 测试单例模式...")

        loader1 = get_plugin_loader()
        loader2 = get_plugin_loader()

        self.assertIs(loader1, loader2, "应该返回相同的实例")

        print(f"[PASS] 单例模式工作正常")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("  Tool Plugin Loader - Test Suite")
    print("=" * 70)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestPluginLoader)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print(f"  Total: {result.testsRun} tests | "
          f"Passed: {result.testsRun - len(result.failures) - len(result.errors)} | "
          f"Failed: {len(result.failures) + len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    run_tests()
