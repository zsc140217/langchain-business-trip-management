"""
Embedding评估指标计算模块

实现核心检索评估指标：
1. Recall@K - 召回率
2. Precision@K - 精确率
3. NDCG@K - 归一化折损累积增益
4. MRR - 平均倒数排名
5. MAP - 平均精度均值
6. Hit Rate - 命中率
7. Average Rank - 平均排名
8. Separation Score - 正负样本分离度
"""

import numpy as np
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


def calculate_recall_at_k(ranks: List[int], k: int) -> float:
    """
    计算Recall@K

    定义：在Top-K结果中找到相关文档的比例

    公式：Recall@K = (检索到的相关文档数) / (总相关文档数)

    在我们的场景中，每个查询只有1个相关文档，所以：
    Recall@K = 1 if rank <= k else 0

    Args:
        ranks: 正确文档的排名列表，-1表示未找到
        k: Top-K阈值

    Returns:
        Recall@K得分 (0-1)
    """
    if not ranks:
        return 0.0

    # 计算有多少查询在Top-K中找到了相关文档
    hits = sum(1 for rank in ranks if 0 < rank <= k)
    return hits / len(ranks)


def calculate_precision_at_k(ranks: List[int], k: int) -> float:
    """
    计算Precision@K

    定义：Top-K结果中相关文档的比例

    公式：Precision@K = (检索到的相关文档数) / K

    Args:
        ranks: 正确文档的排名列表
        k: Top-K阈值

    Returns:
        Precision@K得分 (0-1)
    """
    if not ranks:
        return 0.0

    hits = sum(1 for rank in ranks if 0 < rank <= k)
    return hits / (len(ranks) * k)


def calculate_ndcg_at_k(ranks: List[int], k: int) -> float:
    """
    计算NDCG@K (Normalized Discounted Cumulative Gain)

    定义：考虑排序位置的检索质量指标，排名越靠前权重越高

    公式：
    DCG@K = Σ(rel_i / log2(i+1))  for i=1 to K
    IDCG@K = 理想情况下的DCG (相关文档排在第1位)
    NDCG@K = DCG@K / IDCG@K

    在我们的场景中（单相关文档，二元相关性）：
    - 如果相关文档在Top-K中，DCG = 1 / log2(rank+1)
    - IDCG = 1 / log2(2) = 1.0
    - NDCG = 1 / log2(rank+1)

    Args:
        ranks: 正确文档的排名列表
        k: Top-K阈值

    Returns:
        NDCG@K得分 (0-1)
    """
    if not ranks:
        return 0.0

    ndcg_scores = []
    for rank in ranks:
        if 0 < rank <= k:
            # DCG: 相关文档的贡献 = 1 / log2(rank+1)
            dcg = 1.0 / np.log2(rank + 1)
            # IDCG: 理想情况（rank=1）= 1 / log2(2) = 1.0
            idcg = 1.0
            ndcg = dcg / idcg
        else:
            ndcg = 0.0
        ndcg_scores.append(ndcg)

    return np.mean(ndcg_scores)


def calculate_mrr(ranks: List[int]) -> float:
    """
    计算MRR (Mean Reciprocal Rank)

    定义：第一个相关文档排名的倒数的平均值

    公式：MRR = (1/Q) * Σ(1/rank_i)  for i=1 to Q

    直观理解：
    - 相关文档排第1位：得分1.0
    - 相关文档排第2位：得分0.5
    - 相关文档排第3位：得分0.333

    Args:
        ranks: 正确文档的排名列表

    Returns:
        MRR得分 (0-1)
    """
    if not ranks:
        return 0.0

    reciprocal_ranks = [1.0 / rank if rank > 0 else 0.0 for rank in ranks]
    return np.mean(reciprocal_ranks)


def calculate_map(ranks: List[int], k: int = 10) -> float:
    """
    计算MAP (Mean Average Precision)

    定义：在不同召回水平下的平均精确率

    对于单相关文档的场景：
    MAP = Precision@rank_of_relevant_doc

    Args:
        ranks: 正确文档的排名列表
        k: 考虑的最大排名

    Returns:
        MAP得分 (0-1)
    """
    if not ranks:
        return 0.0

    ap_scores = []
    for rank in ranks:
        if 0 < rank <= k:
            # Average Precision = 1 / rank (只有一个相关文档)
            ap = 1.0 / rank
        else:
            ap = 0.0
        ap_scores.append(ap)

    return np.mean(ap_scores)


def calculate_hit_rate(ranks: List[int], k: int) -> float:
    """
    计算Hit Rate (命中率)

    定义：至少找到一个相关文档的查询比例

    在单相关文档场景下，等价于Recall@K

    Args:
        ranks: 正确文档的排名列表
        k: Top-K阈值

    Returns:
        Hit Rate得分 (0-1)
    """
    return calculate_recall_at_k(ranks, k)


