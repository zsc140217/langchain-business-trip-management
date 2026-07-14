"""
PlanningEngine 测试

测试 Planning 执行引擎的功能：
1. Skill 文档解析
2. 步骤执行
3. 并行任务处理
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestPlanningEngine:
    """PlanningEngine 测试类"""

    @pytest.fixture
    def mock_llm(self):
        """模拟 LLM"""
        llm = Mock()
        llm.invoke = Mock(return_value=Mock(content="生成的差旅方案"))
        return llm

    @pytest.fixture
    def mock_tools(self):
        """模拟工具"""
        return {
            "search_policy": Mock(execute=Mock(return_value="住宿标准：500元")),
            "query_weather": Mock(execute=Mock(return_value="北京：晴天，20-30度")),
            "search_hotels": Mock(execute=Mock(return_value="推荐：北京饭店")),
            "search_flights": Mock(execute=Mock(return_value="北京-深圳：CA1234")),
        }

    @pytest.fixture
    def mock_memory_service(self):
        """模拟记忆服务"""
        memory = Mock()
        memory.build_enhanced_prompt = Mock(return_value="用户偏好：经济型酒店")
        return memory

    @pytest.fixture
    def engine(self, mock_llm, mock_tools, mock_memory_service):
        """创建 PlanningEngine 实例"""
        from src.agents.executors.planning_engine import PlanningEngine
        return PlanningEngine(
            llm=mock_llm,
            tools=mock_tools,
            memory_service=mock_memory_service
        )

    def test_init(self, engine, mock_llm, mock_tools, mock_memory_service):
        """测试初始化"""
        assert engine.llm == mock_llm
        assert engine.tools == mock_tools
        assert engine.memory_service == mock_memory_service

    def test_execute_trip_planning(self, engine, mock_tools):
        """测试执行差旅规划"""
        query = "帮我安排下周去深圳出差3天"
        user_id = "test_user"
        conversation_id = "test_conv"

        result = engine.execute(query, user_id, conversation_id)

        # 验证返回结果
        assert result is not None
        assert isinstance(result, str)

        # 验证调用了政策查询工具
        assert mock_tools["search_policy"].execute.called

    def test_extract_planning_info(self, engine):
        """测试提取规划信息"""
        query = "帮我安排下周一到周三去北京出差"

        info = engine._extract_planning_info(query)

        # 验证提取的信息
        assert info is not None
        assert "city" in info or "destination" in info

    def test_parallel_policy_query(self, engine, mock_tools):
        """测试并行查询差旅标准"""
        city = "北京"

        results = engine._query_policies_parallel(city)

        # 验证并行查询结果
        assert results is not None
        assert isinstance(results, dict)

        # 验证调用了多个政策查询
        call_count = mock_tools["search_policy"].execute.call_count
        assert call_count >= 1

    def test_generate_travel_plan(self, engine, mock_llm):
        """测试生成差旅方案"""
        planning_info = {
            "city": "深圳",
            "days": 3,
            "start_date": "2024-07-15"
        }

        policy_results = {
            "accommodation": "住宿标准：600元",
            "meal": "伙食补助：100元",
            "transport": "交通标准：经济舱"
        }

        weather = "深圳：晴天，25-30度"
        hotel = "推荐：深圳酒店"
        user_preferences = "经济型酒店"
        estimated_cost = {"accommodation": 1800, "meal": 300, "transport": 1000, "total": 3100}

        result = engine._generate_travel_plan(
            planning_info, policy_results, weather, hotel, user_preferences, estimated_cost
        )

        # 验证生成方案
        assert result is not None
        assert "深圳" in result or "差旅" in result

        # 验证调用了 LLM
        mock_llm.invoke.assert_called()

    def test_skill_document_exists(self):
        """测试 Planning Skill 文档存在"""
        skill_path = Path("skills/trip_planning_skill.md")
        assert skill_path.exists(), "Planning Skill 文档不存在"

        # 验证文档内容
        content = skill_path.read_text(encoding="utf-8")
        assert "差旅规划" in content
        assert "Step" in content

    def test_execute_with_missing_info(self, engine, mock_llm):
        """测试缺少关键信息时的处理"""
        # 查询中缺少目的地
        query = "帮我安排出差"

        result = engine.execute(query, "user1", "conv1")

        # 应该返回提示或询问用户
        assert result is not None

    def test_tool_execution_failure(self, engine, mock_tools):
        """测试工具执行失败的处理"""
        # 模拟工具失败
        mock_tools["search_policy"].execute.side_effect = Exception("服务不可用")

        query = "帮我安排去北京出差"

        result = engine.execute(query, "user1", "conv1")

        # 应该返回结果（可能降级）
        assert result is not None

    def test_memory_integration(self, engine, mock_memory_service):
        """测试记忆集成"""
        query = "帮我安排去深圳出差"
        user_id = "test_user"
        conversation_id = "test_conv"

        result = engine.execute(query, user_id, conversation_id)

        # 验证调用了记忆服务
        mock_memory_service.build_enhanced_prompt.assert_called()
