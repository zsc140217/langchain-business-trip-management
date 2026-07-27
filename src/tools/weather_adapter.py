"""Weather tool adapter - calls MCP server instead of Module 3 mock."""
from src.tools.base_tool import BaseTool
from src.tools.mcp_client import get_mcp_client
from typing import Optional
from pydantic import BaseModel, Field
import logging
logger = logging.getLogger(__name__)

class WeatherQueryInput(BaseModel):
    """Input schema for weather query."""
    city: str = Field(description="城市名称，如'北京'、'上海'")

class WeatherTool(BaseTool):
    """Weather query tool that calls MCP server."""
    name: str = "query_weather"
    description: str = "查询指定城市的当前天气情况。输入城市名称即可。"
    args_schema: type[BaseModel] = WeatherQueryInput
    cache_enabled: bool = True
    cache_ttl_seconds: int = 1800

    def _run(self, city: str) -> str:
        try:
            logger.info(f"[WeatherTool] 开始查询城市: {city}")
            client = get_mcp_client()
            logger.info(f"[WeatherTool] MCP客户端已获取")
            result = client.call_tool("query_weather", {"city": city})
            logger.info(f"[WeatherTool] 查询成功，结果长度: {len(str(result))}")
            return result
        except Exception as e:
            logger.error(f"WeatherTool failed: {e}", exc_info=True)
            return f"抱歉，查询{city}天气时出错，请稍后重试。"

def get_weather_tool() -> WeatherTool:
    return WeatherTool()
