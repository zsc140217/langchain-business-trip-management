"""
Embedding评估系统主执行脚本
"""

import os
import sys
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from tests.evaluation.embedding.test_generator import generate_test_set, print_test_set_summary
from tests.evaluation.embedding.evaluator import DashScopeEvaluator, FinetunedEvaluator
from tests.evaluation.embedding.comparator import compare_models, format_comparison_summary
from tests.evaluation.embedding.html_report import generate_html_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_dashscope_api_key():
    api_key = os.environ.get('DASHSCOPE_API_KEY')
    if not api_key:
        env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('DASHSCOPE_API_KEY='):
                        api_key = line.strip().split('=', 1)[1].strip('"\'')
                        break
    if not api_key:
        raise ValueError("未找到DASHSCOPE_API_KEY")
    return api_key


def main():
    print("\n" + "=" * 80)
    print("Embedding评估系统启动")
    print("=" * 80)

    logger.info("生成测试集...")
    test_set = generate_test_set()
    print_test_set_summary(test_set)

    logger.info("加载API密钥...")
    try:
        api_key = load_dashscope_api_key()
    except ValueError as e:
        logger.error(str(e))
        return

    print("\n" + "=" * 80)
    print("评估 DashScope API")
    print("=" * 80)
    dashscope_evaluator = DashScopeEvaluator(api_key=api_key, model="text-embedding-v2")
    dashscope_result = dashscope_evaluator.evaluate(test_set['queries'], test_set['documents'])
    print(f"[OK] Recall@5: {dashscope_result['metrics']['recall@5']:.4f}")

    print("\n" + "=" * 80)
    print("评估微调模型")
    print("=" * 80)
    finetuned_evaluator = FinetunedEvaluator("learning/models/bge-large-zh-travel-finetuned")
    finetuned_result = finetuned_evaluator.evaluate(test_set['queries'], test_set['documents'])
    print(f"[OK] Recall@5: {finetuned_result['metrics']['recall@5']:.4f}")

    print("\n" + "=" * 80)
    print("对比分析")
    print("=" * 80)
    comparison = compare_models(dashscope_result, finetuned_result)
    print(format_comparison_summary(comparison))

    output_path = os.path.join(os.path.dirname(__file__), 'embedding_evaluation_report.html')
    generate_html_report(comparison, output_path)
    print(f"\n[OK] 报告已生成: {output_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"错误: {str(e)}", exc_info=True)
        sys.exit(1)
