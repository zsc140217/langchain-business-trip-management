"""
FastAPI服务 - 用于Prometheus抓取指标
"""

from fastapi import FastAPI
import uvicorn
import asyncio
import random
import time
from dotenv import load_dotenv

load_dotenv()

from src.monitoring import initialize_langsmith, get_metrics_collector
from src.monitoring.prometheus_exporter import setup_metrics_endpoint, PrometheusMiddleware, track_llm_call_metric

app = FastAPI(title="Travel Agent Monitoring API")

# 添加Prometheus中间件
app.add_middleware(PrometheusMiddleware)

@app.on_event("startup")
async def startup():
    """启动时初始化"""
    initialize_langsmith(project_name="api-demo")
    setup_metrics_endpoint(app)
    print("[OK] Monitoring system initialized")
    print("[INFO] Metrics endpoint: http://localhost:8000/metrics")

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Travel Agent Monitoring API",
        "metrics": "http://localhost:8000/metrics",
        "prometheus": "http://localhost:9090",
        "grafana": "http://localhost:3000",
    }

@app.get("/test")
async def test():
    """测试端点 - 模拟LLM调用"""
    delay = random.uniform(0.3, 0.8)
    await asyncio.sleep(delay)

    model = random.choice(["qwen-plus", "qwen-turbo", "gpt-4"])
    track_llm_call_metric(model, delay, False)

    collector = get_metrics_collector()
    collector.record_request(delay, True)
    collector.record_api_call(f"llm_{model}", random.uniform(0.001, 0.005), False)

    return {
        "status": "ok",
        "model": model,
        "latency": f"{delay:.3f}s"
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    print("[INFO] Starting FastAPI monitoring service...")
    print("[INFO] Visit http://localhost:8000/docs for API documentation")
    print("[INFO] Visit http://localhost:8000/metrics for Prometheus metrics")
    uvicorn.run(app, host="0.0.0.0", port=8000)
