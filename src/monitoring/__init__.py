"""
监控系统统一入口
整合LangSmith追踪、Prometheus指标、告警管理

复用module_7_production的实现，提供简化的API
"""
try:
    from src.modules.module_7_production.monitoring import (
        get_metrics_collector,
        track_performance,
        track_agent,
        check_system_health,
        MetricsCollector,
    )
except ImportError:
    # 降级处理：如果依赖不可用，提供mock实现
    def get_metrics_collector():
        """Mock实现"""
        from unittest.mock import Mock
        return Mock()

    def track_performance(operation: str):
        """Mock装饰器"""
        def decorator(func):
            return func
        return decorator

    def track_agent(agent_name: str):
        """Mock装饰器"""
        def decorator(func):
            return func
        return decorator

    def check_system_health():
        """Mock实现"""
        return {"status": "healthy", "checks": {}}

    MetricsCollector = type("MetricsCollector", (), {})

try:
    from src.modules.module_7_production.langsmith_config import (
        initialize_langsmith,
        get_langsmith_config,
        get_run_config,
        LangSmithConfig,
    )
except ImportError:
    # 降级处理
    def initialize_langsmith(*args, **kwargs):
        """Mock实现"""
        from unittest.mock import Mock
        return Mock()

    def get_langsmith_config():
        """Mock实现"""
        from unittest.mock import Mock
        return Mock()

    def get_run_config(**kwargs):
        """Mock实现"""
        return {}

    LangSmithConfig = type("LangSmithConfig", (), {})

# 导出统一API

# Phase 4: Prometheus domain-level + approval metrics
from src.monitoring.prometheus_exporter import (
    track_unified_metric,
    track_approval_metric,
    track_approval_duration_metric,
    track_tool_call_metric,
    set_memory_hit_ratio,
    set_pending_approval_max_hours,
    setup_metrics_endpoint,
    PrometheusMiddleware,
    unified_requests_total,
    approval_count_total,
    approval_duration_hours,
    memory_hit_ratio,
    pending_approval_max_hours,
    tool_calls_total,
)


def trace_operation(operation, domain="unknown", channel="unknown"):
    "Decorator that tracks Prometheus metrics + LangSmith span"
    def decorator(func):
        import time
        import functools
        from src.monitoring import get_langsmith_config

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ls_config = get_langsmith_config()
            start = time.time()
            success = True
            try:
                with ls_config.trace_context(
                    operation=operation,
                    tags=["domain:"+domain, "channel:"+channel]
                ) as run_config:
                    result = func(*args, **kwargs)
                    return result
            except Exception:
                success = False
                raise
            finally:
                duration = time.time() - start
                track_unified_metric(
                    domain=domain,
                    channel=channel,
                    duration_seconds=duration,
                    success=success
                )
        return wrapper
    return decorator

__all__ = [
    # Prometheus指标
    "get_metrics_collector",
    "track_performance",
    "track_agent",
    "check_system_health",
    "MetricsCollector",
    # LangSmith追踪
    "initialize_langsmith",
    "get_langsmith_config",
    "get_run_config",
    "LangSmithConfig",
]
