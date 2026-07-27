"""
LLM-as-Judge RAG评估脚本
使用通义千问评估4个维度：Correctness, Relevance, Groundedness, Retrieval Relevance

基于现有的88条召回分析数据，补充LLM-as-Judge评分
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入现有的评估器
from tests.evaluation.evaluators import (
    ComprehensiveEvaluator,
    CorrectnessInput,
    RelevanceInput,
    GroundednessInput,
    RetrievalRelevanceInput,
    EvaluationResult
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_recall_analysis_data(file_path: str) -> Dict[str, Any]:
    """加载召回分析数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_qwen_llm():
    """创建通义千问LLM实例 - 使用百炼平台私有部署API"""
    try:
        import dashscope
        from dashscope import Generation
        from http import HTTPStatus

        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY environment variable not set")

        # 设置百炼平台自定义API端点
        dashscope.api_key = api_key
        dashscope.base_http_api_url = 'https://ws-u3nguufiemgaazzm.cn-beijing.maas.aliyuncs.com/api/v1'

        # 创建一个包装类，兼容evaluators.py的接口
        class QwenLLMWrapper:
            def __init__(self, model_name="qwen3.7-max"):
                self.model_name = model_name

            def invoke(self, messages):
                """兼容LangChain的invoke接口"""
                # 提取消息内容
                if isinstance(messages, list) and len(messages) > 0:
                    prompt = messages[0].content if hasattr(messages[0], 'content') else str(messages[0])
                else:
                    prompt = str(messages)

                # 调用百炼平台API（使用messages格式）
                response = Generation.call(
                    api_key=api_key,
                    model=self.model_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    result_format="message",
                    temperature=0.0,
                    max_tokens=2000
                )

                if response.status_code == HTTPStatus.OK:
                    # 返回一个兼容的响应对象
                    class ResponseWrapper:
                        def __init__(self, text):
                            self.content = text

                    return ResponseWrapper(response.output.choices[0].message.content)
                else:
                    raise RuntimeError(f"百炼平台API错误: {response.code} - {response.message}")

        llm = QwenLLMWrapper()
        logger.info("通义千问LLM初始化成功（百炼平台 - qwen3.7-max）")
        return llm

    except ImportError:
        logger.error("dashscope not found. Install: pip install dashscope")
        raise
    except Exception as e:
        logger.error(f"LLM初始化失败: {e}")
        raise


def generate_mock_answer(query: str, retrieved_docs: List[str]) -> str:
    """
    基于查询和检索文档生成模拟答案

    注意：这是简化版本，实际应调用RAG系统生成答案
    为了快速验证评估流程，这里使用简化逻辑
    """
    if not retrieved_docs:
        return "抱歉，我没有找到相关信息。"

    # 简单拼接前两个文档
    context = "\n\n".join(retrieved_docs[:2])
    answer = f"根据查询\"{query}\"，相关规定如下：\n\n{context[:200]}..."

    return answer


def evaluate_test_case(
    evaluator: ComprehensiveEvaluator,
    test_case: Dict[str, Any],
    use_mock_answer: bool = True
) -> Dict[str, Any]:
    """
    评估单个测试用例

    Args:
        evaluator: 综合评估器
        test_case: 测试用例数据
        use_mock_answer: 是否使用模拟答案（True=不调用真实RAG系统）

    Returns:
        评估结果字典
    """
    query = test_case['query']
    retrieved_docs = test_case['retrieved_docs']

    # 生成答案（实际应调用RAG系统）
    if use_mock_answer:
        answer = generate_mock_answer(query, retrieved_docs)
    else:
        # TODO: 调用真实RAG系统
        # from src.agents.intelligent_router import IntelligentRouter
        # router = IntelligentRouter(...)
        # result = router.route(query)
        # answer = result['answer']
        answer = generate_mock_answer(query, retrieved_docs)

    # 运行4个维度的评估
    try:
        results = evaluator.evaluate_rag_pipeline(
            question=query,
            answer=answer,
            retrieved_contexts=retrieved_docs,
            reference=None  # 没有参考答案
        )

        # 汇总评分
        summary = evaluator.summarize_results(results)

        return {
            'test_case_id': test_case['id'],
            'query': query,
            'category': test_case['category'],
            'difficulty': test_case['difficulty'],
            'recall_at_5': test_case['recall_at_5'],
            'answer': answer,
            'evaluation_results': {
                metric: {
                    'score': result.score,
                    'passed': result.passed,
                    'reasoning': result.reasoning
                }
                for metric, result in results.items()
            },
            'summary': summary,
            'needs_human_review': _should_review(results, summary)
        }

    except Exception as e:
        logger.error(f"评估测试用例 {test_case['id']} 失败: {e}")
        return {
            'test_case_id': test_case['id'],
            'query': query,
            'error': str(e)
        }