def calculate_average_rank(ranks: List[int]) -> float:
    """
    计算Average Rank (平均排名)

    定义：相关文档的平均排名位置

    排名越小越好（1是最好的）

    Args:
        ranks: 正确文档的排名列表

    Returns:
        平均排名（数值越小越好）
    """
    if not ranks:
        return float('inf')

    # 只计算找到的文档（rank > 0）
    valid_ranks = [rank for rank in ranks if rank > 0]

    if not valid_ranks:
        return float('inf')

    return np.mean(valid_ranks)


def calculate_separation_score(
    positive_scores: List[float],
    negative_scores: List[float]
) -> float:
    """
    计算Separation Score (正负样本分离度)

    定义：正样本相似度均值 - 负样本相似度均值

    分离度越大，说明模型越能区分相关和不相关文档

    Args:
        positive_scores: 正样本（相关文档）的相似度得分列表
        negative_scores: 负样本（不相关文档）的相似度得分列表

    Returns:
        分离度得分（越大越好）
    """
    if not positive_scores or not negative_scores:
        return 0.0

    pos_mean = np.mean(positive_scores)
    neg_mean = np.mean(negative_scores)

    return pos_mean - neg_mean


def calculate_all_metrics(
    ranks: List[int],
    positive_scores: List[float] = None,
    negative_scores: List[float] = None,
    k_values: List[int] = [1, 3, 5, 10]
) -> Dict[str, Any]:
    """
    计算所有评估指标

    Args:
        ranks: 正确文档的排名列表
        positive_scores: 正样本相似度得分（可选）
        negative_scores: 负样本相似度得分（可选）
        k_values: 要计算的K值列表

    Returns:
        包含所有指标的字典
    """
    metrics = {}

    # 计算各个K值下的指标
    for k in k_values:
        metrics[f'recall@{k}'] = calculate_recall_at_k(ranks, k)
        metrics[f'precision@{k}'] = calculate_precision_at_k(ranks, k)
        metrics[f'ndcg@{k}'] = calculate_ndcg_at_k(ranks, k)
        metrics[f'hit_rate@{k}'] = calculate_hit_rate(ranks, k)

    # 计算与K无关的指标
    metrics['mrr'] = calculate_mrr(ranks)
    metrics['map'] = calculate_map(ranks)
    metrics['average_rank'] = calculate_average_rank(ranks)

    # 如果提供了相似度得分，计算分离度
    if positive_scores and negative_scores:
        metrics['separation_score'] = calculate_separation_score(
            positive_scores, negative_scores
        )

    return metrics


def format_metrics_for_display(metrics: Dict[str, float]) -> str:
    """
    格式化指标用于显示

    Args:
        metrics: 指标字典

    Returns:
        格式化的字符串
    """
    lines = []
    lines.append("=" * 60)
    lines.append("评估指标")
    lines.append("=" * 60)

    # 按指标类型分组显示
    recall_keys = [k for k in metrics if k.startswith('recall@')]
    ndcg_keys = [k for k in metrics if k.startswith('ndcg@')]
    other_keys = [k for k in metrics if not k.startswith(('recall@', 'ndcg@', 'precision@', 'hit_rate@'))]

    if recall_keys:
        lines.append("\n召回率指标:")
        for key in sorted(recall_keys):
            lines.append(f"  {key:20s}: {metrics[key]:.4f} ({metrics[key]*100:.2f}%)")

    if ndcg_keys:
        lines.append("\n排序质量指标:")
        for key in sorted(ndcg_keys):
            lines.append(f"  {key:20s}: {metrics[key]:.4f}")

    if other_keys:
        lines.append("\n其他指标:")
        for key in sorted(other_keys):
            value = metrics[key]
            if key == 'average_rank':
                lines.append(f"  {key:20s}: {value:.2f}")
            else:
                lines.append(f"  {key:20s}: {value:.4f}")

    lines.append("=" * 60)
    return "\n".join(lines)


# 示例和测试
if __name__ == "__main__":
    # 模拟评估数据
    # ranks: 正确文档的排名 [1, 2, 1, 5, -1] 表示5个查询的结果排名
    test_ranks = [1, 2, 1, 5, -1, 3, 1, 10, 2, 4]

    print("测试评估指标计算...")
    print(f"输入排名: {test_ranks}")
    print()

    # 计算所有指标
    metrics = calculate_all_metrics(test_ranks)

    # 显示结果
    print(format_metrics_for_display(metrics))

    # 测试分离度
    pos_scores = [0.85, 0.90, 0.88, 0.92, 0.87]
    neg_scores = [0.45, 0.50, 0.42, 0.55, 0.48]

    separation = calculate_separation_score(pos_scores, neg_scores)
    print(f"\n分离度测试:")
    print(f"  正样本平均相似度: {np.mean(pos_scores):.4f}")
    print(f"  负样本平均相似度: {np.mean(neg_scores):.4f}")
    print(f"  分离度得分: {separation:.4f}")
