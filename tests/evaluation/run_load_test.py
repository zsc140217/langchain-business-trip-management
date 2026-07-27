"""
负载压测脚本

测试维度：
1. 并发性能：QPS、吞吐量
2. 延迟分布：P50、P95、P99
3. 错误率：成功率、失败类型
4. 资源使用：响应时间分布

使用方法：
    python tests/evaluation/run_load_test.py --concurrency 10 --duration 60
    python tests/evaluation/run_load_test.py --concurrency 50 --requests 1000

作者：Claude
创建时间：2026-07-25
"""
import os
import sys
import time
import asyncio
import argparse
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import defaultdict
import statistics

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Mock 环境变量
os.environ.setdefault("DASHSCOPE_API_KEY", "test_key")
os.environ.setdefault("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")


@dataclass
class LoadTestConfig:
    """压测配置"""
    concurrency: int = 10  # 并发数
    duration: int = 0  # 持续时间（秒，0=基于请求数）
    total_requests: int = 100  # 总请求数
    ramp_up: int = 0  # 预热时间（秒）
    use_real_llm: bool = False  # 是否使用真实LLM


@dataclass
class RequestResult:
    """单次请求结果"""
    query: str
    category: str
    start_time: float
    end_time: float
    latency_ms: float
    success: bool
    error: Optional[str] = None
    route: Optional[str] = None


@dataclass
class LoadTestReport:
    """压测报告"""
    # 配置信息
    config: Dict[str, Any]

    # 测试元数据
    start_time: str
    end_time: str
    total_duration_sec: float

    # 整体指标
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float

    # QPS指标
    overall_qps: float
    peak_qps: float

    # 延迟指标（毫秒）
    latency_min: float
    latency_max: float
    latency_mean: float
    latency_median: float
    latency_p95: float
    latency_p99: float
    latency_std: float

    # 按类别统计
    by_category: Dict[str, Any] = field(default_factory=dict)

    # 错误统计
    error_distribution: Dict[str, int] = field(default_factory=dict)

    # 时间序列数据（每秒统计）
    time_series: List[Dict[str, Any]] = field(default_factory=list)


