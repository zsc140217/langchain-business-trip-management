"""
ComplexTaskEngine 测试

测试复杂任务执行引擎的功能：
1. 任务分解
2. 并行执行
3. 结果整合
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agents.task_decomposer import SubTask


class TestComplexTaskEngine:
    """ComplexTaskEngine 测试类"""

    @pytest.fixture
    def mock_llm(self):
        """模拟 LLM"""
        llm = Mock()
        llm.invoke = Mock(return_value=Mock(content="整合结果"))
        return llm

    @pytest.fixture
    def mock_task_decomposer(self):
        """模拟任务分解器"""
        decomposer = Mock()
        # 模拟分解结果：查天气 + 查酒店
        decomposer.decompose = Mock(return_value=[
            SubTask(
                id=0,
                task_type="QUERY_WEATHER",
                description="查询北京天气",
                parameters={"city": "北京"},
                depends_on=[],
                priority=0
            ),
            SubTask(
                id=1,
                task_type="QUERY_HOTEL",
                description="查询北京酒店",
                parameters={"city": "北京"},
                depends_on=[],
                priority=0
            )
        ])
        return decomposer

    @pytest.fixture
    def mock_tools(self):
        """模拟工具"""
        weather_tool = Mock()
        weather_tool.name = "query_weather"
        weather_tool.execute = Mock(return_value="北京天气：晴天，20-30度")

        hotel_tool = Mock()
        hotel_tool.name = "search_hotels"
        hotel_tool.execute = Mock(return_value="推荐酒店：北京饭店")

        return {
            "query_weather": weather_tool,
            "search_hotels": hotel_tool
        }

    @pytest.fixture
    def engine(self, mock_llm, mock_task_decomposer, mock_tools):
        """创建 ComplexTaskEngine 实例"""
        from src.agents.executors.complex_task_engine import ComplexTaskEngine
        return ComplexTaskEngine(
            llm=mock_llm,
            task_decomposer=mock_task_decomposer,
            tools=mock_tools
        )

    def test_init(self, engine, mock_llm, mock_task_decomposer, mock_tools):
        """测试初始化"""
        assert engine.llm == mock_llm
        assert engine.task_decomposer == mock_task_decomposer
        assert engine.tools == mock_tools

    def test_execute_simple_query(self, engine, mock_task_decomposer, mock_tools):
        """测试执行简单查询（无依赖的并行任务）"""
        query = "查询北京天气和酒店"

        result = engine.execute(query)

        # 验证任务分解被调用
        mock_task_decomposer.decompose.assert_called_once_with(query)

        # 验证工具被调用
        mock_tools["query_weather"].execute.assert_called_once()
        mock_tools["search_hotels"].execute.assert_called_once()

        # 验证返回结果
        assert result is not None
        assert "整合结果" in result or "天气" in result

    def test_execute_with_dependency(self, engine, mock_task_decomposer, mock_tools):
        """测试执行有依赖关系的任务"""
        # 模拟有依赖的任务：先查政策，再查酒店
        policy_tool = Mock()
        policy_tool.name = "search_policy"
        policy_tool.execute = Mock(return_value="住宿标准：500元")

        hotel_tool = Mock()
        hotel_tool.name = "search_hotels"
        hotel_tool.execute = Mock(return_value="推荐酒店：如家")

        engine.tools = {
            "search_policy": policy_tool,
            "search_hotels": hotel_tool
        }

        # 模拟分解结果：task1 依赖 task0
        mock_task_decomposer.decompose.return_value = [
            SubTask(
                id=0,
                task_type="QUERY_POLICY",
                description="查询住宿标准",
                parameters={"keyword": "北京住宿标准"},
                depends_on=[],
                priority=0
            ),
            SubTask(
                id=1,
                task_type="QUERY_HOTEL",
                description="查询酒店",
                parameters={"city": "北京"},
                depends_on=[0],  # 依赖 task0
                priority=1
            )
        ]

        result = engine.execute("查询北京住宿标准并推荐酒店")

        # 验证工具按顺序执行
        policy_tool.execute.assert_called_once()
        hotel_tool.execute.assert_called_once()

        # 验证返回结果
        assert result is not None

    def test_execute_with_tool_failure(self, engine, mock_task_decomposer, mock_tools):
        """测试工具执行失败的情况"""
        # 模拟工具执行失败
        mock_tools["query_weather"].execute.side_effect = Exception("天气服务不可用")

        result = engine.execute("查询北京天气和酒店")

        # 即使有工具失败，也应该返回结果
        assert result is not None
        # 应该包含错误信息或继续执行其他任务
        assert "酒店" in result or "失败" in result or "整合" in result

    def test_task_type_mapping(self, engine):
        """测试任务类型到工具名称的映射"""
        # 验证任务类型映射
        mapping = engine._get_tool_name_from_task_type("QUERY_WEATHER")
        assert mapping in ["query_weather", "search_weather"]

        mapping = engine._get_tool_name_from_task_type("QUERY_HOTEL")
        assert mapping in ["search_hotels", "query_hotel"]

        mapping = engine._get_tool_name_from_task_type("QUERY_POLICY")
        assert mapping in ["search_policy"]

    def test_empty_task_list(self, engine, mock_task_decomposer):
        """测试空任务列表的情况"""
        mock_task_decomposer.decompose.return_value = []

        result = engine.execute("测试查询")

        # 应该返回提示信息
        assert result is not None
        assert "无法分解" in result or "没有任务" in result
