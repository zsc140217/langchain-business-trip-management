"""
测试监控系统 - 生成模拟数据
用于验证Prometheus、Grafana、LangSmith、Alertmanager
"""

import asyncio
import time
import random
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入监控模块
from src.monitoring import initialize_langsmith, get_metrics_collector
from src.monitoring.prometheus_exporter import track_llm_call_metric

async def generate_test_data():
    """生成测试数据"""
    print(">>> 开始生成监控测试数据...")

    # 初始化LangSmith
    initialize_langsmith(project_name="test-demo")
    print("[OK] LangSmith初始化完成")

    # 获取指标收集器
    collector = get_metrics_collector()

    # 生成20条测试数据
    for i in range(20):
        print(f"[{i+1}/20] 生成数据...")

        # 模拟LLM调用
        start = time.time()
        await asyncio.sleep(random.uniform(0.3, 0.8))  # 模拟300-800ms延迟
        duration = time.time() - start

        # 随机成功/失败
        success = random.random() > 0.1  # 90%成功率

        # 记录Prometheus指标
        model_name = random.choice(["qwen-plus", "qwen-turbo", "gpt-4"])
        track_llm_call_metric(model_name, duration, not success)

        # 记录通用请求
        collector.record_request(duration, success)

        # 模拟成本
        cost = random.uniform(0.0001, 0.005)
        collector.record_api_call(f"llm_call_{model_name}", cost, cached=False)

        # 记录Agent调用
        if i % 3 == 0:
            collector.record_agent_invocation("travel_agent", duration, success, cost)

        print(f"   模型: {model_name}, 延迟: {duration:.3f}s, 成功: {success}")

        # 短暂等待
        await asyncio.sleep(0.5)

    print("\n[OK] 数据生成完成！")
    print("\n访问以下网站查看数据：")
    print("   Prometheus:   http://localhost:9090")
    print("   Grafana:      http://localhost:3000 (admin/admin123)")
    print("   Alertmanager: http://localhost:9093")
    print("   LangSmith:    https://smith.langchain.com/")

if __name__ == "__main__":
    asyncio.run(generate_test_data())
