"""MCP client manager - manages connection to the trip tools MCP server."""
import os, sys, asyncio, contextlib
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_SERVER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    "..", "mcp", "trip_tools_server.py")

class MCPClientManager:
    """Manages persistent stdio connection to MCP server."""

    def __init__(self, server_script=None):
        self._script = server_script or _SERVER
        self._params = StdioServerParameters(
            command=sys.executable, args=[self._script],
            env=os.environ.copy())
        self._loop = None
        self._session = None
        self._stack = None

    def start(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect())

    async def _connect(self):
        self._stack = contextlib.AsyncExitStack()
        r, w = await self._stack.enter_async_context(
            stdio_client(self._params))
        self._session = await self._stack.enter_async_context(
            ClientSession(r, w))
        await self._session.initialize()

    def call_tool(self, tool_name, arguments):
        if not self._session:
            raise RuntimeError("MCPClientManager not started")
        return self._loop.run_until_complete(
            self._call(tool_name, arguments))

    async def _call(self, tool_name, arguments):
        result = await self._session.call_tool(tool_name, arguments)
        if hasattr(result, "content") and result.content:
            return result.content[0].text
        return str(result)

    def stop(self):
        if self._stack:
            try:
                self._loop.run_until_complete(self._stack.aclose())
            except RuntimeError:
                pass  # cancel scope mismatch expected with anyio
        if self._loop:
            self._loop.close()
        self._session = None
        self._connected = False

_client = None

def get_mcp_client():
    global _client
    if _client is None:
        _client = MCPClientManager()
        _client.start()
    return _client

def stop_mcp_client():
    global _client
    if _client:
        _client.stop()
        _client = None
