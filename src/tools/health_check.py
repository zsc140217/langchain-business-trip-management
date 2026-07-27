"""
Tool Health Check System
Monitors tool availability and performance

Features:
- Periodic health checks
- Health status tracking
- Automatic degradation detection
- Health metrics collection
"""
import time
import threading
import logging
from typing import Dict, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Tool health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Health check result"""
    tool_name: str
    status: HealthStatus
    latency_ms: float
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class ToolHealthChecker:
    """
    Tool health checker

    Performs periodic health checks on tools and tracks their status
    """

    def __init__(self, check_interval: int = 60,
                 failure_threshold: int = 3,
                 success_threshold: int = 2):
        """
        Initialize health checker

        Args:
            check_interval: Seconds between health checks
            failure_threshold: Consecutive failures before marking as down
            success_threshold: Consecutive successes before marking as healthy
        """
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold

        self._health_status: Dict[str, HealthCheckResult] = {}
        self._check_functions: Dict[str, Callable] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def register_tool(self, tool_name: str, check_function: Callable) -> None:
        """
        Register a tool for health checking

        Args:
            tool_name: Tool name
            check_function: Function that returns True if tool is healthy
        """
        with self._lock:
            self._check_functions[tool_name] = check_function
            self._health_status[tool_name] = HealthCheckResult(
                tool_name=tool_name,
                status=HealthStatus.UNKNOWN,
                latency_ms=0.0
            )

        logger.info(f"[HealthCheck] Registered tool: {tool_name}")

    def start(self) -> None:
        """Start background health checking"""
        if self._running:
            logger.warning("[HealthCheck] Health checker already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._check_loop, daemon=True)
        self._thread.start()
        logger.info("[HealthCheck] Health checker started")

    def stop(self) -> None:
        """Stop background health checking"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("[HealthCheck] Health checker stopped")

    def check_tool_health(self, tool_name: str) -> HealthCheckResult:
        """
        Check health of a specific tool

        Args:
            tool_name: Tool name

        Returns:
            Health check result
        """
        check_function = self._check_functions.get(tool_name)
        if check_function is None:
            return HealthCheckResult(
                tool_name=tool_name,
                status=HealthStatus.UNKNOWN,
                latency_ms=0.0,
                error="Tool not registered for health checking"
            )

        start_time = time.time()
        try:
            is_healthy = check_function()
            latency_ms = (time.time() - start_time) * 1000

            # Get previous result
            previous = self._health_status.get(tool_name)
            consecutive_failures = 0
            consecutive_successes = 0

            if is_healthy:
                # Success
                if previous and previous.status != HealthStatus.HEALTHY:
                    consecutive_successes = previous.consecutive_successes + 1
                else:
                    consecutive_successes = 1

                # Determine status based on threshold
                if consecutive_successes >= self.success_threshold:
                    status = HealthStatus.HEALTHY
                else:
                    status = HealthStatus.DEGRADED

            else:
                # Failure
                if previous:
                    consecutive_failures = previous.consecutive_failures + 1
                else:
                    consecutive_failures = 1

                # Determine status based on threshold
                if consecutive_failures >= self.failure_threshold:
                    status = HealthStatus.DOWN
                else:
                    status = HealthStatus.DEGRADED

            result = HealthCheckResult(
                tool_name=tool_name,
                status=status,
                latency_ms=latency_ms,
                consecutive_failures=consecutive_failures,
                consecutive_successes=consecutive_successes
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            previous = self._health_status.get(tool_name)
            consecutive_failures = (previous.consecutive_failures + 1) if previous else 1

            status = HealthStatus.DOWN if consecutive_failures >= self.failure_threshold else HealthStatus.DEGRADED

            result = HealthCheckResult(
                tool_name=tool_name,
                status=status,
                latency_ms=latency_ms,
                error=str(e),
                consecutive_failures=consecutive_failures
            )

            logger.warning(f"[HealthCheck] Tool {tool_name} health check failed: {e}")

        # Update status
        with self._lock:
            self._health_status[tool_name] = result

        return result

    def check_all_tools(self) -> Dict[str, HealthCheckResult]:
        """
        Check health of all registered tools

        Returns:
            Dictionary of health check results {tool_name: result}
        """
        results = {}
        for tool_name in self._check_functions.keys():
            results[tool_name] = self.check_tool_health(tool_name)

        return results

    def get_health_status(self, tool_name: str) -> Optional[HealthCheckResult]:
        """
        Get latest health status for a tool

        Args:
            tool_name: Tool name

        Returns:
            Health check result or None if not found
        """
        with self._lock:
            return self._health_status.get(tool_name)

    def get_all_health_status(self) -> Dict[str, HealthCheckResult]:
        """
        Get latest health status for all tools

        Returns:
            Dictionary of health check results {tool_name: result}
        """
        with self._lock:
            return self._health_status.copy()

    def get_healthy_tools(self) -> Dict[str, HealthCheckResult]:
        """
        Get all healthy tools

        Returns:
            Dictionary of healthy tools {tool_name: result}
        """
        with self._lock:
            return {
                name: result
                for name, result in self._health_status.items()
                if result.status == HealthStatus.HEALTHY
            }

    def get_unhealthy_tools(self) -> Dict[str, HealthCheckResult]:
        """
        Get all unhealthy tools (degraded or down)

        Returns:
            Dictionary of unhealthy tools {tool_name: result}
        """
        with self._lock:
            return {
                name: result
                for name, result in self._health_status.items()
                if result.status in [HealthStatus.DEGRADED, HealthStatus.DOWN]
            }

    def _check_loop(self) -> None:
        """Background health check loop"""
        logger.info("[HealthCheck] Health check loop started")

        while self._running:
            try:
                self.check_all_tools()
            except Exception as e:
                logger.error(f"[HealthCheck] Error in health check loop: {e}")

            # Sleep for check interval
            time.sleep(self.check_interval)

        logger.info("[HealthCheck] Health check loop stopped")


# Global health checker instance
_health_checker_instance: Optional[ToolHealthChecker] = None


def get_health_checker() -> ToolHealthChecker:
    """
    Get global health checker instance

    Returns:
        ToolHealthChecker instance
    """
    global _health_checker_instance

    if _health_checker_instance is None:
        from src.tools.config_loader import get_config_loader
        config_loader = get_config_loader()
        health_config = config_loader.get_health_check_config()

        _health_checker_instance = ToolHealthChecker(
            check_interval=health_config.get('interval', 60),
            failure_threshold=health_config.get('failure_threshold', 3),
            success_threshold=health_config.get('success_threshold', 2)
        )

    return _health_checker_instance


def start_health_checking() -> None:
    """Start global health checking"""
    checker = get_health_checker()
    checker.start()


def stop_health_checking() -> None:
    """Stop global health checking"""
    checker = get_health_checker()
    checker.stop()
