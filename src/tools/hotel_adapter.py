"""Hotel tool adapter - calls MCP server instead of Module 3 mock."""
from src.tools.base_tool import BaseTool
from src.tools.mcp_client import get_mcp_client
from typing import Optional
from pydantic import BaseModel, Field
import logging
logger = logging.getLogger(__name__)

class HotelSearchInput(BaseModel):
    """Input schema for hotel search."""
    city: str = Field(description="城市名称，如'北京'、'上海'")
    min_price: Optional[int] = Field(default=None, description="最低价格（元/晚）")
    max_price: Optional[int] = Field(default=None, description="最高价格（元/晚）")
    min_star: Optional[int] = Field(default=None, description="最低星级（1-5星）")

class HotelTool(BaseTool):
    """Hotel search tool that calls MCP server."""
    name: str = "search_hotels"
    description: str = "搜索指定城市的酒店，支持按价格和星级筛选。输入城市名称即可。"
    args_schema: type[BaseModel] = HotelSearchInput
    cache_enabled: bool = True
    cache_ttl_seconds: int = 600

    def _run(self, city: str, min_price: Optional[int] = None,
             max_price: Optional[int] = None,
             min_star: Optional[int] = None) -> str:
        try:
            client = get_mcp_client()
            return client.call_tool("search_hotels", {
                "city": city,
                "min_price": min_price,
                "max_price": max_price,
                "min_star": min_star
            })
        except Exception as e:
            logger.error(f"HotelTool failed: {e}")
            return f"抱歉，查询{city}酒店时出错，请稍后重试。"

def get_hotel_tool() -> HotelTool:
    return HotelTool()