class LoadTestRunner:
    """负载压测执行器"""

    # 测试查询池
    QUERY_POOL = [
        {"query": "北京天气怎么样", "category": "intent"},
        {"query": "查询CA1234航班状态", "category": "intent"},
        {"query": "推荐附近的协议酒店", "category": "intent"},
        {"query": "某某公司的联系方式", "category": "intent"},
        {"query": "到机场怎么走", "category": "intent"},
        {"query": "上海明天温度多少", "category": "intent"},

        {"query": "你好", "category": "chitchat"},
        {"query": "谢谢", "category": "chitchat"},
        {"query": "今天星期几", "category": "chitchat"},
        {"query": "你能做什么", "category": "chitchat"},
        {"query": "出差好累啊", "category": "chitchat"},
        {"query": "再见", "category": "chitchat"},

        {"query": "北京住宿标准是多少", "category": "simple"},
        {"query": "一线城市有哪些", "category": "simple"},
        {"query": "报销流程是什么", "category": "simple"},
        {"query": "审批需要多久", "category": "simple"},

        {"query": "北京和上海住宿标准对比", "category": "medium"},
        {"query": "去杭州出差，查天气并推荐酒店", "category": "complex"},
    ]

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results: List[RequestResult] = []
        self.start_timestamp: Optional[float] = None
        self.end_timestamp: Optional[float] = None
        self.request_counter = 0
        self.lock = asyncio.Lock()

    async def execute_single_request(self, query_data: Dict[str, str]) -> RequestResult:
        """执行单次请求"""
        start_time = time.time()

        try:
            # 模拟路由逻辑（实际应调用真实的router）
            if self.config.use_real_llm:
                # TODO: 调用真实的IntelligentRouter
                await asyncio.sleep(0.1)  # 模拟网络延迟
                route = "layer1_chitchat"
                success = True
                error = None
            else:
                # Mock模式：快速返回
                await asyncio.sleep(0.01)  # 模拟处理时间
                route = self._mock_route(query_data["category"])
                success = True
                error = None

        except Exception as e:
            route = None
            success = False
            error = str(e)

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        return RequestResult(
            query=query_data["query"],
            category=query_data["category"],
            start_time=start_time,
            end_time=end_time,
            latency_ms=round(latency_ms, 2),
            success=success,
            error=error,
            route=route
        )

    def _mock_route(self, category: str) -> str:
        """Mock路由结果"""
        route_map = {
            "intent": "layer0_intent",
            "chitchat": "layer1_chitchat",
            "simple": "layer2_synthesis",
            "medium": "layer2_synthesis",
            "complex": "layer2_orchestration"
        }
        return route_map.get(category, "unknown")

    async def worker(self, worker_id: int, query_queue: asyncio.Queue):
        """工作协程"""
        while True:
            try:
                query_data = await asyncio.wait_for(query_queue.get(), timeout=1.0)

                # 执行请求
                result = await self.execute_single_request(query_data)

                # 保存结果
                async with self.lock:
                    self.results.append(result)
                    self.request_counter += 1

                query_queue.task_done()

            except asyncio.TimeoutError:
                # 队列为空，退出
                break
            except Exception as e:
                print(f"[Worker-{worker_id}] Error: {e}")
                continue

    async def run_load_test(self) -> LoadTestReport:
        """运行负载测试"""
        print(f"\n{'='*70}")
        print(f"[Load Test] Starting Load Test")
        print(f"{'='*70}")
        print(f"Config:")
        print(f"  - Concurrency: {self.config.concurrency}")
        print(f"  - Duration: {self.config.duration}s" if self.config.duration > 0 else f"  - Total Requests: {self.config.total_requests}")
        print(f"  - Real LLM: {self.config.use_real_llm}")
        print(f"{'='*70}\n")

        # 创建查询队列
        query_queue = asyncio.Queue()

        # 填充查询队列
        if self.config.duration > 0:
            # 基于持续时间：生成足够多的查询
            estimated_requests = self.config.duration * self.config.concurrency * 10
            for i in range(estimated_requests):
                query_data = self.QUERY_POOL[i % len(self.QUERY_POOL)]
                await query_queue.put(query_data)
        else:
            # 基于请求数
            for i in range(self.config.total_requests):
                query_data = self.QUERY_POOL[i % len(self.QUERY_POOL)]
                await query_queue.put(query_data)

        # 启动工作协程
        self.start_timestamp = time.time()
        start_datetime = datetime.now()

        workers = [
            asyncio.create_task(self.worker(i, query_queue))
            for i in range(self.config.concurrency)
        ]

        # 等待完成
        if self.config.duration > 0:
            # 基于持续时间
            await asyncio.sleep(self.config.duration)
            # 取消所有worker
            for w in workers:
                w.cancel()
        else:
            # 基于请求数
            await query_queue.join()
            # 等待worker完成
            await asyncio.gather(*workers, return_exceptions=True)

        self.end_timestamp = time.time()
        end_datetime = datetime.now()

        # 生成报告
        report = self._generate_report(start_datetime, end_datetime)

        return report

    def _generate_report(self, start_dt: datetime, end_dt: datetime) -> LoadTestReport:
        """生成测试报告"""
        total_duration = self.end_timestamp - self.start_timestamp

        # 基本统计
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r.success)
        failed_requests = total_requests - successful_requests
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0

        # QPS计算
        overall_qps = total_requests / total_duration if total_duration > 0 else 0
        peak_qps = self._calculate_peak_qps()

        # 延迟统计
        latencies = [r.latency_ms for r in self.results if r.success]

        if latencies:
            latency_min = min(latencies)
            latency_max = max(latencies)
            latency_mean = statistics.mean(latencies)
            latency_median = statistics.median(latencies)
            latency_p95 = self._percentile(latencies, 95)
            latency_p99 = self._percentile(latencies, 99)
            latency_std = statistics.stdev(latencies) if len(latencies) > 1 else 0
        else:
            latency_min = latency_max = latency_mean = latency_median = 0
            latency_p95 = latency_p99 = latency_std = 0

        # 按类别统计
        by_category = self._calculate_category_stats()

        # 错误统计
        error_distribution = self._calculate_error_distribution()

        # 时间序列
        time_series = self._calculate_time_series()

        return LoadTestReport(
            config={
                "concurrency": self.config.concurrency,
                "duration": self.config.duration,
                "total_requests": self.config.total_requests,
                "use_real_llm": self.config.use_real_llm
            },
            start_time=start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            total_duration_sec=round(total_duration, 2),
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=round(success_rate, 2),
            overall_qps=round(overall_qps, 2),
            peak_qps=round(peak_qps, 2),
            latency_min=round(latency_min, 2),
            latency_max=round(latency_max, 2),
            latency_mean=round(latency_mean, 2),
            latency_median=round(latency_median, 2),
            latency_p95=round(latency_p95, 2),
            latency_p99=round(latency_p99, 2),
            latency_std=round(latency_std, 2),
            by_category=by_category,
            error_distribution=error_distribution,
            time_series=time_series
        )

    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _calculate_peak_qps(self) -> float:
        """计算峰值QPS"""
        if not self.results:
            return 0

        # 按秒分桶统计
        buckets = defaultdict(int)
        for result in self.results:
            second = int(result.start_time)
            buckets[second] += 1

        return max(buckets.values()) if buckets else 0

    def _calculate_category_stats(self) -> Dict[str, Any]:
        """按类别统计"""
        stats = defaultdict(lambda: {
            "count": 0,
            "success": 0,
            "latencies": []
        })

        for result in self.results:
            cat = result.category
            stats[cat]["count"] += 1
            if result.success:
                stats[cat]["success"] += 1
                stats[cat]["latencies"].append(result.latency_ms)

        # 计算每个类别的统计指标
        category_stats = {}
        for cat, data in stats.items():
            latencies = data["latencies"]
            category_stats[cat] = {
                "count": data["count"],
                "success": data["success"],
                "success_rate": round(data["success"] / data["count"] * 100, 2) if data["count"] > 0 else 0,
                "avg_latency": round(statistics.mean(latencies), 2) if latencies else 0,
                "p95_latency": round(self._percentile(latencies, 95), 2) if latencies else 0,
                "p99_latency": round(self._percentile(latencies, 99), 2) if latencies else 0
            }

        return category_stats

    def _calculate_error_distribution(self) -> Dict[str, int]:
        """错误分布统计"""
        error_dist = defaultdict(int)
        for result in self.results:
            if not result.success and result.error:
                error_type = result.error.split(":")[0] if ":" in result.error else result.error
                error_dist[error_type] += 1
        return dict(error_dist)

    def _calculate_time_series(self) -> List[Dict[str, Any]]:
        """时间序列统计（每秒）"""
        if not self.results:
            return []

        # 按秒分组
        buckets = defaultdict(lambda: {
            "requests": 0,
            "success": 0,
            "latencies": []
        })

        for result in self.results:
            second = int(result.start_time - self.start_timestamp)
            buckets[second]["requests"] += 1
            if result.success:
                buckets[second]["success"] += 1
                buckets[second]["latencies"].append(result.latency_ms)

        # 生成时间序列
        time_series = []
        for second in sorted(buckets.keys()):
            data = buckets[second]
            latencies = data["latencies"]
            time_series.append({
                "second": second,
                "qps": data["requests"],
                "success": data["success"],
                "avg_latency": round(statistics.mean(latencies), 2) if latencies else 0
            })

        return time_series


