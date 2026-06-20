"""
企业差旅助手 - 综合评估主程序

运行完整的三层评估流程：
1. Code-based 确定性检查
2. Model-based LLM评估
3. 生成评估报告

使用方法：
    python run_comprehensive_eval.py --use-model-grader --output ./results
"""

import argparse
import logging
from pathlib import Path
import json
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.evaluation.comprehensive_eval_framework import (
    TestCase,
    AgentResponse,
    ComprehensiveEvalEngine,
    BatchEvaluator,
    QueryComplexity,
    ScoreLevel
)
from src.models.llm import get_llm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_data(test_data_dir: Path):
    """加载测试数据"""
    # 加载测试用例
    with open(test_data_dir / "test_cases.json", "r", encoding="utf-8") as f:
        test_cases_data = json.load(f)

    test_cases = [
        TestCase(
            task_id=tc["task_id"],
            complexity=QueryComplexity(tc["complexity"]),
            user_query=tc["user_query"],
            expected_tools=tc["expected_tools"],
            expected_output_keywords=tc["expected_output_keywords"],
            forbidden_keywords=tc["forbidden_keywords"],
            policy_constraints=tc["policy_constraints"],
            reference_answer=tc["reference_answer"],
            retrieved_contexts=tc["retrieved_contexts"],
            category=tc["category"],
            metadata=tc["metadata"]
        )
        for tc in test_cases_data
    ]

    # 加载模拟响应
    with open(test_data_dir / "mock_responses.json", "r", encoding="utf-8") as f:
        responses_data = json.load(f)

    responses = [
        AgentResponse(
            answer=r["answer"],
            tool_calls=r["tool_calls"],
            total_cost=r["total_cost"],
            flight_class=r["flight_class"],
            hotel_rating=r["hotel_rating"],
            execution_time=r["execution_time"],
            metadata=r["metadata"]
        )
        for r in responses_data
    ]

    return test_cases, responses


