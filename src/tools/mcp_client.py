"""MCP client manager - manages connection to the trip tools MCP server."""
import os, sys, asyncio, contextlib, threading
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

_SERVER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    "..", "mcp", "trip_tools_server.py")

class MCPClientManager:
    """Manages persistent stdio connection to MCP server in a dedicated thread."""

    def __init__(self, server_script=None):
        self._script = server_script or _SERVER
        self._params = StdioServerParameters(
            command=sys.executable, args=[self._script],
            env=os.environ.copy())
        self._loop = None
        self._session = None
        self._stack = None
        self._thread = None
        self._started = False

    def start(self):
        """Start MCP client in a dedicated background thread."""
        if self._started:
            return

        self._started = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        # Wait for connection to be ready
        import time
        for _ in range(50):  # 5 seconds max
            if self._session:
                logger.info("[MCPClient] Connected successfully")
                return
            time.sleep(0.1)

        logger.warning("[MCPClient] Connection timeout, will retry on first call")

    def _run_loop(self):
        """Run event loop in dedicated thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect())
            # Keep loop running
            self._loop.run_forever()
        except Exception as e:
            logger.error(f"[MCPClient] Loop error: {e}")
        finally:
            self._loop.close()

    async def _connect(self):
        """Connect to MCP server."""
        try:
            self._stack = contextlib.AsyncExitStack()
            r, w = await self._stack.enter_async_context(
                stdio_client(self._params))
            self._session = await self._stack.enter_async_context(
                ClientSession(r, w))
            await self._session.initialize()
            logger.info("[MCPClient] Session initialized")
        except Exception as e:
            logger.error(f"[MCPClient] Connect failed: {e}")
            raise

    def call_tool(self, tool_name, arguments):
        """Call MCP tool - thread-safe."""
        if not self._started:
            self.start()

        if not self._session or not self._loop:
            raise RuntimeError("MCPClientManager not ready")

        # Schedule coroutine in the dedicated loop's thread
        future = asyncio.run_coroutine_threadsafe(
            self._call(tool_name, arguments),
            self._loop
        )
        return future.result(timeout=10)

    async def _call(self, tool_name, arguments):
        """Async call to MCP tool."""
        result = await self._session.call_tool(tool_name, arguments)
        if hasattr(result, "content") and result.content:
            return result.content[0].text
        return str(result)

    def stop(self):
        """Stop MCP client."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=2)
        self._started = False

_client = None

def get_mcp_client():
    global _client
    if _client is None:
        _client = MCPClientManager()
    return _client

def stop_mcp_client():
    global _client
    if _client:
        _client.stop()
        _client = None
