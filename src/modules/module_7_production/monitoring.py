"""
Monitoring and Metrics Module

Comprehensive monitoring for production systems:
1. Performance Metrics: Latency, throughput, success rate
2. Cost Tracking: API call costs, cache savings
3. Agent Metrics: Per-agent performance and usage
4. System Health: Memory, CPU, error rates
5. Custom Metrics: Business-specific KPIs

Features:
- Real-time metrics collection
- Prometheus-compatible metrics export
- Alerting on threshold breaches
- Dashboard-ready statistics
"""

import time
import logging
import psutil
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """Container for a metric value with metadata."""
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    min_latency: float = float('inf')
    max_latency: float = 0.0
    latencies: deque = field(default_factory=lambda: deque(maxlen=1000))

    def record_request(self, latency: float, success: bool = True):
        """Record a request."""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        self.total_latency += latency
        self.min_latency = min(self.min_latency, latency)
        self.max_latency = max(self.max_latency, latency)
        self.latencies.append(latency)

    def get_avg_latency(self) -> float:
        """Get average latency."""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency / self.total_requests

    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    def get_p95_latency(self) -> float:
        """Get 95th percentile latency."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[index] if index < len(sorted_latencies) else 0.0

    def get_p99_latency(self) -> float:
        """Get 99th percentile latency."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[index] if index < len(sorted_latencies) else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "avg_latency_ms": round(self.get_avg_latency() * 1000, 2),
            "min_latency_ms": round(self.min_latency * 1000, 2) if self.min_latency != float('inf') else 0,
            "max_latency_ms": round(self.max_latency * 1000, 2),
            "p95_latency_ms": round(self.get_p95_latency() * 1000, 2),
            "p99_latency_ms": round(self.get_p99_latency() * 1000, 2),
            "success_rate": round(self.get_success_rate(), 2)
        }