def print_evaluation_summary(result, test_case):
    """打印单个评估结果摘要"""
    print(f"\n{'='*70}")
    print(f"任务: {test_case.task_id} | 类别: {test_case.category} | 复杂度: {test_case.complexity.value}")
    print(f"查询: {test_case.user_query}")
    print(f"-" * 70)

    # Code-based 评分
    code_result = result.code_based_details
    print(f"📋 Code-based 评分: {code_result.score:.3f} [{code_result.level.value.upper()}]")
    print(f"   {code_result.details}")

    if code_result.violations:
        print(f"   ⚠️  违规项:")
        for v in code_result.violations:
            print(f"      - [{v['severity'].upper()}] {v['message']}")

    # Model-based 评分
    if result.model_based_score:
        print(f"\n🤖 Model-based 评分: {result.model_based_score:.3f}")
        if result.model_based_details and "llm_results" in result.model_based_details:
            for metric, detail in result.model_based_details["llm_results"].items():
                status = "✓" if detail["passed"] else "✗"
                print(f"   {status} {metric}: {detail['score']}/5")

    # 最终评分
    print(f"\n⭐ 最终评分: {result.final_score:.3f} [{result.final_level.value.upper()}]")
    print(f"   耗时: {result.total_time:.2f}s")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="运行企业差旅助手综合评估")
    parser.add_argument("--test-data", type=str, default="tests/evaluation/test_data",
                       help="测试数据目录")
    parser.add_argument("--output", type=str, default="tests/evaluation/output",
                       help="输出目录")
    parser.add_argument("--use-model-grader", action="store_true",
                       help="启用 Model-based LLM 评估（会产生 API 调用费用）")
    parser.add_argument("--save-for-human", action="store_true",
                       help="保存案例供人工审核")
    parser.add_argument("--filter-category", type=str,
                       help="只评估指定类别的测试用例")
    parser.add_argument("--filter-complexity", type=str,
                       choices=["simple", "medium", "complex"],
                       help="只评估指定复杂度的测试用例")

    args = parser.parse_args()

    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 加载测试数据
    logger.info("加载测试数据...")
    test_data_dir = Path(args.test_data)
    if not test_data_dir.exists():
        logger.error(f"测试数据目录不存在: {test_data_dir}")
        logger.info("运行 python tests/evaluation/generate_test_suite.py 生成测试数据")
        return

    test_cases, responses = load_test_data(test_data_dir)
    logger.info(f"加载了 {len(test_cases)} 个测试用例")

    # 过滤测试用例
    if args.filter_category:
        test_cases_filtered = []
        responses_filtered = []
        for tc, resp in zip(test_cases, responses):
            if tc.category == args.filter_category:
                test_cases_filtered.append(tc)
                responses_filtered.append(resp)
        test_cases, responses = test_cases_filtered, responses_filtered
        logger.info(f"过滤后剩余 {len(test_cases)} 个测试用例（类别: {args.filter_category}）")

    if args.filter_complexity:
        test_cases_filtered = []
        responses_filtered = []
        for tc, resp in zip(test_cases, responses):
            if tc.complexity.value == args.filter_complexity:
                test_cases_filtered.append(tc)
                responses_filtered.append(resp)
        test_cases, responses = test_cases_filtered, responses_filtered
        logger.info(f"过滤后剩余 {len(test_cases)} 个测试用例（复杂度: {args.filter_complexity}）")

    if not test_cases:
        logger.error("没有符合条件的测试用例")
        return

    # 初始化评估引擎
    logger.info("初始化评估引擎...")
    llm = get_llm()
    engine = ComprehensiveEvalEngine(llm, output_dir)
    batch_evaluator = BatchEvaluator(engine)

    # 执行评估
    logger.info(f"开始评估 (use_model_grader={args.use_model_grader})...")
    if args.use_model_grader:
        logger.warning("⚠️  已启用 Model-based 评估，将产生 LLM API 调用费用")

    results = []
    for i, (test_case, response) in enumerate(zip(test_cases, responses), 1):
        logger.info(f"[{i}/{len(test_cases)}] 评估任务: {test_case.task_id}")

        result = engine.evaluate(
            test_case,
            response,
            use_model_grader=args.use_model_grader,
            save_for_human=args.save_for_human
        )
        results.append(result)

        # 打印摘要
        print_evaluation_summary(result, test_case)

    # 生成报告
    logger.info("生成评估报告...")
    report_path = output_dir / "evaluation_report.json"
    report = batch_evaluator.generate_report(results, report_path)

    # 打印报告摘要
    print("\n" + "="*70)
    print("📊 评估报告摘要")
    print("="*70)
    print(f"总任务数: {report['summary']['total_tasks']}")
    print(f"平均分: {report['summary']['average_score']:.3f}")
    print(f"通过率: {report['summary']['pass_rate']:.1%}")
    print(f"总耗时: {report['summary']['total_time']:.2f}s")
    print(f"\n级别分布:")
    for level, count in report['summary']['level_distribution'].items():
        percentage = count / report['summary']['total_tasks'] * 100
        print(f"  {level.upper()}: {count} ({percentage:.1f}%)")

    if report['failures']:
        print(f"\n⚠️  失败案例 ({len(report['failures'])} 个):")
        for failure in report['failures'][:5]:  # 只显示前5个
            print(f"  - {failure['task_id']}: {failure['level']} (score={failure['score']:.3f})")
            if failure['violations']:
                for v in failure['violations'][:2]:  # 只显示前2个违规
                    print(f"    [{v['severity']}] {v['message']}")

    print(f"\n✅ 完整报告已保存到: {report_path}")
    print("="*70)

    # 保存详细结果
    detailed_results_path = output_dir / "detailed_results.json"
    with open(detailed_results_path, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "task_id": r.task_id,
                    "final_score": r.final_score,
                    "final_level": r.final_level.value,
                    "code_based_score": r.code_based_score,
                    "model_based_score": r.model_based_score,
                    "total_time": r.total_time,
                    "timestamp": r.timestamp,
                    "violations": r.code_based_details.violations
                }
                for r in results
            ],
            f,
            ensure_ascii=False,
            indent=2
        )
    logger.info(f"详细结果已保存到: {detailed_results_path}")

    # 退出码
    critical_count = report['summary'].get('critical_count', 0)
    if critical_count > 0:
        logger.error(f"❌ 发现 {critical_count} 个 CRITICAL 问题")
        sys.exit(1)
    elif report['summary']['pass_rate'] < 0.8:
        logger.warning(f"⚠️  通过率 ({report['summary']['pass_rate']:.1%}) 低于 80%")
        sys.exit(1)
    else:
        logger.info("✅ 评估通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
