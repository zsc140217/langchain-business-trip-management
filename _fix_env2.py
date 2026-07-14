import sys, os
P = r"src/mcp/trip_tools_server.py"
with open(P, "r") as f:
    data = f.read()

# Restore the original clean function by simply replacing the whole file
# from the generator. But actually, let me take a simpler approach:
# replace the server's env loading with a direct file read

old = """from dotenv import load_dotenv
load_dotenv(os.path.join(_ROOT, ".env"))
from src.tools.qweather_client import get_qweather_client"""

new = """from src.tools.qweather_client import get_qweather_client
# Load .env manually
import re as _re
_env_path = os.path.join(_ROOT, ".env")
if os.path.exists(_env_path):
    for _line in open(_env_path, encoding="utf-8"):
        _m = _re.match(r"^\s*([A-Z_]+)=(.+)$", _line.strip())
        if _m: os.environ.setdefault(_m.group(1), _m.group(2))"""

data = data.replace(old, new)

with open(P, "w", encoding="utf-8") as f:
    f.write(data)

import py_compile
py_compile.compile(P, doraise=True)
print("Restored weather function and fixed env loading")
