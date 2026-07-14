"""
Prometheus指标导出器 (Phase 4 增强版)
提供/metrics端点，导出应用级指标

指标分组：
  基础指标（原有）: requests_total, llm_calls_total, request_duration_seconds 等
  域级别指标（P0新增）: unified_requests_total（按 domain/channel/status）
  审批指标（P0新增）: approval_count_total, approval_duration_hours
  记忆指标（P0新增）: memory_hit_ratio（按 memory_layer）
  工具指标（P0新增）: tool_calls_total（按 tool_name/success）

对应 docs/ARCHITECTURE_V2_PLAN.md 第九节「监控域」指标表
"""
import logging
import time
from fastapi import FastAPI, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
)
from src.modules.module_7_production.monitoring import get_metrics_collector

logger = logging.getLogger(__name__)

# 创建独立的Registry
registry = CollectorRegistry()

# ======== 基础 Counters（原有） ========
requests_total = Counter(
    'travel_agent_requests_total',
    'Total number of requests',
    ['status'],
    registry=registry
)

llm_calls_total = Counter(
    'travel_agent_llm_calls_total',
    'Total LLM API calls',
    ['operation', 'cached'],
    registry=registry
)

# ======== 域级别 Counters（Phase 4 新增） ========
unified_requests_total = Counter(
    'travel_agent_unified_requests_total',
    'Total requests by domain and channel',
    ['domain', 'channel', 'status'],
    registry=registry
)

approval_count_total = Counter(
    'travel_agent_approval_count_total',
    'Approval count by type and status',
    ['type', 'status'],
    registry=registry
)

tool_calls_total = Counter(
    'travel_agent_tool_calls_total',
    'Tool calls by tool name and success status',
    ['tool_name', 'success'],
    registry=registry
)