@dataclass
class CostMetrics:
    """Cost tracking metrics."""
    total_api_calls: int = 0
    total_cost: float = 0.0
    cached_calls: int = 0
    cache_savings: float = 0.0
    cost_by_operation: Dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def record_api_call(self, operation: str, cost: float, cached: bool = False):
        """Record an API call."""
        self.total_api_calls += 1
        if not cached:
            self.total_cost += cost
            self.cost_by_operation[operation] += cost
        else:
            self.cached_calls += 1
            self.cache_savings += cost

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate as percentage."""
        total = self.total_api_calls + self.cached_calls
        if total == 0:
            return 0.0
        return (self.cached_calls / total) * 100

    def get_savings_rate(self) -> float:
        """Get cost savings rate as percentage."""
        potential_total = self.total_cost + self.cache_savings
        if potential_total == 0:
            return 0.0
        return (self.cache_savings / potential_total) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_api_calls": self.total_api_calls,
            "total_cost_usd": round(self.total_cost, 4),
            "cached_calls": self.cached_calls,
            "cache_savings_usd": round(self.cache_savings, 4),
            "cache_hit_rate": round(self.get_cache_hit_rate(), 2),
            "savings_rate": round(self.get_savings_rate(), 2),
            "cost_by_operation": {
                k: round(v, 4) for k, v in self.cost_by_operation.items()
            }
        }


@dataclass
class AgentMetrics:
    """Metrics for individual agents."""
    agent_name: str
    invocations: int = 0
    successes: int = 0
    failures: int = 0
    total_latency: float = 0.0
    total_cost: float = 0.0

    def record_invocation(self, latency: float, success: bool, cost: float = 0.0):
        """Record an agent invocation."""
        self.invocations += 1
        if success:
            self.successes += 1
        else:
            self.failures += 1
        self.total_latency += latency
        self.total_cost += cost

    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.invocations == 0:
            return 0.0
        return (self.successes / self.invocations) * 100

    def get_avg_latency(self) -> float:
        """Get average latency."""
        if self.invocations == 0:
            return 0.0
        return self.total_latency / self.invocations

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "invocations": self.invocations,
            "successes": self.successes,
            "failures": self.failures,
            "success_rate": round(self.get_success_rate(), 2),
            "avg_latency_ms": round(self.get_avg_latency() * 1000, 2),
            "total_cost_usd": round(self.total_cost, 4)
        }


class SystemMonitor:
    """Monitor system resources."""

    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get memory usage statistics."""
        memory = psutil.virtual_memory()
        return {
            "total_mb": round(memory.total / (1024 * 1024), 2),
            "available_mb": round(memory.available / (1024 * 1024), 2),
            "used_mb": round(memory.used / (1024 * 1024), 2),
            "percent": memory.percent
        }

    @staticmethod
    def get_cpu_usage() -> Dict[str, float]:
        """Get CPU usage statistics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        return {
            "percent": cpu_percent,
            "count": cpu_count,
            "per_cpu": psutil.cpu_percent(interval=1, percpu=True)
        }

    @staticmethod
    def get_disk_usage() -> Dict[str, float]:
        """Get disk usage statistics."""
        disk = psutil.disk_usage('/')
        return {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "percent": disk.percent
        }


class MetricsCollector:
    """
    Central metrics collector for the application.

    Collects and aggregates metrics from various sources:
    - Performance metrics (latency, throughput)
    - Cost metrics (API calls, caching)
    - Agent metrics (per-agent stats)
    - System metrics (CPU, memory)
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.performance = PerformanceMetrics()
        self.cost = CostMetrics()
        self.agents: Dict[str, AgentMetrics] = {}
        self.custom_metrics: Dict[str, List[MetricValue]] = defaultdict(list)
        self.start_time = datetime.utcnow()
        self.alerts: List[Dict[str, Any]] = []

        logger.info("MetricsCollector initialized")

    def record_request(self, latency: float, success: bool = True):
        """Record a request."""
        self.performance.record_request(latency, success)

    def record_api_call(self, operation: str, cost: float, cached: bool = False):
        """Record an API call."""
        self.cost.record_api_call(operation, cost, cached)

    def record_agent_invocation(
        self,
        agent_name: str,
        latency: float,
        success: bool,
        cost: float = 0.0
    ):
        """Record an agent invocation."""
        if agent_name not in self.agents:
            self.agents[agent_name] = AgentMetrics(agent_name=agent_name)

        self.agents[agent_name].record_invocation(latency, success, cost)

    def record_custom_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Record a custom metric.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels for the metric
        """
        metric = MetricValue(value=value, labels=labels or {})
        self.custom_metrics[name].append(metric)

        # Keep only last 1000 values per metric
        if len(self.custom_metrics[name]) > 1000:
            self.custom_metrics[name] = self.custom_metrics[name][-1000:]

    def add_alert(self, severity: str, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Add an alert.

        Args:
            severity: Alert severity (info, warning, error, critical)
            message: Alert message
            details: Additional details
        """
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": severity,
            "message": message,
            "details": details or {}
        }
        self.alerts.append(alert)
        logger.warning(f"ALERT [{severity}]: {message}")

        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": round(uptime, 2),
            "performance": self.performance.to_dict(),
            "cost": self.cost.to_dict(),
            "agents": {
                name: agent.to_dict()
                for name, agent in self.agents.items()
            },
            "system": {
                "memory": SystemMonitor.get_memory_usage(),
                "cpu": SystemMonitor.get_cpu_usage(),
                "disk": SystemMonitor.get_disk_usage()
            },
            "alerts": self.alerts[-10:] if self.alerts else []
        }

    def get_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            Metrics in Prometheus text format
        """
        lines = []

        # Performance metrics
        lines.append("# HELP requests_total Total number of requests")
        lines.append("# TYPE requests_total counter")
        lines.append(f"requests_total {self.performance.total_requests}")

        lines.append("# HELP request_latency_seconds Request latency")
        lines.append("# TYPE request_latency_seconds histogram")
        lines.append(f"request_latency_seconds {{quantile=\"0.95\"}} {self.performance.get_p95_latency()}")
        lines.append(f"request_latency_seconds {{quantile=\"0.99\"}} {self.performance.get_p99_latency()}")

        # Cost metrics
        lines.append("# HELP api_calls_total Total API calls")
        lines.append("# TYPE api_calls_total counter")
        lines.append(f"api_calls_total {self.cost.total_api_calls}")

        lines.append("# HELP cost_total_usd Total cost in USD")
        lines.append("# TYPE cost_total_usd counter")
        lines.append(f"cost_total_usd {self.cost.total_cost}")

        # Agent metrics
        for agent_name, agent in self.agents.items():
            lines.append(f"# HELP agent_invocations_total Total agent invocations")
            lines.append(f"# TYPE agent_invocations_total counter")
            lines.append(f"agent_invocations_total{{agent=\"{agent_name}\"}} {agent.invocations}")

        return "\n".join(lines)

    def reset(self):
        """Reset all metrics."""
        self.performance = PerformanceMetrics()
        self.cost = CostMetrics()
        self.agents.clear()
        self.custom_metrics.clear()
        self.alerts.clear()
        self.start_time = datetime.utcnow()
        logger.info("Metrics reset")


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector

    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()

    return _metrics_collector


def track_performance(operation: str = "request"):
    """
    Decorator to track function performance.

    Args:
        operation: Operation name for tracking

    Example:
        @track_performance("trip_planning")
        def plan_trip(destination: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            start_time = time.time()
            success = True

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"Error in {operation}: {str(e)}")
                raise
            finally:
                latency = time.time() - start_time
                collector.record_request(latency, success)

                # Add alert if latency is too high
                if latency > 5.0:  # 5 seconds threshold
                    collector.add_alert(
                        "warning",
                        f"High latency detected in {operation}",
                        {"latency_seconds": latency}
                    )

        return wrapper
    return decorator


