"""
推理能力与工具使用能力评测 - 统一入口
专注于评估系统的推理链路和工具调用能力
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.evaluation.evaluators.reasoning_evaluator import run_reasoning_evaluation
from tests.evaluation.evaluators.tool_evaluator import run_tool_evaluation
from tests.evaluation.evaluators.cost_tracker import get_tracker


class ReasoningToolEvaluator:
    """推理能力与工具使用能力评测执行器"""

    def __init__(self):
        self.test_data_dir = Path(__file__).parent / 'test_data'
        self.reports_dir = Path(__file__).parent / 'reports' / 'comprehensive'
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.tracker = get_tracker()

    async def run_full_evaluation(self):
        """运行完整评测流程"""
        print("=" * 70)
        print("差旅报销系统 - 推理能力与工具使用能力评测")
        print(f"评测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        results = {}

        # Phase 1: 简单推理评估
        print("\n[Phase 1/4] 简单推理能力评估...")
        results['simple_reasoning'] = await self._run_simple_reasoning()

        # Phase 2: 复杂推理评估
        print("\n[Phase 2/4] 复杂推理能力评估...")
        results['complex_reasoning'] = await self._run_complex_reasoning()

        # Phase 3: 工具使用评估
        print("\n[Phase 3/4] 工具使用能力评估...")
        results['tool_usage'] = await self._run_tool_usage()

        # Phase 4: 生成综合报告
        print("\n[Phase 4/4] 生成综合报告...")
        report_path = self._generate_comprehensive_report(results)

        # 打印成本汇总
        self._print_cost_summary()

        print(f"\n[SUCCESS] 评测完成！")
        print(f"[REPORT] 报告已保存: {report_path}")

        return results

    async def _run_simple_reasoning(self) -> Dict:
        """运行简单推理评估"""
        test_data_path = self.test_data_dir / 'reasoning_simple.json'

        # 1. 收集系统响应
        print("  收集系统响应...")
        responses = await self._collect_system_responses(test_data_path)

        # 2. 运行评估
        print("  执行评估...")
        results = run_reasoning_evaluation(
            str(test_data_path),
            responses,
            evaluator_type='simple'
        )

        # 3. 统计
        stats = self._calculate_statistics(results)
        print(f"  平均分: {stats['avg_score']:.2f}/5")
        print(f"  通过率: {stats['pass_rate']:.1%}")

        return {
            'results': results,
            'statistics': stats
        }

    async def _run_complex_reasoning(self) -> Dict:
        """运行复杂推理评估"""
        test_data_path = self.test_data_dir / 'reasoning_complex.json'

        print("  收集系统响应...")
        responses = await self._collect_system_responses(test_data_path)

        print("  执行评估...")
        results = run_reasoning_evaluation(
            str(test_data_path),
            responses,
            evaluator_type='complex'
        )

        stats = self._calculate_statistics(results)
        print(f"  平均分: {stats['avg_score']:.2f}/5")
        print(f"  通过率: {stats['pass_rate']:.1%}")

        return {
            'results': results,
            'statistics': stats
        }

    async def _run_tool_usage(self) -> Dict:
        """运行工具使用评估"""
        test_data_path = self.test_data_dir / 'tool_usage.json'

        print("  收集系统响应...")
        responses = await self._collect_system_responses(test_data_path)

        print("  执行评估...")
        results = run_tool_evaluation(
            str(test_data_path),
            responses
        )

        stats = self._calculate_statistics(results)
        print(f"  平均分: {stats['avg_score']:.2f}/5")
        print(f"  通过率: {stats['pass_rate']:.1%}")

        return {
            'results': results,
            'statistics': stats
        }

    async def _collect_system_responses(
        self,
        test_data_path: Path
    ) -> List[Dict]:
        """
        收集系统响应 - 调用实际业务系统API
        """
        import requests
        import time

        # 加载测试用例
        with open(test_data_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)

        test_cases = test_data['test_cases']

        # 业务系统API地址
        api_url = 'http://localhost:8000/api/chat/sync'

        responses = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"    [{i}/{len(test_cases)}] 测试: {test_case['id']}")

            try:
                # 记录开始时间
                start_time = time.time()

                # 调用实际API
                api_response = requests.post(
                    api_url,
                    json={'question': test_case['query']},
                    timeout=30
                )

                # 计算响应时间
                latency_ms = int((time.time() - start_time) * 1000)

                if api_response.status_code == 200:
                    result = api_response.json()

                    response = {
                        'test_id': test_case['id'],
                        'answer': result.get('answer', ''),
                        'latency_ms': latency_ms,
                        'tool_calls': result.get('tool_calls', []),
                        'retrieved_docs': result.get('retrieved_docs', [])
                    }
                else:
                    print(f"      警告: API返回错误 {api_response.status_code}")
                    response = {
                        'test_id': test_case['id'],
                        'answer': f"API错误: {api_response.status_code}",
                        'latency_ms': latency_ms,
                        'tool_calls': [],
                        'retrieved_docs': []
                    }

            except requests.exceptions.ConnectionError:
                print(f"      错误: 无法连接到业务系统API ({api_url})")
                print(f"      请确保业务系统正在运行")
                response = {
                    'test_id': test_case['id'],
                    'answer': "系统未启动",
                    'latency_ms': 0,
                    'tool_calls': [],
                    'retrieved_docs': []
                }
            except Exception as e:
                print(f"      错误: {str(e)}")
                response = {
                    'test_id': test_case['id'],
                    'answer': f"调用失败: {str(e)}",
                    'latency_ms': 0,
                    'tool_calls': [],
                    'retrieved_docs': []
                }

            responses.append(response)

        return responses

    def _calculate_statistics(self, results: List) -> Dict:
        """计算统计数据"""
        if not results:
            return {
                'total': 0,
                'avg_score': 0,
                'pass_rate': 0,
                'needs_review_count': 0
            }

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        needs_review = sum(1 for r in results if r.needs_review)

        avg_score = sum(r.overall_score for r in results) / total

        return {
            'total': total,
            'passed': passed,
            'avg_score': avg_score,
            'pass_rate': passed / total,
            'needs_review_count': needs_review
        }

    def _generate_comprehensive_report(self, results: Dict) -> str:
        """生成综合报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.reports_dir / f'reasoning_tool_evaluation_{timestamp}.md'

        # 生成Markdown报告
        report_content = self._format_markdown_report(results)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        # 导出成本详情
        cost_path = self.reports_dir / f'cost_details_{timestamp}.json'
        self.tracker.export_to_file(str(cost_path))

        return str(report_path)

    def _format_markdown_report(self, results: Dict) -> str:
        """格式化Markdown报告"""
        lines = []

        lines.append("# 差旅报销系统 - 推理能力与工具使用能力评测报告")
        lines.append("")
        lines.append(f"**评测时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 总体概览
        lines.append("## 一、总体概览")
        lines.append("")

        total_cases = sum(
            r['statistics']['total']
            for r in results.values()
        )

        lines.append(f"- **总测试用例数**: {total_cases}条")
        lines.append(f"- **评测成本**: ¥{self.tracker.get_summary()['total_cost_cny']}")
        lines.append("")

        # 分维度评分
        lines.append("## 二、分维度评分")
        lines.append("")
        lines.append("| 维度 | 平均分 | 通过率 | 需Review |")
        lines.append("|------|--------|--------|----------|")

        for key, result in results.items():
            stats = result['statistics']
            lines.append(
                f"| {key} | {stats['avg_score']:.2f}/5 | "
                f"{stats['pass_rate']:.1%} | {stats['needs_review_count']}条 |"
            )

        lines.append("")

        # Bad Case列表
        lines.append("## 三、需要Review的Case")
        lines.append("")

        for key, result in results.items():
            bad_cases = [
                r for r in result['results']
                if r.needs_review
            ]

            if bad_cases:
                lines.append(f"### {key}")
                lines.append("")
                for case in bad_cases[:5]:  # 只显示前5个
                    lines.append(f"**{case.test_id}**: {case.query}")
                    lines.append(f"- 得分: {case.overall_score:.2f}/5")
                    # 兼容不同类型的结果对象
                    detail = getattr(case, 'evaluation_detail', None) or getattr(case, 'reasoning_detail', '')
                    lines.append(f"- 原因: {detail[:100]}")
                    lines.append("")

        # 成本分析
        lines.append("## 四、成本分析")
        lines.append("")

        cost_summary = self.tracker.get_summary()
        lines.append(f"- **总调用次数**: {cost_summary['total_calls']}次")
        lines.append(f"- **总Token消耗**: {cost_summary['total_tokens']:,} tokens")
        lines.append(f"- **总成本**: ¥{cost_summary['total_cost_cny']}")
        if total_cases > 0:
            lines.append(f"- **单用例成本**: ¥{cost_summary['total_cost_cny']/total_cases:.3f}")
        lines.append("")

        return "\n".join(lines)

    def _print_cost_summary(self):
        """打印成本汇总"""
        summary = self.tracker.get_summary()

        print("\n" + "=" * 70)
        print("成本汇总")
        print("=" * 70)
        print(f"总调用次数: {summary['total_calls']}次")
        print(f"总Token消耗: {summary['total_tokens']:,} tokens")
        print(f"  - 输入: {summary['input_tokens']:,} tokens")
        print(f"  - 输出: {summary['output_tokens']:,} tokens")
        print(f"总成本: CNY {summary['total_cost_cny']}")
        if summary['total_calls'] > 0:
            print(f"平均每次调用: CNY {summary['avg_cost_per_call']}")
        print("=" * 70)


async def main():
    """主函数"""
    evaluator = ReasoningToolEvaluator()
    await evaluator.run_full_evaluation()


if __name__ == '__main__':
    asyncio.run(main())