def _should_review(results: Dict[str, EvaluationResult], summary: Dict[str, Any]) -> bool:
    """
    判断是否需要人工review

    规则：
    1. 任何维度得分 <= 2 分（严重问题）
    2. Groundedness <= 3分（疑似幻觉）
    3. 平均分在 3-4 之间（边界分数）
    """
    # 严重问题
    if any(r.score <= 2 for r in results.values()):
        return True

    # 疑似幻觉
    if results['groundedness'].score <= 3:
        return True

    # 边界分数
    avg_score = summary['average_score']
    if 3.0 <= avg_score <= 4.0:
        return True

    return False


def run_evaluation(
    data_file: str,
    output_dir: str,
    max_samples: int = 10,
    use_mock_answer: bool = True
) -> Dict[str, Any]:
    """
    运行LLM-as-Judge评估

    Args:
        data_file: 召回分析数据文件
        output_dir: 输出目录
        max_samples: 最大评估样本数（成本控制）
        use_mock_answer: 是否使用模拟答案

    Returns:
        评估结果汇总
    """
    logger.info("="*60)
    logger.info("LLM-as-Judge RAG评估")
    logger.info("="*60)

    # 加载数据
    logger.info(f"加载数据: {data_file}")
    data = load_recall_analysis_data(data_file)

    # 过滤有效数据（有检索结果的）
    test_cases = [
        case for case in data['vector']
        if case['retrieved_docs'] and len(case['retrieved_docs']) > 0
    ]

    logger.info(f"有效测试用例数: {len(test_cases)}")

    # 限制样本数（成本控制）
    if max_samples > 0:
        test_cases = test_cases[:max_samples]
        logger.info(f"实际评估数: {len(test_cases)} (max_samples={max_samples})")

    # 创建LLM
    logger.info("初始化通义千问LLM...")
    llm = create_qwen_llm()

    # 创建评估器
    evaluator = ComprehensiveEvaluator(llm=llm, temperature=0.0)
    logger.info("评估器初始化完成")

    # 运行评估
    results = []
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n[{i}/{len(test_cases)}] 评估测试用例: {test_case['id']}")
        logger.info(f"  查询: {test_case['query']}")
        logger.info(f"  类别: {test_case['category']}")

        result = evaluate_test_case(evaluator, test_case, use_mock_answer)
        results.append(result)

        # 显示评分
        if 'summary' in result:
            logger.info(f"  平均分: {result['summary']['average_score']:.2f}/5")
            logger.info(f"  需要review: {'是' if result['needs_human_review'] else '否'}")

    # 计算统计数据
    stats = calculate_statistics(results)

    # 生成报告
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_path / f"llm_judge_evaluation_{timestamp}.md"

    generate_report(results, stats, report_file)

    logger.info(f"\n报告已生成: {report_file}")

    return {
        'results': results,
        'stats': stats,
        'report_file': str(report_file)
    }


def calculate_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算统计数据"""
    valid_results = [r for r in results if 'summary' in r]

    if not valid_results:
        return {}

    # 各维度平均分
    metrics = ['correctness', 'relevance', 'groundedness', 'retrieval_relevance']
    metric_scores = {metric: [] for metric in metrics}

    for result in valid_results:
        for metric in metrics:
            if metric in result['evaluation_results']:
                metric_scores[metric].append(result['evaluation_results'][metric]['score'])

    # 计算平均分
    metric_avg = {
        metric: sum(scores) / len(scores) if scores else 0
        for metric, scores in metric_scores.items()
    }

    # 整体平均分
    overall_avg = sum(r['summary']['average_score'] for r in valid_results) / len(valid_results)

    # 需要review的数量
    review_count = sum(1 for r in valid_results if r['needs_human_review'])

    # 按类别统计
    by_category = {}
    for result in valid_results:
        category = result.get('category', 'unknown')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(result['summary']['average_score'])

    category_avg = {
        cat: sum(scores) / len(scores)
        for cat, scores in by_category.items()
    }

    return {
        'total_cases': len(results),
        'valid_cases': len(valid_results),
        'overall_average': round(overall_avg, 2),
        'metric_averages': {k: round(v, 2) for k, v in metric_avg.items()},
        'review_count': review_count,
        'review_percentage': round(review_count / len(valid_results) * 100, 1),
        'by_category': {k: round(v, 2) for k, v in category_avg.items()}
    }


def generate_report(
    results: List[Dict[str, Any]],
    stats: Dict[str, Any],
    output_file: Path
):
    """生成Markdown报告"""
    # 处理空统计数据的情况
    if not stats:
        report = f"""# LLM-as-Judge RAG评估报告

**评估时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**评估模型**: 通义千问 (qwen-plus)
**评估方法**: 4维度LLM-as-Judge (Correctness, Relevance, Groundedness, Retrieval Relevance)

---

## 评估失败

所有测试用例评估均失败，请检查：
1. DASHSCOPE_API_KEY环境变量是否正确设置
2. 通义千问API是否可访问
3. 测试数据格式是否正确

