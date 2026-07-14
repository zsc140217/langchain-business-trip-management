"""Weather tool adapter - calls MCP server instead of Module 3 mock."""
from src.tools.base_tool import BaseTool
from src.tools.mcp_client import get_mcp_client
from typing import Optional
import logging
logger = logging.getLogger(__name__)

class WeatherTool(BaseTool):
    """Weather query tool that calls MCP server."""
    name: str = "query_weather"
    description: str = "查询指定城市的当前天气情况。"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 1800

    def _run(self, city: str) -> str:
        try:
            client = get_mcp_client()
            return client.call_tool("query_weather", {"city": city})
        except Exception as e:
            logger.error(f"WeatherTool failed: {e}")
            return f"抱歉，查询{city}天气时出错，请稍后重试。"

def get_weather_tool() -> WeatherTool:
    return WeatherTool()
