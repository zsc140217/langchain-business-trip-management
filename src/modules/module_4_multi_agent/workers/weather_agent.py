"""
Weather Query Worker Agent
Specialized agent for querying weather information

Responsibilities:
- Query real-time weather data
- Extract city information from queries
- Provide weather-based travel recommendations

Reuses:
- BaseAgent for common functionality
- WeatherTool for weather queries
"""
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from tools.weather_tool import WeatherTool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
import logging
import re

logger = logging.getLogger(__name__)


class WeatherWorkerAgent(BaseAgent):
    """
    Weather query worker agent

    Queries weather information using WeatherTool.
    Extracts city names and provides weather-based recommendations.

    Example:
        agent = WeatherWorkerAgent(llm, weather_tool)
        result = agent.execute({
            "query": "北京天气怎么样",
            "context": {}
        })
    """

    def __init__(
        self,
        llm: BaseChatModel,
        weather_tool: Optional[WeatherTool] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize weather worker agent

        Args:
            llm: Language model instance
            weather_tool: Weather query tool (creates new if None)
            config: Agent configuration
        """
        # Create weather tool if not provided
        if weather_tool is None:
            weather_tool = WeatherTool()

        super().__init__(
            name="WeatherWorkerAgent",
            llm=llm,
            tools=[weather_tool],
            config=config or {}
        )

        self.weather_tool = weather_tool
        logger.info("WeatherWorkerAgent initialized")

    @traceable(name="weather_worker_execute")
    def execute(self, task: Dict[str, Any]) -> str:
        """
        Execute weather query task

        Args:
            task: Task dictionary with:
                - query: User query
                - context: Additional context

        Returns:
            Weather query result with recommendations
        """
        query = task.get("query", "")
        context = task.get("context", {})

        logger.info(f"WeatherWorker: Processing query: {query}")

        try:
            # Extract cities from query
            cities = self._extract_cities(query)

            if not cities:
                logger.warning("No cities found in query")
                return "未能识别查询中的城市，请明确指定城市名称（如：北京、上海等）"

            # Query weather for each city
            weather_results = []
            for city in cities:
                weather_data = self._query_weather(city)
                weather_results.append(weather_data)

            # Format response
            result = self._format_response(cities, weather_results)

            logger.info("WeatherWorker: Query completed successfully")
            return result

        except Exception as e:
            logger.error(f"WeatherWorker failed: {e}")
            return f"天气查询失败：{str(e)}"

    def _extract_cities(self, query: str) -> list:
        """
        Extract city names from query

        Args:
            query: User query

        Returns:
            List of city names
        """
        # Common Chinese cities
        city_list = [
            "北京", "上海", "广州", "深圳", "杭州", "成都",
            "重庆", "武汉", "西安", "南京", "天津", "苏州",
            "长沙", "郑州", "济南", "青岛", "大连", "厦门"
        ]

        # Find all cities mentioned in query
        found_cities = [city for city in city_list if city in query]

        logger.debug(f"Extracted cities: {found_cities}")
        return found_cities

    def _query_weather(self, city: str) -> str:
        """
        Query weather for a city

        Args:
            city: City name

        Returns:
            Weather information
        """
        logger.debug(f"Querying weather for: {city}")

        try:
            # Use weather tool
            result = self.weather_tool.invoke({"city": city})
            return result

        except Exception as e:
            logger.error(f"Weather query failed for {city}: {e}")
            return f"{city}：天气查询失败"

    def _format_response(self, cities: list, weather_results: list) -> str:
        """
        Format weather results with recommendations

        Args:
            cities: List of queried cities
            weather_results: List of weather results

        Returns:
            Formatted response with recommendations
        """
        if len(cities) == 1:
            # Single city
            weather = weather_results[0]
            recommendation = self._get_recommendation(weather)

            return f"""**天气查询结果**

{weather}

**出行建议**
{recommendation}"""

        else:
            # Multiple cities (comparison)
            formatted_results = []
            for city, weather in zip(cities, weather_results):
                formatted_results.append(f"• {weather}")

            weather_str = "\n".join(formatted_results)

            return f"""**天气对比结果**

{weather_str}

**出行建议**
请根据天气情况选择合适的出行时间和准备相应物品。"""

    def _get_recommendation(self, weather: str) -> str:
        """
        Generate travel recommendation based on weather

        Args:
            weather: Weather information string

        Returns:
            Recommendation text
        """
        weather_lower = weather.lower()

        if "雨" in weather or "rain" in weather_lower:
            return "有降雨，建议携带雨具，注意交通延误风险。"
        elif "雪" in weather or "snow" in weather_lower:
            return "有降雪，建议提前出行，注意保暖和交通安全。"
        elif "晴" in weather or "sunny" in weather_lower:
            return "天气晴好，适合出行，注意防晒。"
        elif "阴" in weather or "cloudy" in weather_lower or "多云" in weather:
            return "天气较好，适合出行。"
        else:
            return "请根据天气情况做好出行准备。"


# ============================================================================
# Test Code
# ============================================================================

if __name__ == "__main__":
    """
    Test WeatherWorkerAgent
    """
    print("Testing WeatherWorkerAgent...\n")

    from models.llm import get_llm

    try:
        llm = get_llm(temperature=0.3)
        agent = WeatherWorkerAgent(llm)

        # Test queries
        test_queries = [
            "北京天气怎么样",
            "上海和杭州天气对比",
            "深圳明天适合出差吗",
            "查询广州天气"
        ]

        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"{'='*60}")

            result = agent.execute({
                "query": query,
                "context": {"user_id": "test_user"}
            })

            print(f"Result:\n{result}")

        print("\n✅ WeatherWorkerAgent test completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