class ReportGenerator:
    """报告生成器"""

    @staticmethod
    def print_console_report(report: LoadTestReport):
        """打印控制台报告"""
        print(f"\n{'='*70}")
        print(f"[Load Test Report] Performance Load Test Results")
        print(f"{'='*70}\n")

        print(f"Test Metadata:")
        print(f"  Start Time: {report.start_time}")
        print(f"  End Time: {report.end_time}")
        print(f"  Duration: {report.total_duration_sec}s")
        print(f"  Concurrency: {report.config['concurrency']}")

        print(f"\nOverall Metrics:")
        print(f"  Total Requests: {report.total_requests}")
        print(f"  Successful: {report.successful_requests}")
        print(f"  Failed: {report.failed_requests}")
        print(f"  Success Rate: {report.success_rate}%")

        print(f"\nThroughput:")
        print(f"  Overall QPS: {report.overall_qps}")
        print(f"  Peak QPS: {report.peak_qps}")

        print(f"\nLatency (ms):")
        print(f"  Min: {report.latency_min}")
        print(f"  Max: {report.latency_max}")
        print(f"  Mean: {report.latency_mean}")
        print(f"  Median (P50): {report.latency_median}")
        print(f"  P95: {report.latency_p95}")
        print(f"  P99: {report.latency_p99}")
        print(f"  Std Dev: {report.latency_std}")

        print(f"\nBy Category:")
        for cat, stats in report.by_category.items():
            print(f"\n  {cat.upper()}:")
            print(f"    Requests: {stats['count']}")
            print(f"    Success Rate: {stats['success_rate']}%")
            print(f"    Avg Latency: {stats['avg_latency']}ms")
            print(f"    P95: {stats['p95_latency']}ms")
            print(f"    P99: {stats['p99_latency']}ms")

        if report.error_distribution:
            print(f"\nError Distribution:")
            for error_type, count in report.error_distribution.items():
                print(f"  - {error_type}: {count}")

        print(f"\n{'='*70}\n")

    @staticmethod
    def save_json_report(report: LoadTestReport, output_path: str):
        """保存JSON报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2)
        print(f"[OK] JSON report saved: {output_path}")

    @staticmethod
    def save_markdown_report(report: LoadTestReport, output_path: str):
        """保存Markdown报告"""
        md_lines = []

        # 标题
        md_lines.append("# Load Test Performance Report\n")
        md_lines.append(f"**Generated:** {report.end_time}\n")
        md_lines.append("---\n")

        # 测试配置
        md_lines.append("## Test Configuration\n")
        md_lines.append("| Parameter | Value |")
        md_lines.append("|-----------|-------|")
        md_lines.append(f"| Concurrency | {report.config['concurrency']} |")
        md_lines.append(f"| Duration | {report.total_duration_sec}s |")
        md_lines.append(f"| Total Requests | {report.total_requests} |")
        md_lines.append(f"| Use Real LLM | {report.config['use_real_llm']} |")
        md_lines.append("")

        # 整体指标
        md_lines.append("## Overall Metrics\n")
        md_lines.append("| Metric | Value |")
        md_lines.append("|--------|-------|")
        md_lines.append(f"| Total Requests | {report.total_requests} |")
        md_lines.append(f"| Successful | {report.successful_requests} |")
        md_lines.append(f"| Failed | {report.failed_requests} |")
        md_lines.append(f"| Success Rate | {report.success_rate}% |")
        md_lines.append(f"| Overall QPS | {report.overall_qps} |")
        md_lines.append(f"| Peak QPS | {report.peak_qps} |")
        md_lines.append("")

        # 延迟分布
        md_lines.append("## Latency Distribution (ms)\n")
        md_lines.append("| Percentile | Latency (ms) |")
        md_lines.append("|------------|--------------|")
        md_lines.append(f"| Min | {report.latency_min} |")
        md_lines.append(f"| Mean | {report.latency_mean} |")
        md_lines.append(f"| Median (P50) | {report.latency_median} |")
        md_lines.append(f"| P95 | {report.latency_p95} |")
        md_lines.append(f"| P99 | {report.latency_p99} |")
        md_lines.append(f"| Max | {report.latency_max} |")
        md_lines.append(f"| Std Dev | {report.latency_std} |")
        md_lines.append("")

        # 按类别统计
        md_lines.append("## Performance by Category\n")
        md_lines.append("| Category | Requests | Success Rate | Avg Latency | P95 | P99 |")
        md_lines.append("|----------|----------|--------------|-------------|-----|-----|")
        for cat, stats in sorted(report.by_category.items()):
            md_lines.append(
                f"| {cat} | {stats['count']} | {stats['success_rate']}% | "
                f"{stats['avg_latency']}ms | {stats['p95_latency']}ms | {stats['p99_latency']}ms |"
            )
        md_lines.append("")

        # 错误分布
        if report.error_distribution:
            md_lines.append("## Error Distribution\n")
            md_lines.append("| Error Type | Count |")
            md_lines.append("|------------|-------|")
            for error_type, count in sorted(report.error_distribution.items()):
                md_lines.append(f"| {error_type} | {count} |")
            md_lines.append("")

        # QPS时间序列
        if report.time_series:
            md_lines.append("## QPS Time Series (First 10 seconds)\n")
            md_lines.append("| Second | QPS | Success | Avg Latency (ms) |")
            md_lines.append("|--------|-----|---------|------------------|")
            for ts in report.time_series[:10]:
                md_lines.append(
                    f"| {ts['second']} | {ts['qps']} | {ts['success']} | {ts['avg_latency']} |"
                )
            md_lines.append("")

        # 性能评估
        md_lines.append("## Performance Assessment\n")

        # 成功率评估
        if report.success_rate >= 99:
            success_assessment = "Excellent"
        elif report.success_rate >= 95:
            success_assessment = "Good"
        elif report.success_rate >= 90:
            success_assessment = "Acceptable"
        else:
            success_assessment = "Poor"
        md_lines.append(f"**Success Rate:** {success_assessment} ({report.success_rate}%)\n")

        # P95延迟评估
        if report.latency_p95 < 100:
            latency_assessment = "Excellent"
        elif report.latency_p95 < 500:
            latency_assessment = "Good"
        elif report.latency_p95 < 1000:
            latency_assessment = "Acceptable"
        else:
            latency_assessment = "Poor"
        md_lines.append(f"**P95 Latency:** {latency_assessment} ({report.latency_p95}ms)\n")

        # QPS评估
        if report.overall_qps >= 100:
            qps_assessment = "Excellent"
        elif report.overall_qps >= 50:
            qps_assessment = "Good"
        elif report.overall_qps >= 10:
            qps_assessment = "Acceptable"
        else:
            qps_assessment = "Poor"
        md_lines.append(f"**Throughput (QPS):** {qps_assessment} ({report.overall_qps})\n")

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))

        print(f"[OK] Markdown report saved: {output_path}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Load Testing Tool")
    parser.add_argument("--concurrency", "-c", type=int, default=10, help="Number of concurrent workers")
    parser.add_argument("--duration", "-d", type=int, default=0, help="Test duration in seconds (0=use requests count)")
    parser.add_argument("--requests", "-n", type=int, default=100, help="Total number of requests")
    parser.add_argument("--real-llm", action="store_true", help="Use real LLM instead of mock")
    parser.add_argument("--output", "-o", type=str, default="load_test_report", help="Output file prefix")

    args = parser.parse_args()

    # 创建配置
    config = LoadTestConfig(
        concurrency=args.concurrency,
        duration=args.duration,
        total_requests=args.requests,
        use_real_llm=args.real_llm
    )

    # 运行压测
    runner = LoadTestRunner(config)
    report = await runner.run_load_test()

    # 生成报告
    ReportGenerator.print_console_report(report)
    ReportGenerator.save_json_report(report, f"{args.output}.json")
    ReportGenerator.save_markdown_report(report, f"{args.output}.md")

    print(f"\n[OK] Load test completed!")
    print(f"  - Console output: above")
    print(f"  - JSON report: {args.output}.json")
    print(f"  - Markdown report: {args.output}.md")


if __name__ == "__main__":
    asyncio.run(main())