# Histograms
request_duration_seconds = Histogram(
    'travel_agent_request_duration_seconds',
    'Request duration in seconds',
    ['domain', 'channel'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=registry
)

llm_duration_seconds = Histogram(
    'travel_agent_llm_duration_seconds',
    'LLM call duration in seconds',
    ['operation'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry
)

# ======== 审批 Histograms（Phase 4 新增） ========
approval_duration_hours = Histogram(
    'travel_agent_approval_duration_hours',
    'Approval duration in hours by type',
    ['type'],
    buckets=[0.1, 0.5, 1.0, 6.0, 12.0, 24.0, 48.0, 72.0],
    registry=registry
)

# ======== 基础 Gauges（原有） ========
active_requests = Gauge(
    'travel_agent_active_requests',
    'Number of active requests',
    registry=registry
)

# ======== 记忆 Gauges（Phase 4 新增） ========
memory_hit_ratio = Gauge(
    'travel_agent_memory_hit_ratio',
    'Memory hit ratio by layer',
    ['memory_layer'],
    registry=registry
)
# ======== 审批超时 Gauges（Phase 4 P1） ========
pending_approval_max_hours = Gauge(
    'travel_agent_pending_approval_max_hours',
    'Current max hours a pending approval has been waiting',
    ['type'],
    registry=registry
)



cache_hit_rate = Gauge(
    'travel_agent_cache_hit_rate',
    'Cache hit rate percentage',
    registry=registry
)

cost_total_usd = Gauge(
    'travel_agent_cost_total_usd',
    'Total cost in USD',
    registry=registry
)

system_memory_usage_percent = Gauge(
    'travel_agent_system_memory_usage_percent',
    'System memory usage percentage',
    registry=registry
)

system_cpu_usage_percent = Gauge(
    'travel_agent_system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=registry
)


def update_metrics_from_collector():
    """从 MetricsCollector 更新 Prometheus 指标（含原有 + 新增）"""
    try:
        from src.modules.module_7_production.monitoring import get_metrics_collector
    except ImportError:
        return

    collector = get_metrics_collector()
    cache_hit_rate.set(collector.cost.get_cache_hit_rate())
    cost_total_usd.set(collector.cost.total_cost)
    memory_hit_ratio.labels(memory_layer="chat").set(0.0)
    memory_hit_ratio.labels(memory_layer="working").set(0.0)
    memory_hit_ratio.labels(memory_layer="long_term").set(0.0)

    try:
        from src.modules.module_7_production.monitoring import SystemMonitor
        memory = SystemMonitor.get_memory_usage()
        cpu = SystemMonitor.get_cpu_usage()
        system_memory_usage_percent.set(memory['percent'])
        system_cpu_usage_percent.set(cpu['percent'])
    except Exception as e:
        logger.warning(f"Failed to update system metrics: {e}")

    # 更新Gauge
    cache_hit_rate.set(collector.cost.get_cache_hit_rate())
    cost_total_usd.set(collector.cost.total_cost)

    # 更新系统指标
    try:
        from src.modules.module_7_production.monitoring import SystemMonitor
        memory = SystemMonitor.get_memory_usage()
        cpu = SystemMonitor.get_cpu_usage()
        system_memory_usage_percent.set(memory['percent'])
        system_cpu_usage_percent.set(cpu['percent'])
    except Exception as e:
        logger.warning(f"Failed to update system metrics: {e}")


def track_request_metric(duration_seconds: float, success: bool):
    """记录请求指标（原有，向后兼容）"""
    status = 'success' if success else 'error'
    requests_total.labels(status=status).inc()
    request_duration_seconds.labels(domain='legacy', channel='unknown').observe(duration_seconds)

def track_llm_call_metric(operation: str, duration_seconds: float, cached: bool = False):
    """记录LLM调用指标"""
    cached_label = 'true' if cached else 'false'
    llm_calls_total.labels(operation=operation, cached=cached_label).inc()
    llm_duration_seconds.labels(operation=operation).observe(duration_seconds)



# ======== Phase 4 新增追踪函数 ========

def track_unified_metric(
    domain: str,
    channel: str,
    duration_seconds: float,
    success: bool = True
):
    """记录统一域级别指标"""
    status = 'success' if success else 'error'
    unified_requests_total.labels(domain=domain, channel=channel, status=status).inc()
    request_duration_seconds.labels(domain=domain, channel=channel).observe(duration_seconds)


def track_approval_metric(approval_type: str, status: str):
    """记录审批指标"""
    approval_count_total.labels(type=approval_type, status=status).inc()


def track_approval_duration_metric(approval_type: str, duration_hours: float):
    """记录审批耗时"""
    approval_duration_hours.labels(type=approval_type).observe(duration_hours)


def track_tool_call_metric(tool_name: str, success: bool):
    """记录工具调用次数"""
    success_label = 'true' if success else 'false'
    tool_calls_total.labels(tool_name=tool_name, success=success_label).inc()


def set_memory_hit_ratio(layer: str, ratio: float):
    """设置某层记忆命中率"""
    memory_hit_ratio.labels(memory_layer=layer).set(ratio)


def set_pending_approval_max_hours(approval_type: str, hours: float):
    """设置审批最长等待时间（供AlertManager告警）"""
    pending_approval_max_hours.labels(type=approval_type).set(hours)


def setup_metrics_endpoint(app: FastAPI):
    """在FastAPI应用中添加/metrics端点"""
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        update_metrics_from_collector()
        data = generate_latest(registry)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    logger.info("Prometheus /metrics endpoint registered")


class PrometheusMiddleware:
    """FastAPI中间件，自动追踪所有请求"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        if scope["path"] == "/metrics":
            return await self.app(scope, receive, send)

        active_requests.inc()
        start_time = time.time()
        success = True

        try:
            await self.app(scope, receive, send)
        except Exception:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            track_unified_metric(
                domain=scope.get("domain", "http"),
                channel=scope.get("channel", "unknown"),
                duration_seconds=duration,
                success=success
            )
            active_requests.dec()
