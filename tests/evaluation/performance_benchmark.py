"""
三层路由架构性能基准测试

测试维度：
1. 响应延迟（各层平均延迟）
2. 路由分布（各层拦截占比）
3. 准确率（工具调用成功率）
4. 成本对比（LLM调用次数）

作者：Claude
创建时间：2026-06-28
"""
import os
import sys
import time
import json
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from unittest.mock import Mock, patch
from langchain_core.documents import Document

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock 环境变量
os.environ.setdefault("DASHSCOPE_API_KEY", "test_key")
os.environ.setdefault("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

from src.agents.intelligent_router import IntelligentRouter
from src.models.llm import get_llm


@dataclass
class TestQuery:
    """测试查询"""
    query: str
    expected_layer: str  # layer0_intent, layer1_rag, layer2_synthesis, layer2_orchestration
    category: str  # intent, chitchat, simple, medium, complex
    description: str


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    query: str
    category: str
    expected_layer: str
    actual_route: str
    latency_ms: float
    llm_calls: int
    success: bool
    error: str = None


class PerformanceBenchmark:
    """性能基准测试"""

    # 测试数据集（20条查询）
    TEST_DATASET = [
        # 第零层（工具调用）- 6条
        TestQuery("北京天气怎么样", "layer0_intent", "intent", "明确天气查询意图"),
        TestQuery("查询CA1234航班状态", "layer0_intent", "intent", "明确航班查询意图"),
        TestQuery("推荐附近的协议酒店", "layer0_intent", "intent", "明确酒店查询意图"),
        TestQuery("某某公司的联系方式", "layer0_intent", "intent", "明确客户信息查询"),
        TestQuery("到机场怎么走", "layer0_intent", "intent", "明确路线查询"),
        TestQuery("上海明天温度多少", "layer0_intent", "intent", "明确天气查询"),

        # 第一层（闲聊）- 8条
        TestQuery("你好", "layer1_chitchat", "chitchat", "简单问候"),
        TestQuery("谢谢", "layer1_chitchat", "chitchat", "感谢"),
        TestQuery("今天星期几", "layer1_chitchat", "chitchat", "通用知识"),
        TestQuery("你能做什么", "layer1_chitchat", "chitchat", "系统功能"),
        TestQuery("出差好累啊", "layer1_chitchat", "chitchat", "闲聊感受"),
        TestQuery("再见", "layer1_chitchat", "chitchat", "告别"),
        TestQuery("不客气", "layer1_chitchat", "chitchat", "礼貌回应"),
        TestQuery("早上好", "layer1_chitchat", "chitchat", "问候"),

        # 第二层SIMPLE（简单RAG）- 4条
        TestQuery("北京住宿标准是多少", "layer2_synthesis", "simple", "单一政策查询"),
        TestQuery("一线城市有哪些", "layer2_synthesis", "simple", "分类定义查询"),
        TestQuery("报销流程是什么", "layer2_synthesis", "simple", "流程查询"),
        TestQuery("审批需要多久", "layer2_synthesis", "simple", "时效查询"),

        # 第二层MEDIUM（中等复杂）- 1条
        TestQuery("北京和上海住宿标准对比", "layer2_synthesis", "medium", "对比查询"),

        # 第二层COMPLEX（复杂任务）- 1条
        TestQuery("去杭州出差，查天气并推荐酒店", "layer2_orchestration", "complex", "多意图组合"),
    ]

    def __init__(self, use_real_llm: bool = False):
        """
        初始化基准测试

        Args:
            use_real_llm: 是否使用真实LLM（False=Mock，True=真实API）
        """
        self.use_real_llm = use_real_llm
        self.results: List[BenchmarkResult] = []

    def _create_router(self) -> IntelligentRouter:
        """创建路由器实例"""
        if self.use_real_llm:
            # 使用真实LLM和检索器
            llm = get_llm(temperature=0.3)
            # TODO: 加载真实的retriever和rag_chain
            from src.rag.retriever import get_retriever
            from src.rag.chain import create_rag_chain

            retriever = get_retriever()
            rag_chain = create_rag_chain(llm, retriever)
            tools = {}  # TODO: 加载真实工具
        else:
            # 使用Mock组件
            llm = Mock()
            retriever = Mock()
            rag_chain = Mock()
            tools = {}

            # Mock retriever返回
            retriever.get_relevant_documents.return_value = [
                Document(page_content="一线城市住宿标准500元/晚", metadata={"source": "policy.txt"})
            ]

        router = IntelligentRouter(
            llm=llm,
            retriever=retriever,
            rag_chain=rag_chain,
            tools=tools
        )

        return router

    def _mock_llm_responses(self, router: IntelligentRouter, test: TestQuery):
        """为Mock场景配置LLM响应"""
        if self.use_real_llm:
            return None

        # Mock synthesis layer响应
        if test.category == "intent":
            synthesis_response = {
                "complete": True,
                "confidence": 0.95,
                "answer": f"根据查询结果：{test.query}",
                "reasoning": "基于工具调用结果",
                "next_action": None
            }
        elif test.category == "chitchat":
            synthesis_response = {
                "complete": True,
                "confidence": 0.9,
                "answer": "您好！",
                "reasoning": "闲聊回应",
                "next_action": None
            }
        else:
            synthesis_response = {
                "complete": True,
                "confidence": 0.85,
                "answer": f"根据政策文档：{test.query}的答案",
                "reasoning": "基于RAG文档",
                "next_action": None
            }

        return patch.object(router.synthesis_layer, 'synthesize', return_value=synthesis_response)

    def run_single_test(self, test: TestQuery) -> BenchmarkResult:
        """运行单个测试"""
        router = self._create_router()

        try:
            start_time = time.time()

            # 配置Mock响应
            patcher = self._mock_llm_responses(router, test)
            if patcher:
                patcher.start()

            # 执行路由
            result = router.route(test.query)

            if patcher:
                patcher.stop()

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            # 统计LLM调用次数（从统计信息获取）
            llm_calls = 0
            if hasattr(router, 'stats'):
                llm_calls = router.stats.get('llm_calls', 0)

            # 判断成功
            actual_route = result.get("route", "unknown")
            success = self._check_success(test, actual_route)

            return BenchmarkResult(
                query=test.query,
                category=test.category,
                expected_layer=test.expected_layer,
                actual_route=actual_route,
                latency_ms=round(latency_ms, 2),
                llm_calls=llm_calls,
                success=success
            )

        except Exception as e:
            return BenchmarkResult(
                query=test.query,
                category=test.category,
                expected_layer=test.expected_layer,
                actual_route="error",
                latency_ms=0,
                llm_calls=0,
                success=False,
                error=str(e)
            )

    def _check_success(self, test: TestQuery, actual_route: str) -> bool:
        """检查路由是否成功"""
        # 简化判断：检查关键词
        if test.expected_layer == "layer0_intent" and "intent" in actual_route:
            return True
        if test.expected_layer == "layer1_chitchat" and "chitchat" in actual_route:
            return True
        if test.expected_layer == "layer2_synthesis" and "synthesis" in actual_route:
            return True
        if test.expected_layer == "layer2_orchestration" and "orchestration" in actual_route:
            return True
        return False

    def run_all_tests(self) -> List[BenchmarkResult]:
        """运行所有测试"""
        self.results = []

        for i, test in enumerate(self.TEST_DATASET, 1):
            result = self.run_single_test(test)
            self.results.append(result)

        return self.results

    def analyze_results(self) -> Dict[str, Any]:
        """分析测试结果"""
        total = len(self.results)
        success_count = sum(1 for r in self.results if r.success)

        # 按类别分组统计
        by_category = {}
        for result in self.results:
            cat = result.category
            if cat not in by_category:
                by_category[cat] = {
                    "count": 0,
                    "success": 0,
                    "total_latency": 0,
                    "avg_latency": 0
                }

            by_category[cat]["count"] += 1
            if result.success:
                by_category[cat]["success"] += 1
            by_category[cat]["total_latency"] += result.latency_ms

        # 计算平均延迟
        for cat in by_category:
            count = by_category[cat]["count"]
            by_category[cat]["avg_latency"] = round(
                by_category[cat]["total_latency"] / count, 2
            )

        # 总体统计
        total_latency = sum(r.latency_ms for r in self.results)
        avg_latency = round(total_latency / total, 2) if total > 0 else 0

        analysis = {
            "total_queries": total,
            "success_count": success_count,
            "success_rate": round(success_count / total * 100, 2) if total > 0 else 0,
            "avg_latency_ms": avg_latency,
            "by_category": by_category
        }

        return analysis

    def print_report(self):
        """打印性能报告"""
        analysis = self.analyze_results()

        print(f"\n{'='*70}")
        print(f"[性能报告] 性能基准测试报告")
        print(f"{'='*70}\n")

        print(f"总体统计:")
        print(f"  - 测试查询数: {analysis['total_queries']}")
        print(f"  - 成功数: {analysis['success_count']}")
        print(f"  - 成功率: {analysis['success_rate']}%")
        print(f"  - 平均延迟: {analysis['avg_latency_ms']}ms")

        print(f"\n按类别统计:")
        for cat, stats in analysis['by_category'].items():
            success_rate = round(stats['success'] / stats['count'] * 100, 2)
            print(f"\n  {cat.upper()}:")
            print(f"    - 查询数: {stats['count']}")
            print(f"    - 成功数: {stats['success']}")
            print(f"    - 成功率: {success_rate}%")
            print(f"    - 平均延迟: {stats['avg_latency']}ms")

        print(f"\n{'='*70}\n")

    def save_report(self, output_path: str = "performance_report.json"):
        """保存报告为JSON"""
        analysis = self.analyze_results()

        report = {
            "metadata": {
                "test_mode": "real_llm" if self.use_real_llm else "mock",
                "test_count": len(self.results),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "analysis": analysis,
            "details": [asdict(r) for r in self.results]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"[OK] 报告已保存: {output_path}")


def main():
    """主函数"""
    benchmark_mock = PerformanceBenchmark(use_real_llm=False)
    benchmark_mock.run_all_tests()
    benchmark_mock.print_report()
    benchmark_mock.save_report("performance_report_mock.json")


if __name__ == "__main__":
    main()
