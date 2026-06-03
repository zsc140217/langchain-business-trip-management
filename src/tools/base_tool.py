"""
Base Tool Class
Provides common functionality for all tools

Design Principles:
- Single Responsibility: Each tool does one thing well
- Error Handling: Graceful degradation with fallbacks
- Caching: Optional caching for expensive operations
- Observability: Automatic tracing with LangSmith
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_core.tools import BaseTool as LangChainBaseTool
from langsmith import traceable
import logging
import time

logger = logging.getLogger(__name__)


class BaseTool(LangChainBaseTool, ABC):
    """
    Base class for all tools

    Provides:
    - Input validation
    - Error handling
    - Caching (optional)
    - Observability (automatic tracing)
    - Retry logic

    Usage:
        class MyTool(BaseTool):
            name = "my_tool"
            description = "Does something useful"

            def _run(self, param1: str, param2: int) -> str:
                # Implementation
                pass
    """

    # Tool metadata (override in subclasses)
    name: str = "base_tool"
    description: str = "Base tool class"

    # Configuration
    cache_enabled: bool = False
    cache_ttl_seconds: int = 300
    max_retries: int = 3
    timeout_seconds: float = 30.0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cache: Dict[str, tuple] = {}  # (result, timestamp)

    @traceable(name="tool_invoke")
    def _run(self, **kwargs) -> str:
        """
        Execute tool (synchronous)

        This method should be overridden by subclasses

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result as string

        Raises:
            ValueError: Invalid parameters
            RuntimeError: Execution failed
        """
        raise NotImplementedError("Subclasses must implement _run method")

    async def _arun(self, **kwargs) -> str:
        """
        Execute tool (asynchronous)

        Default implementation wraps synchronous _run
        Override for true async execution

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result as string
        """
        return self._run(**kwargs)

    def invoke(self, input_dict: Dict[str, Any]) -> str:
        """
        Invoke tool with error handling and caching

        Args:
            input_dict: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ValueError: Invalid parameters
            RuntimeError: Execution failed after retries
        """
        start_time = time.time()

        try:
            # Check cache
            if self.cache_enabled:
                cached_result = self._get_from_cache(input_dict)
                if cached_result is not None:
                    logger.debug(f"{self.name}: Cache hit")
                    return cached_result

            # Execute with retry logic
            result = self._execute_with_retry(input_dict)

            # Update cache
            if self.cache_enabled:
                self._put_in_cache(input_dict, result)

            execution_time = (time.time() - start_time) * 1000
            logger.info(f"{self.name} executed in {execution_time:.2f}ms")

            return result

        except Exception as e:
            logger.error(f"{self.name} failed: {e}")
            raise RuntimeError(f"Tool execution failed: {e}") from e

    def _execute_with_retry(self, input_dict: Dict[str, Any]) -> str:
        """
        Execute tool with retry logic

        Args:
            input_dict: Tool parameters

        Returns:
            Tool execution result

        Raises:
            RuntimeError: All retry attempts failed
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"{self.name}: Attempt {attempt + 1}/{self.max_retries}")
                return self._run(**input_dict)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"{self.name}: Attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"{self.name}: All {self.max_retries} attempts failed")

        raise RuntimeError(f"All retry attempts failed: {last_error}") from last_error

    def _get_from_cache(self, input_dict: Dict[str, Any]) -> Optional[str]:
        """
        Get result from cache if available and not expired

        Args:
            input_dict: Tool parameters

        Returns:
            Cached result or None
        """
        cache_key = self._make_cache_key(input_dict)
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.cache_ttl_seconds:
                return result
            else:
                # Expired, remove from cache
                del self._cache[cache_key]
        return None

    def _put_in_cache(self, input_dict: Dict[str, Any], result: str) -> None:
        """
        Put result in cache

        Args:
            input_dict: Tool parameters
            result: Tool execution result
        """
        cache_key = self._make_cache_key(input_dict)
        self._cache[cache_key] = (result, time.time())

    def _make_cache_key(self, input_dict: Dict[str, Any]) -> str:
        """
        Create cache key from input parameters

        Args:
            input_dict: Tool parameters

        Returns:
            Cache key string
        """
        # Simple implementation: sort keys and concatenate
        sorted_items = sorted(input_dict.items())
        return f"{self.name}:" + ":".join(f"{k}={v}" for k, v in sorted_items)

    def clear_cache(self) -> None:
        """Clear tool cache"""
        self._cache.clear()
        logger.info(f"{self.name}: Cache cleared")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class ToolExecutionError(Exception):
    """Custom exception for tool execution failures"""
    pass
