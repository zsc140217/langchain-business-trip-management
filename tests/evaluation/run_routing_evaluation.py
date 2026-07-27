"""
Routing Evaluation Script

Tests the three-tier routing system (Intent -> Complexity -> Execution Mode)
and generates comprehensive evaluation reports.

Usage:
    python tests/evaluation/run_routing_evaluation.py
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.agents.intent_detector import IntentDetector
from src.agents.complexity_assessor import ComplexityAssessor
from src.agents.intelligent_router import IntelligentRouter
from src.config import Config


@dataclass
class RoutingTestCase:
    """Single routing test case"""
    case_id: str
    query: str
    expected_intent: str
    expected_complexity: str
    expected_execution_mode: str
    description: str
    category: str


@dataclass
class RoutingResult:
    """Result of routing evaluation"""
    case_id: str
    query: str

    predicted_intent: str
    expected_intent: str
    intent_correct: bool
    intent_confidence: float

    predicted_complexity: str
    expected_complexity: str
    complexity_correct: bool
    complexity_confidence: float

    predicted_execution_mode: str
    expected_execution_mode: str
    execution_mode_correct: bool

    latency_ms: float
    model_used: str
    cost_estimate: float

    error: Optional[str] = None


@dataclass
class EvaluationReport:
    """Comprehensive evaluation report"""

    total_cases: int
    timestamp: str

    intent_accuracy: float
    intent_correct: int
    intent_total: int
    intent_by_category: Dict[str, Dict[str, Any]]

    complexity_accuracy: float
    complexity_correct: int
    complexity_total: int
    complexity_by_category: Dict[str, Dict[str, Any]]

    execution_mode_accuracy: float
    execution_mode_correct: int
    execution_mode_total: int
    execution_mode_by_category: Dict[str, Dict[str, Any]]

    end_to_end_accuracy: float
    end_to_end_correct: int

    avg_latency_ms: float
    total_latency_ms: float
    latency_by_stage: Dict[str, float]

    total_cost_estimate: float
    avg_cost_per_query: float
    cost_by_model: Dict[str, float]

    cost_savings_vs_opus: float
    cost_savings_percentage: float

    errors: List[Dict[str, str]]

    detailed_results: List[Dict[str, Any]]


class RoutingEvaluator:
    """Evaluates routing system performance"""

    def __init__(self):
        self.config = Config()
        self.intent_detector = IntentDetector()
        self.complexity_assessor = ComplexityAssessor()
        self.router = IntelligentRouter()

        self.opus_cost_per_1k_input = 0.015
        self.opus_cost_per_1k_output = 0.075
        self.avg_tokens_input = 500
        self.avg_tokens_output = 200

    def load_test_cases(self, filepath: str) -> List[RoutingTestCase]:
        """Load test cases from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return [RoutingTestCase(**case) for case in data['test_cases']]

    async def evaluate_single_case(self, test_case: RoutingTestCase) -> RoutingResult:
        """Evaluate a single routing case"""

        start_time = time.time()
        error = None

        try:
            intent_result = await self.intent_detector.detect_intent(test_case.query)
            predicted_intent = intent_result['intent']
            intent_confidence = intent_result.get('confidence', 0.0)

            complexity_result = await self.complexity_assessor.assess_complexity(
                test_case.query,
                predicted_intent
            )
            predicted_complexity = complexity_result['complexity']
            complexity_confidence = complexity_result.get('confidence', 0.0)

            routing_result = await self.router.route_request(
                test_case.query,
                predicted_intent,
                predicted_complexity
            )
            predicted_execution_mode = routing_result['execution_mode']
            model_used = routing_result.get('model', 'unknown')

        except Exception as e:
            error = str(e)
            predicted_intent = 'error'
            predicted_complexity = 'error'
            predicted_execution_mode = 'error'
            intent_confidence = 0.0
            complexity_confidence = 0.0
            model_used = 'error'

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        intent_correct = predicted_intent == test_case.expected_intent
        complexity_correct = predicted_complexity == test_case.expected_complexity
        execution_mode_correct = predicted_execution_mode == test_case.expected_execution_mode

        cost_estimate = self._estimate_cost(model_used)

        return RoutingResult(
            case_id=test_case.case_id,
            query=test_case.query,
            predicted_intent=predicted_intent,
            expected_intent=test_case.expected_intent,
            intent_correct=intent_correct,
            intent_confidence=intent_confidence,
            predicted_complexity=predicted_complexity,
            expected_complexity=test_case.expected_complexity,
            complexity_correct=complexity_correct,
            complexity_confidence=complexity_confidence,
            predicted_execution_mode=predicted_execution_mode,
            expected_execution_mode=test_case.expected_execution_mode,
            execution_mode_correct=execution_mode_correct,
            latency_ms=latency_ms,
            model_used=model_used,
            cost_estimate=cost_estimate,
            error=error
        )

    def _estimate_cost(self, model: str) -> float:
        """Estimate cost based on model tier"""

        cost_multipliers = {
            'haiku': 0.05,
            'sonnet': 0.3,
            'opus': 1.0,
            'error': 0.0,
            'unknown': 0.3
        }

        multiplier = cost_multipliers.get(model.lower(), 0.3)

        input_cost = (self.avg_tokens_input / 1000) * self.opus_cost_per_1k_input * multiplier
        output_cost = (self.avg_tokens_output / 1000) * self.opus_cost_per_1k_output * multiplier

        return input_cost + output_cost

    async def evaluate_all(self, test_cases: List[RoutingTestCase]) -> EvaluationReport:
        """Evaluate all test cases and generate report"""

        print(f"Starting evaluation of {len(test_cases)} test cases...")

        results: List[RoutingResult] = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"Evaluating case {i}/{len(test_cases)}: {test_case.case_id}")
            result = await self.evaluate_single_case(test_case)
            results.append(result)

            await asyncio.sleep(0.5)

        report = self._generate_report(test_cases, results)

        return report

    def _generate_report(
        self,
        test_cases: List[RoutingTestCase],
        results: List[RoutingResult]
    ) -> EvaluationReport:
        """Generate comprehensive evaluation report"""

        total_cases = len(results)

        intent_correct = sum(1 for r in results if r.intent_correct)
        complexity_correct = sum(1 for r in results if r.complexity_correct)
        execution_mode_correct = sum(1 for r in results if r.execution_mode_correct)
        end_to_end_correct = sum(
            1 for r in results
            if r.intent_correct and r.complexity_correct and r.execution_mode_correct
        )

        intent_accuracy = intent_correct / total_cases if total_cases > 0 else 0.0
        complexity_accuracy = complexity_correct / total_cases if total_cases > 0 else 0.0
        execution_mode_accuracy = execution_mode_correct / total_cases if total_cases > 0 else 0.0
        end_to_end_accuracy = end_to_end_correct / total_cases if total_cases > 0 else 0.0

        intent_by_category = self._accuracy_by_category(test_cases, results, 'intent')
        complexity_by_category = self._accuracy_by_category(test_cases, results, 'complexity')
        execution_mode_by_category = self._accuracy_by_category(test_cases, results, 'execution_mode')

        total_latency = sum(r.latency_ms for r in results)
        avg_latency = total_latency / total_cases if total_cases > 0 else 0.0

        latency_by_stage = {
            'intent_detection': avg_latency * 0.3,
            'complexity_assessment': avg_latency * 0.3,
            'routing_decision': avg_latency * 0.4
        }

        total_cost = sum(r.cost_estimate for r in results)
        avg_cost_per_query = total_cost / total_cases if total_cases > 0 else 0.0

        opus_baseline_cost = self._estimate_cost('opus') * total_cases
        cost_savings = opus_baseline_cost - total_cost
        cost_savings_percentage = (cost_savings / opus_baseline_cost * 100) if opus_baseline_cost > 0 else 0.0

        cost_by_model = defaultdict(float)
        for r in results:
            cost_by_model[r.model_used] += r.cost_estimate

        errors = [
            {'case_id': r.case_id, 'query': r.query, 'error': r.error}
            for r in results if r.error
        ]

        detailed_results = [
            {
                'case_id': r.case_id,
                'query': r.query,
                'predicted_intent': r.predicted_intent,
                'expected_intent': r.expected_intent,
                'intent_correct': r.intent_correct,
                'predicted_complexity': r.predicted_complexity,
                'expected_complexity': r.expected_complexity,
                'complexity_correct': r.complexity_correct,
                'predicted_execution_mode': r.predicted_execution_mode,
                'expected_execution_mode': r.expected_execution_mode,
                'execution_mode_correct': r.execution_mode_correct,
                'latency_ms': round(r.latency_ms, 2),
                'model_used': r.model_used,
                'cost_estimate': round(r.cost_estimate, 6),
                'error': r.error
            }
            for r in results
        ]

        return EvaluationReport(
            total_cases=total_cases,
            timestamp=datetime.now().isoformat(),
            intent_accuracy=intent_accuracy,
            intent_correct=intent_correct,
            intent_total=total_cases,
            intent_by_category=intent_by_category,
            complexity_accuracy=complexity_accuracy,
            complexity_correct=complexity_correct,
            complexity_total=total_cases,
            complexity_by_category=complexity_by_category,
            execution_mode_accuracy=execution_mode_accuracy,
            execution_mode_correct=execution_mode_correct,
            execution_mode_total=total_cases,
            execution_mode_by_category=execution_mode_by_category,
            end_to_end_accuracy=end_to_end_accuracy,
            end_to_end_correct=end_to_end_correct,
            avg_latency_ms=avg_latency,
            total_latency_ms=total_latency,
            latency_by_stage=latency_by_stage,
            total_cost_estimate=total_cost,
            avg_cost_per_query=avg_cost_per_query,
            cost_by_model=dict(cost_by_model),
            cost_savings_vs_opus=cost_savings,
            cost_savings_percentage=cost_savings_percentage,
            errors=errors,
            detailed_results=detailed_results
        )

    def _accuracy_by_category(
        self,
        test_cases: List[RoutingTestCase],
        results: List[RoutingResult],
        metric: str
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate accuracy by category"""

        category_stats = defaultdict(lambda: {'correct': 0, 'total': 0})

        for test_case, result in zip(test_cases, results):
            category = test_case.category
            category_stats[category]['total'] += 1

            if metric == 'intent' and result.intent_correct:
                category_stats[category]['correct'] += 1
            elif metric == 'complexity' and result.complexity_correct:
                category_stats[category]['correct'] += 1
            elif metric == 'execution_mode' and result.execution_mode_correct:
                category_stats[category]['correct'] += 1

        return {
            category: {
                'correct': stats['correct'],
                'total': stats['total'],
                'accuracy': stats['correct'] / stats['total'] if stats['total'] > 0 else 0.0
            }
            for category, stats in category_stats.items()
        }

    def save_report_json(self, report: EvaluationReport, filepath: str):
        """Save report as JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
        print(f"JSON report saved to {filepath}")

    def save_report_markdown(self, report: EvaluationReport, filepath: str):
        """Save report as Markdown"""

        md_lines = [
            "# Routing Evaluation Report",
            "",
            f"**Generated:** {report.timestamp}",
            f"**Total Test Cases:** {report.total_cases}",
            "",
            "## Executive Summary",
            "",
            f"- **End-to-End Accuracy:** {report.end_to_end_accuracy:.2%} ({report.end_to_end_correct}/{report.total_cases})",
            f"- **Cost Savings vs Opus:** ${report.cost_savings_vs_opus:.4f} ({report.cost_savings_percentage:.1f}%)",
            f"- **Average Latency:** {report.avg_latency_ms:.2f}ms",
            f"- **Average Cost per Query:** ${report.avg_cost_per_query:.6f}",
            "",
            "## Routing Stage Accuracy",
            "",
            "### Intent Detection",
            "",
            f"- **Accuracy:** {report.intent_accuracy:.2%} ({report.intent_correct}/{report.intent_total})",
            "",
            "**By Category:**",
            ""
        ]

        for category, stats in report.intent_by_category.items():
            md_lines.append(
                f"- {category}: {stats['accuracy']:.2%} ({stats['correct']}/{stats['total']})"
            )

        md_lines.extend([
            "",
            "### Complexity Assessment",
            "",
            f"- **Accuracy:** {report.complexity_accuracy:.2%} ({report.complexity_correct}/{report.complexity_total})",
            "",
            "**By Category:**",
            ""
        ])

        for category, stats in report.complexity_by_category.items():
            md_lines.append(
                f"- {category}: {stats['accuracy']:.2%} ({stats['correct']}/{stats['total']})"
            )

        md_lines.extend([
            "",
            "### Execution Mode Routing",
            "",
            f"- **Accuracy:** {report.execution_mode_accuracy:.2%} ({report.execution_mode_correct}/{report.execution_mode_total})",
            "",
            "**By Category:**",
            ""
        ])

        for category, stats in report.execution_mode_by_category.items():
            md_lines.append(
                f"- {category}: {stats['accuracy']:.2%} ({stats['correct']}/{stats['total']})"
            )

        md_lines.extend([
            "",
            "## Performance Metrics",
            "",
            "### Latency",
            "",
            f"- **Total Latency:** {report.total_latency_ms:.2f}ms",
            f"- **Average per Query:** {report.avg_latency_ms:.2f}ms",
            "",
            "**By Stage:**",
            ""
        ])

        for stage, latency in report.latency_by_stage.items():
            md_lines.append(f"- {stage}: {latency:.2f}ms")

        md_lines.extend([
            "",
            "### Cost Analysis",
            "",
            f"- **Total Cost:** ${report.total_cost_estimate:.6f}",
            f"- **Average per Query:** ${report.avg_cost_per_query:.6f}",
            f"- **Baseline (all Opus):** ${report.total_cost_estimate + report.cost_savings_vs_opus:.6f}",
            f"- **Savings:** ${report.cost_savings_vs_opus:.6f} ({report.cost_savings_percentage:.1f}%)",
            "",
            "**By Model:**",
            ""
        ])

        for model, cost in report.cost_by_model.items():
            md_lines.append(f"- {model}: ${cost:.6f}")

        if report.errors:
            md_lines.extend([
                "",
                "## Errors",
                "",
                f"**Total Errors:** {len(report.errors)}",
                ""
            ])

            for error in report.errors:
                md_lines.append(f"- **{error['case_id']}**: {error['error']}")
                md_lines.append(f"  - Query: {error['query']}")
                md_lines.append("")

        md_lines.extend([
            "",
            "## Detailed Results",
            "",
            "| Case ID | Intent | Complexity | Exec Mode | Latency (ms) | Cost | Model |",
            "|---------|--------|------------|-----------|--------------|------|-------|"
        ])

        for result in report.detailed_results:
            intent_symbol = '✓' if result['intent_correct'] else '✗'
            complexity_symbol = '✓' if result['complexity_correct'] else '✗'
            exec_symbol = '✓' if result['execution_mode_correct'] else '✗'

            md_lines.append(
                f"| {result['case_id']} | {intent_symbol} | {complexity_symbol} | "
                f"{exec_symbol} | {result['latency_ms']:.2f} | "
                f"${result['cost_estimate']:.6f} | {result['model_used']} |"
            )

        md_lines.append("")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))

        print(f"Markdown report saved to {filepath}")


