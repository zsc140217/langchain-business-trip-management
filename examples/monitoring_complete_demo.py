"""监控系统完整演示"""
import asyncio
import logging
import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.monitoring import initialize_langsmith, get_metrics_collector
from src.monitoring.prometheus_exporter import track_llm_call_metric

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simulate_llm_call(operation: str, duration: float, cached: bool = False):
    """模拟LLM调用"""
    logger.info(f"🔄 {operation} 开始...")
    await asyncio.sleep(duration)
    track_llm_call_metric(operation, duration, cached)
    collector = get_metrics_collector()
    collector.record_api_call(operation, duration * 0.01, cached)
    logger.info(f"✅ {operation} 完成")

async def main():
    logger.info("🚀 监控系统演示启动\n")
    
    # 1. 初始化LangSmith
    config = initialize_langsmith(project_name="travel-agent-demo", tags=["demo"])
    logger.info(f"✅ LangSmith: {'已启用' if config.enabled else '未启用'}\n")
    
    # 2. 模拟请求
    logger.info("📊 模拟10个请求...")
    for i in range(1, 11):
        await simulate_llm_call("query_rewrite", 0.3, cached=False)
        await simulate_llm_call("embedding", 0.2, cached=i % 3 == 0)
        await simulate_llm_call("llm", 1.0, cached=False)
    
    # 3. 显示统计
    collector = get_metrics_collector()
    summary = collector.get_summary()
    logger.info(f"\n📈 统计结果:")
    logger.info(f"  总成本: ${summary['cost']['total_cost_usd']:.4f}")
    logger.info(f"  缓存命中率: {summary['cost']['cache_hit_rate']:.2f}%")
    logger.info(f"\n✅ 演示完成！")
    logger.info(f"访问 https://smith.langchain.com/ 查看追踪")

if __name__ == "__main__":
    asyncio.run(main())
