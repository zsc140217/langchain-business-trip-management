"""FastAPI监控集成演示"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
import time

from src.monitoring import initialize_langsmith
from src.monitoring.prometheus_exporter import setup_metrics_endpoint, PrometheusMiddleware, track_llm_call_metric

app = FastAPI(title="监控演示")

@app.on_event("startup")
async def startup():
    initialize_langsmith(project_name="fastapi-demo")
    setup_metrics_endpoint(app)
    print("✅ 监控系统已启动")

app.add_middleware(PrometheusMiddleware)

@app.get("/")
async def root():
    return HTMLResponse("""
    <h1>🎯 监控演示</h1>
    <ul>
        <li><a href="/metrics">/metrics</a> - Prometheus指标</li>
        <li><a href="/api/query?q=test">/api/query</a> - 模拟查询</li>
        <li><a href="/api/stress?n=20">/api/stress</a> - 压力测试</li>
    </ul>
    <p>外部服务：</p>
    <ul>
        <li><a href="http://localhost:9090">Prometheus (9090)</a></li>
        <li><a href="http://localhost:3000">Grafana (3000)</a></li>
        <li><a href="https://smith.langchain.com">LangSmith</a></li>
    </ul>
    """)

@app.get("/api/query")
async def query(q: str):
    start = time.time()
    await asyncio.sleep(0.3)
    track_llm_call_metric("query_rewrite", 0.3, False)
    await asyncio.sleep(1.0)
    track_llm_call_metric("llm", 1.0, False)
    return {"status": "ok", "query": q, "duration": time.time() - start}

@app.get("/api/stress")
async def stress(n: int = 10):
    for i in range(n):
        await asyncio.sleep(0.1)
        track_llm_call_metric("stress_test", 0.1, False)
    return {"processed": n}

if __name__ == "__main__":
    print("\n🚀 启动监控演示服务")
    print("访问: http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
