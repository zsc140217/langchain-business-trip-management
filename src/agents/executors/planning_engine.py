"""
PlanningEngine - 规划执行引擎

职责：
1. 解析 Planning Skill 文档
2. 按步骤执行差旅规划
3. 并行查询差旅标准
4. 生成完整的差旅方案

对应架构文档：
- 通道类型：规划通道（PLANNING）
- 适用场景：需要完整差旅方案
- 示例："帮我安排下周去深圳出差"
"""
from typing import Dict, Optional, Any
from langchain_core.messages import HumanMessage
import logging
import re

logger = logging.getLogger(__name__)


class PlanningEngine:
    """
    规划执行引擎

    基于 Planning Skill 文档，按步骤执行差旅规划：
    1. 提取信息
    2. 并行查询差旅标准
    3. 查询天气、酒店、航班
    4. 查询用户偏好
    5. 计算费用
    6. 生成方案
    """

    def __init__(
        self,
        llm,
        tools: Dict,
        memory_service=None
    ):
        """
        初始化规划引擎

        Args:
            llm: 语言模型
            tools: 工具字典 {tool_name: tool}
            memory_service: 记忆服务（可选）
        """
        self.llm = llm
        self.tools = tools
        self.memory_service = memory_service

    def execute(
        self,
        query: str,
        user_id: str,
        conversation_id: str
    ) -> str:
        """
        执行差旅规划

        Args:
            query: 用户查询
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            差旅方案
        """
        logger.info(f"[PlanningEngine] 开始规划: {query}")

        try:
            # Step 1: 提取规划信息
            planning_info = self._extract_planning_info(query)

            if not planning_info.get("city"):
                return "抱歉，请告诉我您要去哪个城市出差？"

            city = planning_info["city"]
            days = planning_info.get("days", 3)

            logger.info(f"[PlanningEngine] 规划信息: 目的地={city}, 天数={days}")

            # Step 2: 并行查询差旅标准
            policy_results = self._query_policies_parallel(city)

            # Step 3: 查询天气
            weather_result = self._query_weather(city)

            # Step 4: 推荐酒店
            hotel_result = self._query_hotels(city)

            # Step 5: 查询用户偏好（从记忆）
            user_preferences = self._query_user_preferences(user_id, conversation_id)

            # Step 6: 计算费用
            estimated_cost = self._calculate_cost(policy_results, days)

            # Step 7: 生成方案
            travel_plan = self._generate_travel_plan(
                planning_info=planning_info,
                policy_results=policy_results,
                weather=weather_result,
                hotel=hotel_result,
                user_preferences=user_preferences,
                estimated_cost=estimated_cost
            )

            logger.info("[PlanningEngine] 规划完成")
            return travel_plan

        except Exception as e:
            logger.error(f"[PlanningEngine] 执行失败: {e}", exc_info=True)
            return f"抱歉，生成差旅方案时出现错误：{str(e)}"

    def _extract_planning_info(self, query: str) -> Dict[str, Any]:
        """
        从查询中提取规划信息

        Args:
            query: 用户查询

        Returns:
            规划信息字典
        """
        info = {}

        # 提取城市（简单规则匹配）
        cities = ["北京", "上海", "深圳", "广州", "杭州", "成都", "西安", "武汉"]
        for city in cities:
            if city in query:
                info["city"] = city
                break

        # 提取天数
        days_match = re.search(r'(\d+)天', query)
        if days_match:
            info["days"] = int(days_match.group(1))

        # 提取日期（简单处理）
        if "下周" in query:
            info["time_desc"] = "下周"
        elif "本周" in query:
            info["time_desc"] = "本周"

        return info

    def _query_policies_parallel(self, city: str) -> Dict[str, str]:
        """
        并行查询差旅标准

        Args:
            city: 目的地城市

        Returns:
            政策结果字典
        """
        results = {}

        if "search_policy" not in self.tools:
            logger.warning("[PlanningEngine] search_policy 工具不可用")
            return results

        policy_tool = self.tools["search_policy"]

        try:
            # 查询住宿标准
            accommodation = policy_tool.execute(query=f"{city}住宿标准")
            results["accommodation"] = accommodation

            # 查询伙食补助
            meal = policy_tool.execute(query="伙食补助标准")
            results["meal"] = meal

            # 查询交通标准
            transport = policy_tool.execute(query=f"{city}交通标准")
            results["transport"] = transport

        except Exception as e:
            logger.error(f"[PlanningEngine] 查询政策失败: {e}")

        return results

    def _query_weather(self, city: str) -> str:
        """查询天气"""
        if "query_weather" not in self.tools:
            return "天气信息暂时不可用"

        try:
            weather_tool = self.tools["query_weather"]
            return weather_tool.execute(city=city)
        except Exception as e:
            logger.error(f"[PlanningEngine] 查询天气失败: {e}")
            return "天气信息查询失败"

    def _query_hotels(self, city: str) -> str:
        """查询酒店"""
        if "search_hotels" not in self.tools:
            return "酒店信息暂时不可用"

        try:
            hotel_tool = self.tools["search_hotels"]
            return hotel_tool.execute(city=city)
        except Exception as e:
            logger.error(f"[PlanningEngine] 查询酒店失败: {e}")
            return "酒店信息查询失败"

    def _query_user_preferences(self, user_id: str, conversation_id: str) -> str:
        """查询用户偏好"""
        if not self.memory_service:
            return ""

        try:
            preferences = self.memory_service.build_enhanced_prompt(
                user_id=user_id,
                conversation_id=conversation_id
            )
            return preferences
        except Exception as e:
            logger.error(f"[PlanningEngine] 查询用户偏好失败: {e}")
            return ""

    def _calculate_cost(self, policy_results: Dict[str, str], days: int) -> Dict[str, Any]:
        """计算费用"""
        cost = {"accommodation": 0, "meal": 0, "transport": 0, "total": 0}

        try:
            # 从政策结果中提取金额（简单正则）
            accommodation_text = policy_results.get("accommodation", "")
            accommodation_match = re.search(r'(\d+)元', accommodation_text)
            if accommodation_match:
                cost["accommodation"] = int(accommodation_match.group(1)) * days

            meal_text = policy_results.get("meal", "")
            meal_match = re.search(r'(\d+)元', meal_text)
            if meal_match:
                cost["meal"] = int(meal_match.group(1)) * days

            cost["transport"] = 1000
            cost["total"] = cost["accommodation"] + cost["meal"] + cost["transport"]

        except Exception as e:
            logger.error(f"[PlanningEngine] 计算费用失败: {e}")

        return cost

    def _generate_travel_plan(
        self,
        planning_info: Dict,
        policy_results: Dict,
        weather: str,
        hotel: str,
        user_preferences: str,
        estimated_cost: Dict
    ) -> str:
        """生成差旅方案"""
        city = planning_info.get("city", "")
        days = planning_info.get("days", 3)

        prompt = f"""请根据以下信息生成一份完整的差旅方案：

目的地：{city}
天数：{days}天

差旅标准：
{policy_results.get('accommodation', '住宿标准未查询')}
{policy_results.get('meal', '伙食标准未查询')}
{policy_results.get('transport', '交通标准未查询')}

天气信息：{weather}
酒店推荐：{hotel}
用户偏好：{user_preferences if user_preferences else '无'}

费用预算：
- 住宿：¥{estimated_cost['accommodation']}
- 伙食：¥{estimated_cost['meal']}
- 交通：¥{estimated_cost['transport']}
- 总计：¥{estimated_cost['total']}

请生成一份专业、清晰的差旅方案，包含时间安排、住宿建议、费用预算和天气提醒。
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content

        except Exception as e:
            logger.error(f"[PlanningEngine] LLM 生成方案失败: {e}")
            return f"""【差旅方案】目的地：{city}

📅 **时间安排** - 出差天数：{days}天
🏨 **住宿安排** - {policy_results.get('accommodation', '住宿标准未查询')}
🍽️ **伙食补助** - {policy_results.get('meal', '伙食标准未查询')}
✈️ **交通安排** - {policy_results.get('transport', '交通标准未查询')}
💰 **费用预算** - 总计：¥{estimated_cost['total']}
🌤️ **天气提醒** - {weather}
"""
