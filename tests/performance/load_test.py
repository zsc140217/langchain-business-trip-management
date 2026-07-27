"""
轻量级压测模块 - 差旅管理系统性能测试

测试目标：
1. 简单查询场景（Simple RAG）
2. 复杂任务场景（Multi-Agent）
3. 路由系统场景（Intelligent Router）

性能指标：
- P50 延迟（中位数）
- P95 延迟（95%请求）
- P99 延迟（99%请求）
- QPS（每秒查询数）
- 成功率
"""
import asyncio
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass, field
import json
import httpx


@dataclass
class PerformanceMetrics:
    """性能指标统计"""
    scenario_name: str
    total_requests: int
    successful_requests: int = 0
    failed_requests: int = 0
    latencies: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def duration(self) -> float:
        """总耗时（秒）"""
        return self.end_time - self.start_time

    @property
    def qps(self) -> float:
        """每秒查询数"""
        if self.duration == 0:
            return 0.0
        return self.successful_requests / self.duration

    @property
    def p50_latency(self) -> float:
        """P50延迟（中位数）"""
        if not self.latencies:
            return 0.0
        return statistics.median(self.latencies)

    @property
    def p95_latency(self) -> float:
        """P95延迟"""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[index]

    @property
    def p99_latency(self) -> float:
        """P99延迟"""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[index]

    @property
    def avg_latency(self) -> float:
        """平均延迟"""
        if not self.latencies:
            return 0.0
        return statistics.mean(self.latencies)

    @property
    def min_latency(self) -> float:
        """最小延迟"""
        if not self.latencies:
            return 0.0
        return min(self.latencies)

    @property
    def max_latency(self) -> float:
        """最大延迟"""
        if not self.latencies:
            return 0.0
        return max(self.latencies)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "scenario": self.scenario_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": f"{self.success_rate:.2f}%",
            "duration": f"{self.duration:.2f}s",
            "qps": f"{self.qps:.2f}",
            "latency": {
                "min": f"{self.min_latency * 1000:.2f}ms",
                "avg": f"{self.avg_latency * 1000:.2f}ms",
                "p50": f"{self.p50_latency * 1000:.2f}ms",
                "p95": f"{self.p95_latency * 1000:.2f}ms",
                "p99": f"{self.p99_latency * 1000:.2f}ms",
                "max": f"{self.max_latency * 1000:.2f}ms",
            },
            "errors": self.errors[:5] if self.errors else [],  # 只显示前5个错误
        }


@dataclass
class LoadTestConfig:
    """压测配置"""
    base_url: str = "http://localhost:8000"
    concurrency: int = 10  # 并发数
    total_requests: int = 100  # 总请求数
    timeout: float = 30.0  # 超时时间（秒）


class LoadTester:
    """压测执行器"""

    def __init__(self, config: LoadTestConfig):
        self.config = config

    async def _send_request(
        self,
        client: httpx.AsyncClient,
        url: str,
        payload: Dict[str, Any],
        metrics: PerformanceMetrics,
    ):
        """发送单个请求并记录指标"""
        start_time = time.time()
        try:
            response = await client.post(
                url,
                json=payload,
                timeout=self.config.timeout,
            )
            latency = time.time() - start_time

            if response.status_code == 200:
                metrics.successful_requests += 1
                metrics.latencies.append(latency)
            else:
                metrics.failed_requests += 1
                metrics.errors.append(
                    f"HTTP {response.status_code}: {response.text[:100]}"
                )

        except Exception as e:
            latency = time.time() - start_time
            metrics.failed_requests += 1
            metrics.errors.append(f"{type(e).__name__}: {str(e)[:100]}")

    async def run_scenario(
        self,
        scenario_name: str,
        endpoint: str,
        payload: Dict[str, Any],
    ) -> PerformanceMetrics:
        """运行单个测试场景"""
        print(f"\n{'='*60}")
        print(f"[开始] {scenario_name}")
        print(f"[配置] 并发: {self.config.concurrency}, 总请求: {self.config.total_requests}")
        print(f"[端点] {endpoint}")
        print(f"{'='*60}\n")

        metrics = PerformanceMetrics(
            scenario_name=scenario_name,
            total_requests=self.config.total_requests,
        )

        url = f"{self.config.base_url}{endpoint}"

        # 创建异步HTTP客户端
        async with httpx.AsyncClient() as client:
            metrics.start_time = time.time()

            # 创建任务队列
            tasks = []
            for i in range(self.config.total_requests):
                task = self._send_request(client, url, payload, metrics)
                tasks.append(task)

                # 控制并发数
                if len(tasks) >= self.config.concurrency:
                    await asyncio.gather(*tasks)
                    tasks = []
                    print(f"[进度] {i + 1}/{self.config.total_requests}")

            # 执行剩余任务
            if tasks:
                await asyncio.gather(*tasks)

            metrics.end_time = time.time()

        return metrics

    async def run_all_scenarios(self) -> List[PerformanceMetrics]:
        """运行所有测试场景"""
        scenarios = [
            {
                "name": "简单查询 - Simple RAG",
                "endpoint": "/simple-rag/invoke",
                "payload": {"input": "去上海出差住宿能报多少钱？"},
            },
            {
                "name": "复杂任务 - Multi-Agent",
                "endpoint": "/multi-agent/invoke",
                "payload": {"input": "下周去杭州出差3天，帮我规划行程"},
            },
            {
                "name": "智能路由 - Chat Sync",
                "endpoint": "/api/chat/sync",
                "payload": {"query": "出差期间的餐饮补贴标准是什么？"},
            },
        ]

        all_metrics = []
        for scenario in scenarios:
            metrics = await self.run_scenario(
                scenario_name=scenario["name"],
                endpoint=scenario["endpoint"],
                payload=scenario["payload"],
            )
            all_metrics.append(metrics)

            # 场景间休息2秒
            await asyncio.sleep(2)

        return all_metrics


