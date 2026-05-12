"""
天气查询Skill
处理天气相关的查询

对应Spring AI的：
src/main/java/com/jblmj/aiagent/skill/business/WeatherQuerySkill.java
"""
from src.skills.base import Skill
from src.tools.weather import query_weather
from typing import List
import re


class WeatherQuerySkill(Skill):
    """
    天气查询Skill

    功能：
    1. 单城市天气查询
    2. 多城市天气对比

    设计思路：
    - 通过关键词快速判断是否为天气查询
    - 提取城市名称
    - 调用天气工具
    - 格式化返回结果
    """

    def __init__(self):
        self._cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安", "南京", "苏州"]

    @property
    def name(self) -> str:
        return "weather_query"

    @property
    def description(self) -> str:
        return "查询天气信息，支持单城市查询和多城市对比"

    @property
    def keywords(self) -> List[str]:
        return ["天气", "温度", "下雨", "带伞", "气温", "晴天", "阴天"]

    @property
    def priority(self) -> int:
        return 50  # 高优先级

    def can_handle(self, query: str) -> bool:
        """
        判断是否为天气查询

        Args:
            query: 用户查询

        Returns:
            是否能处理
        """
        return any(keyword in query for keyword in self.keywords)

    def execute(self, query: str, chat_id: str) -> str:
        """
        执行天气查询

        流程：
        1. 提取城市名称
        2. 判断是单城市还是多城市
        3. 调用天气工具
        4. 格式化返回

        Args:
            query: 用户查询
            chat_id: 会话ID

        Returns:
            天气信息
        """
        print(f"\n{'='*60}")
        print(f"WeatherQuerySkill执行")
        print(f"查询：{query}")
        print(f"{'='*60}")

        # 1. 提取城市
        cities = self._extract_cities(query)

        if not cities:
            return "请提供城市名称，例如：北京天气怎么样"

        # 2. 判断查询类型
        if len(cities) == 1:
            # 单城市查询
            return self._handle_single_city(cities[0])
        else:
            # 多城市对比
            return self._handle_multi_city(cities)

    def _extract_cities(self, query: str) -> List[str]:
        """
        从查询中提取城市名称

        Args:
            query: 用户查询

        Returns:
            城市列表
        """
        found_cities = []
        for city in self._cities:
            if city in query:
                found_cities.append(city)

        print(f"提取到城市：{found_cities}")
        return found_cities

    def _handle_single_city(self, city: str) -> str:
        """
        处理单城市查询

        Args:
            city: 城市名称

        Returns:
            天气信息
        """
        print(f"单城市查询：{city}")

        try:
            result = query_weather.invoke({"city": city})
            return result
        except Exception as e:
            return f"查询{city}天气失败：{str(e)}"

    def _handle_multi_city(self, cities: List[str]) -> str:
        """
        处理多城市对比

        Args:
            cities: 城市列表

        Returns:
            对比结果
        """
        print(f"多城市对比：{cities}")

        results = []
        for city in cities[:3]:  # 最多对比3个城市
            try:
                weather = query_weather.invoke({"city": city})
                results.append(weather)
            except Exception as e:
                results.append(f"{city}：查询失败")

        return "天气对比：\n" + "\n".join(results)


class TravelPlanningSkill(Skill):
    """
    差旅规划Skill

    功能：
    1. 行程规划
    2. 差旅建议

    设计思路：
    - 识别规划类查询
    - 调用RAG查询差旅政策
    - 调用天气工具
    - 综合生成建议
    """

    def __init__(self, rag_chain=None):
        self.rag_chain = rag_chain

    @property
    def name(self) -> str:
        return "travel_planning"

    @property
    def description(self) -> str:
        return "差旅行程规划和建议"

    @property
    def keywords(self) -> List[str]:
        return ["规划", "行程", "安排", "计划", "准备", "出差"]

    @property
    def priority(self) -> int:
        return 60  # 中等优先级

    def can_handle(self, query: str) -> bool:
        """判断是否为规划类查询"""
        return any(keyword in query for keyword in self.keywords)

    def execute(self, query: str, chat_id: str) -> str:
        """
        执行差旅规划

        Args:
            query: 用户查询
            chat_id: 会话ID

        Returns:
            规划建议
        """
        print(f"\n{'='*60}")
        print(f"TravelPlanningSkill执行")
        print(f"查询：{query}")
        print(f"{'='*60}")

        if self.rag_chain:
            # 查询差旅政策
            result = self.rag_chain.invoke({"query": query})
            return result.get("result", "未找到相关政策")
        else:
            return "差旅规划功能需要配置RAG系统"


# 测试代码
if __name__ == "__main__":
    """
    测试天气查询Skill
    """
    print("测试WeatherQuerySkill...\n")

    from src.skills.base import SkillRegistry

    # 创建注册中心
    registry = SkillRegistry()

    # 注册天气Skill
    weather_skill = WeatherQuerySkill()
    registry.register(weather_skill)

    # 注册规划Skill
    planning_skill = TravelPlanningSkill()
    registry.register(planning_skill)

    # 测试查询
    test_queries = [
        "北京天气怎么样",
        "上海和广州天气对比",
        "帮我规划去杭州的行程"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"测试查询：{query}")
        print(f"{'='*60}")

        skill = registry.select_skill(query)
        if skill:
            result = skill.execute(query, "test123")
            print(f"\n结果：{result}")
        else:
            print("没有Skill能处理该查询")

    print("\n✅ WeatherQuerySkill测试完成！")
