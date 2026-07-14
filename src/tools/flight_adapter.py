"""Flight tool adapter - calls MCP server instead of Module 3 mock."""
from src.tools.base_tool import BaseTool
from src.tools.mcp_client import get_mcp_client
from typing import Optional
import logging
logger = logging.getLogger(__name__)

class FlightTool(BaseTool):
    """Flight search tool that calls MCP server."""
    name: str = "search_flights"
    description: str = "搜索指定日期从出发城市到目的地城市的所有可用航班。"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 900

    def _run(self, departure_city: str, arrival_city: str,
             date: Optional[str] = None) -> str:
        try:
            client = get_mcp_client()
            return client.call_tool("search_flights", {
                "departure_city": departure_city,
                "arrival_city": arrival_city,
                "date": date
            })
        except Exception as e:
            logger.error(f"FlightTool failed: {e}")
            return f"抱歉，查询{departure_city}到{arrival_city}航班时出错。"

def get_flight_tool() -> FlightTool:
    return FlightTool()
