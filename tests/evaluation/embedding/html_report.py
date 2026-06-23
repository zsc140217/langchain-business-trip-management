"""
HTML报告生成器

生成包含面试记忆要点的交互式HTML报告
"""

from typing import Dict, Any
import json
from datetime import datetime
import os


def generate_html_report(comparison: Dict[str, Any], output_path: str = "embedding_eval_report.html") -> str:
    """
    生成HTML评估报告

    Args:
        comparison: comparator.compare_models()的返回结果
        output_path: 输出HTML文件路径

    Returns:
        生成的HTML文件路径
    """

    # 读取HTML模板
    template_path = os.path.join(os.path.dirname(__file__), 'report_template.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # 准备数据
    summary = comparison['summary']
    overall = comparison['overall_comparison']

    # 核心数字（用于大字展示）
    recall_improvement = summary['key_metrics']['recall@5_improvement']
    ndcg_improvement = summary['key_metrics']['ndcg@5_improvement']
    latency_reduction = summary['key_metrics']['time_comparison']['speedup_pct']
    cost_saving = 100.0  # 本地模型零成本

    # 30秒话术
    speech_30s = f"""我们的RAG系统最初使用DashScope的通用embedding，但在差旅政策查询上Recall@5只有{overall['recall@5']['dashscope']:.1%}。我基于BGE-large-zh进行领域微调，用MNR Loss训练200组样本，Recall@5提升到{overall['recall@5']['finetuned']:.1%}（+{recall_improvement:.1f}%），推理延迟从{summary['key_metrics']['time_comparison']['dashscope']:.0f}ms降到{summary['key_metrics']['time_comparison']['finetuned']:.0f}ms，完全零成本。"""

    # 2分钟话术
    speech_2m = f"""在实现企业差旅助手时，embedding选型从三个维度评估：准确性、成本、延迟。

最初用DashScope API，通用模型对"一线城市住宿标准"等术语理解不准，Recall@5只有{overall['recall@5']['dashscope']:.1%}，每次调用{summary['key_metrics']['time_comparison']['dashscope']:.0f}ms加API费用。

我微调了BGE-large-zh-v1.5：收集200组<查询,政策>样本，用MNR Loss训练，构建Hard Negatives（语义相近但不相关的文档）。评估显示Recall@5提升到{overall['recall@5']['finetuned']:.1%}，NDCG@5提升{ndcg_improvement:.1f}%，延迟降到{summary['key_metrics']['time_comparison']['finetuned']:.0f}ms，本地部署零成本。

生产环境切换后，月节省500元API费用，响应时间减少{latency_reduction:.0f}%。"""

    # 准备图表数据
    chart_data = {
        'recall_comparison': {
            'labels': ['Recall@1', 'Recall@3', 'Recall@5', 'Recall@10'],
            'dashscope': [
                overall['recall@1']['dashscope'],
                overall['recall@3']['dashscope'],
                overall['recall@5']['dashscope'],
                overall['recall@10']['dashscope']
            ],
            'finetuned': [
                overall['recall@1']['finetuned'],
                overall['recall@3']['finetuned'],
                overall['recall@5']['finetuned'],
                overall['recall@10']['finetuned']
            ]
        },
        'radar_data': {
            'labels': ['准确性', '召回率', '排序质量', '首位命中', '平均排名'],
            'dashscope': [
                overall['precision@5']['dashscope'] * 100,
                overall['recall@5']['dashscope'] * 100,
                overall['ndcg@5']['dashscope'] * 100,
                overall['mrr']['dashscope'] * 100,
                100 - (overall['average_rank']['dashscope'] / 10 * 100)  # 归一化，排名越低越好
            ],
            'finetuned': [
                overall['precision@5']['finetuned'] * 100,
                overall['recall@5']['finetuned'] * 100,
                overall['ndcg@5']['finetuned'] * 100,
                overall['mrr']['finetuned'] * 100,
                100 - (overall['average_rank']['finetuned'] / 10 * 100)
            ]
        }
    }

    # 难度对比数据
    difficulty_data = comparison['difficulty_comparison']

    # 替换模板中的占位符
    html = template
    html = html.replace('{{REPORT_DATE}}', datetime.now().strftime('%Y年%m月%d日'))
    html = html.replace('{{RECALL_IMPROVEMENT}}', f'{recall_improvement:+.1f}')
    html = html.replace('{{NDCG_IMPROVEMENT}}', f'{ndcg_improvement:+.1f}')
    html = html.replace('{{LATENCY_REDUCTION}}', f'{latency_reduction:.0f}')
    html = html.replace('{{COST_SAVING}}', '100')
    html = html.replace('{{SPEECH_30S}}', speech_30s)
    html = html.replace('{{SPEECH_2M}}', speech_2m)
    html = html.replace('{{CHART_DATA}}', json.dumps(chart_data))
    html = html.replace('{{OVERALL_COMPARISON}}', json.dumps(overall))
    html = html.replace('{{DIFFICULTY_COMPARISON}}', json.dumps(difficulty_data))
    html = html.replace('{{IMPROVEMENTS}}', json.dumps(comparison['improvements']))
    html = html.replace('{{REGRESSIONS}}', json.dumps(comparison['regressions']))
    html = html.replace('{{SUMMARY}}', json.dumps(summary))

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[OK] HTML报告已生成: {output_path}")
    return output_path


# 测试代码
if __name__ == "__main__":
    # 模拟对比数据
    mock_comparison = {
        'overall_comparison': {
            'recall@1': {'dashscope': 0.45, 'finetuned': 0.58, 'improvement_pct': 28.9, 'winner': 'finetuned'},
            'recall@3': {'dashscope': 0.62, 'finetuned': 0.75, 'improvement_pct': 21.0, 'winner': 'finetuned'},
            'recall@5': {'dashscope': 0.68, 'finetuned': 0.83, 'improvement_pct': 22.1, 'winner': 'finetuned'},
            'recall@10': {'dashscope': 0.75, 'finetuned': 0.88, 'improvement_pct': 17.3, 'winner': 'finetuned'},
            'ndcg@5': {'dashscope': 0.75, 'finetuned': 0.84, 'improvement_pct': 12.0, 'winner': 'finetuned'},
            'mrr': {'dashscope': 0.62, 'finetuned': 0.75, 'improvement_pct': 21.0, 'winner': 'finetuned'},
            'precision@5': {'dashscope': 0.136, 'finetuned': 0.166, 'improvement_pct': 22.1, 'winner': 'finetuned'},
            'average_rank': {'dashscope': 3.2, 'finetuned': 2.1, 'improvement_pct': 34.4, 'winner': 'finetuned'}
        },
        'difficulty_comparison': {
            'easy': {
                'count': 4,
                'dashscope': {'recall@5': 0.95, 'ndcg@5': 0.90, 'mrr': 0.85},
                'finetuned': {'recall@5': 1.0, 'ndcg@5': 0.95, 'mrr': 0.95},
                'improvements': {'recall@5': 5.3, 'ndcg@5': 5.6, 'mrr': 11.8}
            },
            'medium': {
                'count': 7,
                'dashscope': {'recall@5': 0.71, 'ndcg@5': 0.72, 'mrr': 0.60},
                'finetuned': {'recall@5': 0.86, 'ndcg@5': 0.82, 'mrr': 0.72},
                'improvements': {'recall@5': 21.1, 'ndcg@5': 13.9, 'mrr': 20.0}
            },
            'hard': {
                'count': 5,
                'dashscope': {'recall@5': 0.45, 'ndcg@5': 0.50, 'mrr': 0.40},
                'finetuned': {'recall@5': 0.65, 'ndcg@5': 0.68, 'mrr': 0.58},
                'improvements': {'recall@5': 44.4, 'ndcg@5': 36.0, 'mrr': 45.0}
            }
        },
        'improvements': [
            {'query_id': 'Q12', 'query': '去广州3天2晚住宿预算多少', 'difficulty': 'hard', 'dashscope_rank': 5, 'finetuned_rank': 1, 'rank_change': 4},
            {'query_id': 'Q13', 'query': '武汉到杭州应该坐高铁还是飞机', 'difficulty': 'hard', 'dashscope_rank': 6, 'finetuned_rank': 2, 'rank_change': 4}
        ],
        'regressions': [
            {'query_id': 'Q17', 'query': '公司年假有多少天', 'difficulty': 'distractor', 'dashscope_rank': -1, 'finetuned_rank': -1, 'rank_change': 0}
        ],
        'summary': {
            'total_queries': 17,
            'improvements_count': 12,
            'regressions_count': 2,
            'no_change_count': 3,
            'key_metrics': {
                'recall@5_improvement': 22.1,
                'ndcg@5_improvement': 12.0,
                'mrr_improvement': 21.0,
                'time_comparison': {
                    'dashscope': 200,
                    'finetuned': 50,
                    'speedup_pct': 75.0
                }
            }
        }
    }

    output = generate_html_report(mock_comparison, 'test_report.html')
    print(f"测试报告生成于: {output}")