错误详情：
"""
        for result in results:
            if 'error' in result:
                report += f"\n- 测试用例 {result['test_case_id']}: {result['error']}\n"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        return

    report = f"""# LLM-as-Judge RAG评估报告

**评估时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**评估模型**: 通义千问 (qwen-plus)
**评估方法**: 4维度LLM-as-Judge (Correctness, Relevance, Groundedness, Retrieval Relevance)

---

## 整体统计

| 指标 | 值 |
|------|-----|
| 总测试用例数 | {stats['total_cases']} |
| 有效评估数 | {stats['valid_cases']} |
| 整体平均分 | **{stats['overall_average']}/5** |
| 需要人工review | {stats['review_count']} ({stats['review_percentage']}%) |

---

## 各维度平均分

| 维度 | 平均分 | 说明 |
|------|--------|------|
| **Correctness** (正确性) | {stats['metric_averages']['correctness']}/5 | 答案是否准确无误 |
| **Relevance** (相关性) | {stats['metric_averages']['relevance']}/5 | 答案是否切题 |
| **Groundedness** (忠实度) | {stats['metric_averages']['groundedness']}/5 | 是否基于检索内容（幻觉检测） |
| **Retrieval Relevance** (检索相关性) | {stats['metric_averages']['retrieval_relevance']}/5 | 检索文档质量 |

---

## 按类别统计

| 类别 | 平均分 |
|------|--------|
"""

    for category, avg_score in stats['by_category'].items():
        report += f"| {category} | {avg_score}/5 |\n"

    report += "\n---\n\n## 需要人工Review的Case\n\n"

    review_cases = [r for r in results if r.get('needs_human_review', False)]

    if review_cases:
        for i, result in enumerate(review_cases, 1):
            report += f"""
### Case {i}: {result['test_case_id']}

**查询**: {result['query']}

**类别**: {result['category']}

**平均分**: {result['summary']['average_score']:.2f}/5

**各维度评分**:
"""
            for metric, eval_result in result['evaluation_results'].items():
                report += f"- {metric}: {eval_result['score']}/5 {'✓' if eval_result['passed'] else '✗'}\n"

            report += f"\n**Review原因**: "

            # 分析原因
            reasons = []
            for metric, eval_result in result['evaluation_results'].items():
                if eval_result['score'] <= 2:
                    reasons.append(f"{metric}得分过低({eval_result['score']})")

            if result['evaluation_results']['groundedness']['score'] <= 3:
                reasons.append("疑似幻觉")

            if 3.0 <= result['summary']['average_score'] <= 4.0:
                reasons.append("边界分数")

            report += ", ".join(reasons) + "\n"
            report += "\n---\n"
    else:
        report += "\n无需人工review的case。\n"

    report += """

---

## 详细评估结果

"""

    valid_results = [r for r in results if 'summary' in r]
    for i, result in enumerate(valid_results, 1):
        report += f"""
### Test {i}: {result['test_case_id']}

**查询**: {result['query']}
**类别**: {result['category']}
**难度**: {result['difficulty']}
**Recall@5**: {'✓' if result['recall_at_5'] else '✗'}
**平均分**: {result['summary']['average_score']:.2f}/5

**各维度评分与理由**:

"""

        for metric, eval_result in result['evaluation_results'].items():
            status = '✓ 通过' if eval_result['passed'] else '✗ 未通过'
            report += f"""
#### {metric.upper()}: {eval_result['score']}/5 {status}

{eval_result['reasoning']}

"""

        report += "---\n"

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="LLM-as-Judge RAG评估脚本")
    parser.add_argument(
        "--data-file",
        default="tests/evaluation/recall_analysis.json",
        help="召回分析数据文件"
    )
    parser.add_argument(
        "--output-dir",
        default="tests/evaluation/reports/llm_judge",
        help="输出目录"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=10,
        help="最大评估样本数（成本控制），0表示全部"
    )
    parser.add_argument(
        "--use-real-rag",
        action="store_true",
        help="使用真实RAG系统生成答案（默认使用模拟答案）"
    )

    args = parser.parse_args()

    # 运行评估
    result = run_evaluation(
        data_file=args.data_file,
        output_dir=args.output_dir,
        max_samples=args.max_samples,
        use_mock_answer=not args.use_real_rag
    )

    logger.info("\n" + "="*60)
    logger.info("评估完成！")
    logger.info("="*60)

    if result['stats']:
        logger.info(f"总测试用例数: {result['stats']['total_cases']}")
        logger.info(f"整体平均分: {result['stats']['overall_average']}/5")
        logger.info(f"需要review: {result['stats']['review_count']} ({result['stats']['review_percentage']}%)")
    else:
        logger.error("所有评估均失败，请检查LLM配置和网络连接")

    logger.info(f"报告位置: {result['report_file']}")


if __name__ == "__main__":
    main()
