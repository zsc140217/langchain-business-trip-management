import os, py_compile, sys
P = r"src/mcp/trip_tools_server.py"
with open(P, "r", encoding="utf-8") as f:
    data = f.read()

# Move env loading BEFORE the src import, simpler parsing
old = 'from src.tools.qweather_client import get_qweather_client\n_env_path = os.path.join(_ROOT, ".env")\nif os.path.exists(_env_path):\n    for _line in open(_env_path, encoding="utf-8"):\n        parts = _line.strip().split("=", 1)\n        if len(parts) == 2 and parts[0].isupper():\n            os.environ.setdefault(parts[0], parts[1])'

new = '_env_path = os.path.join(_ROOT, ".env")\nif os.path.exists(_env_path):\n    for _line in open(_env_path, encoding="utf-8"):\n        _line = _line.strip()\n        if _line.startswith("#") or not _line:\n            continue\n        if "=" in _line:\n            k, v = _line.split("=", 1)\n            if k.isupper():\n                os.environ.setdefault(k, v)\nfrom src.tools.qweather_client import get_qweather_client'

data = data.replace(old, new)
with open(P, "w", encoding="utf-8") as f:
    f.write(data)
py_compile.compile(P, doraise=True)
print("Fixed env loading order")

# Test
sys.path.insert(0, ".")
from src.tools.mcp_client import MCPClientManager
client = MCPClientManager()
client.start()
r1 = client.call_tool("query_weather", {"city": "\u5317\u4eac"})
print("Beijing weather:", r1)
r2 = client.call_tool("query_weather", {"city": "\u5185\u6c5f"})
print("Neijiang weather:", r2)
client.stop()