def track_agent(agent_name: str):
    """
    Decorator to track agent performance.

    Args:
        agent_name: Agent name

    Example:
        @track_agent("PolicyAdvisor")
        def check_policy(trip_data: dict):
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            start_time = time.time()
            success = True

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"Error in agent {agent_name}: {str(e)}")
                raise
            finally:
                latency = time.time() - start_time
                # Estimate cost (can be replaced with actual cost calculation)
                cost = latency * 0.0001  # $0.0001 per second estimate

                collector.record_agent_invocation(agent_name, latency, success, cost)

        return wrapper
    return decorator


# Health check utilities
def check_system_health() -> Dict[str, Any]:
    """
    Perform system health check.

    Returns:
        Health check results with status and details
    """
    collector = get_metrics_collector()
    memory = SystemMonitor.get_memory_usage()
    cpu = SystemMonitor.get_cpu_usage()

    # Determine health status
    status = "healthy"
    issues = []

    if memory["percent"] > 90:
        status = "degraded"
        issues.append("High memory usage")

    if cpu["percent"] > 90:
        status = "degraded"
        issues.append("High CPU usage")

    if collector.performance.get_success_rate() < 95 and collector.performance.total_requests > 10:
        status = "degraded"
        issues.append("Low success rate")

    if issues:
        status = "unhealthy" if len(issues) > 1 else "degraded"

    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "memory": memory["percent"] < 90,
            "cpu": cpu["percent"] < 90,
            "success_rate": collector.performance.get_success_rate() >= 95
        },
        "issues": issues,
        "details": {
            "memory_usage_percent": memory["percent"],
            "cpu_usage_percent": cpu["percent"],
            "success_rate": collector.performance.get_success_rate()
        }
    }


# Example usage
if __name__ == "__main__":
    # Initialize metrics collector
    collector = get_metrics_collector()

    # Simulate some metrics
    collector.record_request(0.5, success=True)
    collector.record_request(0.3, success=True)
    collector.record_request(1.2, success=False)

    collector.record_api_call("embedding", 0.001, cached=False)
    collector.record_api_call("llm", 0.01, cached=False)
    collector.record_api_call("llm", 0.01, cached=True)

    collector.record_agent_invocation("PolicyAdvisor", 0.8, True, 0.005)
    collector.record_agent_invocation("TripPlanner", 1.5, True, 0.012)

    # Get summary
    summary = collector.get_summary()
    print(json.dumps(summary, indent=2))

    # Health check
    health = check_system_health()
    print("\nHealth Check:", json.dumps(health, indent=2))
