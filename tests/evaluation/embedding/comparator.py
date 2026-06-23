"""
Embedding模型对比分析器

对比DashScope API与微调本地模型的性能差异
"""

from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


def compare_models(
    dashscope_result: Dict[str, Any],
    finetuned_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    对比两个模型的评估结果

    Args:
        dashscope_result: DashScope API的评估结果
        finetuned_result: 微调模型的评估结果

    Returns:
        对比分析字典，包含：
        - overall_comparison: 整体指标对比
        - difficulty_comparison: 按难度分组对比
        - improvements: 改进案例（微调模型表现更好）
        - regressions: 退化案例（微调模型表现更差）
        - summary: 总结统计
    """
    logger.info("开始对比两个模型的性能...")

    # 1. 整体指标对比
    overall_comparison = {}
    dashscope_metrics = dashscope_result['metrics']
    finetuned_metrics = finetuned_result['metrics']

    for metric_name in dashscope_metrics.keys():
        dashscope_value = dashscope_metrics[metric_name]
        finetuned_value = finetuned_metrics[metric_name]

        # 计算提升百分比
        if dashscope_value > 0:
            if metric_name == 'average_rank':
                # average_rank越小越好
                improvement_pct = ((dashscope_value - finetuned_value) / dashscope_value) * 100
            else:
                # 其他指标越大越好
                improvement_pct = ((finetuned_value - dashscope_value) / dashscope_value) * 100
        else:
            improvement_pct = 0.0

        # 判断胜者
        if metric_name == 'average_rank':
            winner = 'finetuned' if finetuned_value < dashscope_value else 'dashscope'
        else:
            winner = 'finetuned' if finetuned_value > dashscope_value else 'dashscope'

        overall_comparison[metric_name] = {
            'dashscope': dashscope_value,
            'finetuned': finetuned_value,
            'improvement_pct': improvement_pct,
            'winner': winner
        }

    # 2. 按难度分组对比
    difficulty_comparison = {}
    for difficulty in ['easy', 'medium', 'hard', 'distractor']:
        dashscope_stats = dashscope_result['difficulty_stats'].get(difficulty)
        finetuned_stats = finetuned_result['difficulty_stats'].get(difficulty)

        if dashscope_stats and finetuned_stats:
            difficulty_comparison[difficulty] = {
                'count': dashscope_stats['count'],
                'dashscope': {
                    'recall@5': dashscope_stats['recall@5'],
                    'ndcg@5': dashscope_stats['ndcg@5'],
                    'mrr': dashscope_stats['mrr']
                },
                'finetuned': {
                    'recall@5': finetuned_stats['recall@5'],
                    'ndcg@5': finetuned_stats['ndcg@5'],
                    'mrr': finetuned_stats['mrr']
                },
                'improvements': {
                    'recall@5': ((finetuned_stats['recall@5'] - dashscope_stats['recall@5']) / dashscope_stats['recall@5'] * 100) if dashscope_stats['recall@5'] > 0 else 0,
                    'ndcg@5': ((finetuned_stats['ndcg@5'] - dashscope_stats['ndcg@5']) / dashscope_stats['ndcg@5'] * 100) if dashscope_stats['ndcg@5'] > 0 else 0,
                    'mrr': ((finetuned_stats['mrr'] - dashscope_stats['mrr']) / dashscope_stats['mrr'] * 100) if dashscope_stats['mrr'] > 0 else 0
                }
            }

    # 3. 找出改进和退化案例
    improvements = []
    regressions = []

    dashscope_details = {item['query_id']: item for item in dashscope_result['detailed_results']}
    finetuned_details = {item['query_id']: item for item in finetuned_result['detailed_results']}

    for query_id in dashscope_details.keys():
        dashscope_rank = dashscope_details[query_id]['rank']
        finetuned_rank = finetuned_details[query_id]['rank']

        # 计算排名变化
        if dashscope_rank > 0 and finetuned_rank > 0:
            rank_change = dashscope_rank - finetuned_rank

            case = {
                'query_id': query_id,
                'query': dashscope_details[query_id]['query'],
                'difficulty': dashscope_details[query_id]['difficulty'],
                'dashscope_rank': dashscope_rank,
                'finetuned_rank': finetuned_rank,
                'rank_change': rank_change
            }

            if rank_change > 0:
                # 排名提升（数字变小）
                improvements.append(case)
            elif rank_change < 0:
                # 排名下降（数字变大）
                regressions.append(case)
        elif dashscope_rank <= 0 and finetuned_rank > 0:
            # DashScope未找到，微调模型找到了
            improvements.append({
                'query_id': query_id,
                'query': dashscope_details[query_id]['query'],
                'difficulty': dashscope_details[query_id]['difficulty'],
                'dashscope_rank': -1,
                'finetuned_rank': finetuned_rank,
                'rank_change': float('inf')
            })
        elif dashscope_rank > 0 and finetuned_rank <= 0:
            # DashScope找到了，微调模型未找到
            regressions.append({
                'query_id': query_id,
                'query': dashscope_details[query_id]['query'],
                'difficulty': dashscope_details[query_id]['difficulty'],
                'dashscope_rank': dashscope_rank,
                'finetuned_rank': -1,
                'rank_change': float('-inf')
            })

    # 排序：改进案例按rank_change降序，退化案例按rank_change升序
    improvements.sort(key=lambda x: x['rank_change'] if x['rank_change'] != float('inf') else 1000, reverse=True)
    regressions.sort(key=lambda x: x['rank_change'] if x['rank_change'] != float('-inf') else -1000)

    # 4. 生成总结统计
    summary = {
        'total_queries': len(dashscope_details),
        'improvements_count': len(improvements),
        'regressions_count': len(regressions),
        'no_change_count': len(dashscope_details) - len(improvements) - len(regressions),
        'key_metrics': {
            'recall@5_improvement': overall_comparison['recall@5']['improvement_pct'],
            'ndcg@5_improvement': overall_comparison['ndcg@5']['improvement_pct'],
            'mrr_improvement': overall_comparison['mrr']['improvement_pct'],
            'time_comparison': {
                'dashscope': dashscope_result['eval_time'],
                'finetuned': finetuned_result['eval_time'],
                'speedup_pct': ((dashscope_result['eval_time'] - finetuned_result['eval_time']) / dashscope_result['eval_time'] * 100) if dashscope_result['eval_time'] > 0 else 0
            }
        }
    }

    logger.info("对比完成:")
    logger.info(f"  改进案例: {len(improvements)}个")
    logger.info(f"  退化案例: {len(regressions)}个")
    logger.info(f"  Recall@5提升: {summary['key_metrics']['recall@5_improvement']:.2f}%")

    return {
        'overall_comparison': overall_comparison,
        'difficulty_comparison': difficulty_comparison,
        'improvements': improvements[:10],  # 取Top 10
        'regressions': regressions[:10],  # 取Top 10
        'summary': summary
    }


def format_comparison_summary(comparison: Dict[str, Any]) -> str:
    """
    格式化对比摘要用于终端显示

    Args:
        comparison: compare_models()的返回结果

    Returns:
        格式化的字符串
    """
    lines = []
    lines.append("\n" + "=" * 80)
    lines.append("[对比] Embedding模型对比报告")
    lines.append("=" * 80)

    summary = comparison['summary']

    # 核心指标对比
    lines.append("\n【核心指标对比】")
    lines.append(f"  Recall@5提升:  {summary['key_metrics']['recall@5_improvement']:>+6.2f}%")
    lines.append(f"  NDCG@5提升:    {summary['key_metrics']['ndcg@5_improvement']:>+6.2f}%")
    lines.append(f"  MRR提升:       {summary['key_metrics']['mrr_improvement']:>+6.2f}%")
    lines.append(f"  延迟对比:      DashScope {summary['key_metrics']['time_comparison']['dashscope']:.2f}s → 微调 {summary['key_metrics']['time_comparison']['finetuned']:.2f}s")

    # 案例统计
    lines.append(f"\n【案例分布】")
    lines.append(f"  总查询数:      {summary['total_queries']}")
    lines.append(f"  改进案例:      {summary['improvements_count']} ({summary['improvements_count']/summary['total_queries']*100:.1f}%)")
    lines.append(f"  退化案例:      {summary['regressions_count']} ({summary['regressions_count']/summary['total_queries']*100:.1f}%)")
    lines.append(f"  无变化:        {summary['no_change_count']}")

    # Top 5改进案例
    if comparison['improvements']:
        lines.append(f"\n【Top 5 改进案例】")
        for i, case in enumerate(comparison['improvements'][:5], 1):
            lines.append(f"  {i}. {case['query']}")
            lines.append(f"     排名: {case['dashscope_rank']} → {case['finetuned_rank']} (提升{case['rank_change']}位)")

    # Top 3退化案例
    if comparison['regressions']:
        lines.append(f"\n【Top 3 退化案例】")
        for i, case in enumerate(comparison['regressions'][:3], 1):
            lines.append(f"  {i}. {case['query']}")
            lines.append(f"     排名: {case['dashscope_rank']} → {case['finetuned_rank']} (下降{abs(case['rank_change'])}位)")

    lines.append("\n" + "=" * 80)

    return "\n".join(lines)


# 测试代码
if __name__ == "__main__":
    import json

    # 模拟评估结果
    dashscope_result = {
        'model_name': 'DashScope API',
        'metrics': {'recall@5': 0.68, 'ndcg@5': 0.75, 'mrr': 0.62, 'average_rank': 3.2},
        'difficulty_stats': {
            'easy': {'count': 4, 'recall@5': 0.95, 'ndcg@5': 0.90, 'mrr': 0.85},
            'medium': {'count': 7, 'recall@5': 0.71, 'ndcg@5': 0.72, 'mrr': 0.60}
        },
        'detailed_results': [
            {'query_id': 'Q01', 'query': '北京出差住宿标准', 'rank': 3, 'difficulty': 'easy'},
            {'query_id': 'Q02', 'query': '市内交通费用', 'rank': 1, 'difficulty': 'easy'}
        ],
        'eval_time': 12.5
    }

    finetuned_result = {
        'model_name': 'Finetuned Model',
        'metrics': {'recall@5': 0.83, 'ndcg@5': 0.84, 'mrr': 0.75, 'average_rank': 2.1},
        'difficulty_stats': {
            'easy': {'count': 4, 'recall@5': 1.0, 'ndcg@5': 0.95, 'mrr': 0.95},
            'medium': {'count': 7, 'recall@5': 0.86, 'ndcg@5': 0.82, 'mrr': 0.72}
        },
        'detailed_results': [
            {'query_id': 'Q01', 'query': '北京出差住宿标准', 'rank': 1, 'difficulty': 'easy'},
            {'query_id': 'Q02', 'query': '市内交通费用', 'rank': 1, 'difficulty': 'easy'}
        ],
        'eval_time': 3.2
    }

    comparison = compare_models(dashscope_result, finetuned_result)
    print(format_comparison_summary(comparison))
