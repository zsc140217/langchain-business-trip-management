"""
Module 7: Production Infrastructure

Production-ready deployment with LangSmith observability,
three-layer caching, security protections, and comprehensive monitoring.

Key Features:
- LangSmith tracing (100% coverage)
- Three-layer caching (60%+ cost savings)
- Security protection (SQL injection, XSS, rate limiting)
- Monitoring & metrics (real-time performance tracking)
"""

from .langsmith_config import (
    LangSmithConfig,
    get_langsmith_config,
    initialize_langsmith,
    get_run_config
)

from .cache import (
    PromptCache,
    EmbeddingCache,
    RetrievalCache,
    CacheManager,
    get_cache_manager,
    initialize_cache
)

from .security import (
    TripRequest,
    QueryRequest,
    PolicyCheckRequest,
    SQLSanitizer,
    XSSProtection,
    RateLimiter,
    get_rate_limiter,
    require_rate_limit,
    validate_input,
    generate_secure_token,
    hash_sensitive_data,
    audit_log
)

from .monitoring import (
    MetricsCollector,
    PerformanceMetrics,
    CostMetrics,
    AgentMetrics,
    SystemMonitor,
    get_metrics_collector,
    track_performance,
    track_agent,
    check_system_health
)

__version__ = "1.0.0"

__all__ = [
    # LangSmith
    "LangSmithConfig",
    "get_langsmith_config",
    "initialize_langsmith",
    "get_run_config",

    # Cache
    "PromptCache",
    "EmbeddingCache",
    "RetrievalCache",
    "CacheManager",
    "get_cache_manager",
    "initialize_cache",

    # Security
    "TripRequest",
    "QueryRequest",
    "PolicyCheckRequest",
    "SQLSanitizer",
    "XSSProtection",
    "RateLimiter",
    "get_rate_limiter",
    "require_rate_limit",
    "validate_input",
    "generate_secure_token",
    "hash_sensitive_data",
    "audit_log",

    # Monitoring
    "MetricsCollector",
    "PerformanceMetrics",
    "CostMetrics",
    "AgentMetrics",
    "SystemMonitor",
    "get_metrics_collector",
    "track_performance",
    "track_agent",
    "check_system_health",
]
