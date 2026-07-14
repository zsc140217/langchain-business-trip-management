"""
监控系统示例
演示如何使用LangSmith、Prometheus、告警系统
"""
import asyncio
import logging
from src.monitoring import initialize_langsmith, get_metrics_collector
from src.monitoring.prometheus_exporter import track_llm_call_metric

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_llm_call():
    """模拟LLM调用"""
    import time
    logger.info("开始LLM调用...")
    start_time = time.time()
    await asyncio.sleep(0.5)
    duration = time.time() - start_time
    track_llm_call_metric("llm", duration, cached=False)
    collector = get_metrics_collector()
    collector.record_api_call("llm", 0.01, cached=False)
    logger.info(f"LLM调用完成，耗时: {duration:.2f}秒")


async def main():
    """主函数"""
    logger.info("=== 初始化LangSmith ===")
    initialize_langsmith(project_name="travel-agent-demo", tags=["demo"])
    
    logger.info("\n=== 模拟API调用 ===")
    for i in range(3):
        await example_llm_call()
    
    logger.info("\n=== MetricsCollector统计 ===")
    collector = get_metrics_collector()
    summary = collector.get_summary()
    logger.info(f"总成本: ${summary['cost']['total_cost_usd']}")
    logger.info(f"缓存命中率: {summary['cost']['cache_hit_rate']}%")
    
    logger.info("\n=== 监控系统演示完成 ===")
    logger.info("1. 启动监控: cd monitoring && docker-compose up -d")
    logger.info("2. Prometheus: http://localhost:9090")
    logger.info("3. Grafana: http://localhost:3000 (admin/admin123)")


if __name__ == "__main__":
    asyncio.run(main())
