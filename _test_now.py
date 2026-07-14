import os, sys
os.environ["QWEATHER_API_KEY"] = "21fbbbf3b8fb4932b68ca51544dfbb8b"
os.environ["QWEATHER_API_HOST"] = "mr487tqjdj.re.qweatherapi.com"
sys.path.insert(0, ".")
from src.tools.mcp_client import MCPClientManager
client = MCPClientManager()
client.start()
r1 = client.call_tool("query_weather", {"city": "\u5317\u4eac"})
print("Beijing:", r1)
r2 = client.call_tool("query_weather", {"city": "\u5185\u6c5f"})
print("Neijiang:", r2)
r3 = client.call_tool("get_weather_forecast", {"city": "\u5317\u4eac", "days": 3})
print("Forecast:", r3)
client.stop()
