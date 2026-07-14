import sys, os
P = r"src/mcp/trip_tools_server.py"
with open(P, "r", encoding="utf-8") as f:
    data = f.read()
# Add debug right before the qweather call in query_weather
old = 'def query_weather(city):\n  """查询指定城市的当前天气情况。"""\n  client = get_qweather_client()\n  if not client.is_ready:'
new = 'def query_weather(city):\n  """查询指定城市的当前天气情况。"""\n  from dotenv import load_dotenv; load_dotenv(os.path.join(_ROOT, ".env"))\n  import os; print(f"[MCP_DEBUG] is_ready={get_qweather_client().is_ready} api_key={bool(os.getenv(\"QWEATHER_API_KEY\"))} host={os.getenv(\"QWEATHER_API_HOST\")}", file=sys.stderr, flush=True)\n  client = get_qweather_client()\n  if not client.is_ready:'
data = data.replace(old, new)
with open(P, "w", encoding="utf-8") as f:
    f.write(data)
import py_compile
py_compile.compile(P, doraise=True)
print("Added debug prints")