def generate_test_case_template(output_path: str):
    """Generate test case template JSON file"""

    template = {
        "test_cases": [
            {
                "case_id": "TC001",
                "query": "查询我的最新报销单",
                "expected_intent": "query",
                "expected_complexity": "simple",
                "expected_execution_mode": "react",
                "description": "简单查询意图，低复杂度",
                "category": "query_simple"
            },
            {
                "case_id": "TC002",
                "query": "帮我提交一个差旅申请，从北京到上海，预算5000元",
                "expected_intent": "submit",
                "expected_complexity": "medium",
                "expected_execution_mode": "planning",
                "description": "提交意图，中等复杂度，需要提取多个参数",
                "category": "submit_medium"
            },
            {
                "case_id": "TC003",
                "query": "分析一下Q3的差旅支出趋势，并给出优化建议",
                "expected_intent": "analysis",
                "expected_complexity": "complex",
                "expected_execution_mode": "complex",
                "description": "分析意图，高复杂度，需要多步推理",
                "category": "analysis_complex"
            },
            {
                "case_id": "TC004",
                "query": "我的报销单为什么被拒绝了？",
                "expected_intent": "query",
                "expected_complexity": "simple",
                "expected_execution_mode": "react",
                "description": "查询意图，简单查询",
                "category": "query_simple"
            },
            {
                "case_id": "TC005",
                "query": "修改我最新的差旅申请，增加住宿预算1000元",
                "expected_intent": "update",
                "expected_complexity": "medium",
                "expected_execution_mode": "planning",
                "description": "更新意图，中等复杂度",
                "category": "update_medium"
            }
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print(f"Test case template generated at {output_path}")


async def main():
    """Main evaluation workflow"""

    project_root = Path(__file__).parent.parent.parent
    test_data_dir = project_root / 'tests' / 'evaluation' / 'data'
    report_dir = project_root / 'tests' / 'evaluation' / 'reports'

    test_data_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    test_cases_file = test_data_dir / 'routing_test_cases.json'

    if not test_cases_file.exists():
        print("Generating test case template...")
        generate_test_case_template(str(test_cases_file))
        print(f"\nPlease add more test cases to {test_cases_file}")
        print("Then run this script again.")
        return

    evaluator = RoutingEvaluator()

    print(f"Loading test cases from {test_cases_file}...")
    test_cases = evaluator.load_test_cases(str(test_cases_file))

    print(f"Loaded {len(test_cases)} test cases")

    report = await evaluator.evaluate_all(test_cases)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_report_path = report_dir / f'routing_evaluation_{timestamp}.json'
    md_report_path = report_dir / f'routing_evaluation_{timestamp}.md'

    evaluator.save_report_json(report, str(json_report_path))
    evaluator.save_report_markdown(report, str(md_report_path))

    print("\n" + "="*70)
    print("EVALUATION COMPLETE")
    print("="*70)
    print(f"End-to-End Accuracy: {report.end_to_end_accuracy:.2%}")
    print(f"Cost Savings: ${report.cost_savings_vs_opus:.4f} ({report.cost_savings_percentage:.1f}%)")
    print(f"Average Latency: {report.avg_latency_ms:.2f}ms")
    print(f"\nReports saved to:")
    print(f"  - JSON: {json_report_path}")
    print(f"  - Markdown: {md_report_path}")


if __name__ == '__main__':
    asyncio.run(main())