def print_report(all_metrics: List[PerformanceMetrics]):
    """打印压测报告"""
    print("\n" + "=" * 80)
    print(" " * 25 + "压测报告")
    print("=" * 80 + "\n")

    for metrics in all_metrics:
        print(f"场景: {metrics.scenario_name}")
        print("-" * 80)
        print(f"  总请求数:     {metrics.total_requests}")
        print(f"  成功请求:     {metrics.successful_requests}")
        print(f"  失败请求:     {metrics.failed_requests}")
        print(f"  成功率:       {metrics.success_rate:.2f}%")
        print(f"  总耗时:       {metrics.duration:.2f}s")
        print(f"  QPS:          {metrics.qps:.2f} req/s")
        print(f"\n  延迟统计:")
        print(f"    最小值:     {metrics.min_latency * 1000:.2f}ms")
        print(f"    平均值:     {metrics.avg_latency * 1000:.2f}ms")
        print(f"    P50 (中位): {metrics.p50_latency * 1000:.2f}ms")
        print(f"    P95:        {metrics.p95_latency * 1000:.2f}ms")
        print(f"    P99:        {metrics.p99_latency * 1000:.2f}ms")
        print(f"    最大值:     {metrics.max_latency * 1000:.2f}ms")

        if metrics.errors:
            print(f"\n  错误示例 (前3条):")
            for error in metrics.errors[:3]:
                print(f"    - {error}")

        print("\n")

    # 生成JSON报告
    json_report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scenarios": [m.to_dict() for m in all_metrics],
    }

    report_path = "load_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print(f"[已保存] JSON报告: {report_path}")
    print("=" * 80 + "\n")


async def main():
    """主函数"""
    # 默认配置：10并发，100次请求
    config = LoadTestConfig(
        base_url="http://localhost:8000",
        concurrency=10,
        total_requests=100,
        timeout=30.0,
    )

    tester = LoadTester(config)

    print("\n" + "=" * 80)
    print(" " * 20 + "差旅管理系统 - 轻量级压测")
    print("=" * 80)
    print(f"\n[配置]")
    print(f"  基础URL:      {config.base_url}")
    print(f"  并发数:       {config.concurrency}")
    print(f"  总请求数:     {config.total_requests}")
    print(f"  超时时间:     {config.timeout}s")

    # 健康检查
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{config.base_url}/health", timeout=5.0)
            if response.status_code == 200:
                print(f"\n[检查] 服务健康 - {config.base_url}/health")
            else:
                print(f"\n[警告] 服务可能不可用 - HTTP {response.status_code}")
    except Exception as e:
        print(f"\n[错误] 无法连接到服务: {e}")
        print("请确保服务已启动：python -m src.api.main")
        return

    # 运行压测
    all_metrics = await tester.run_all_scenarios()

    # 打印报告
    print_report(all_metrics)


if __name__ == "__main__":
    asyncio.run(main())
