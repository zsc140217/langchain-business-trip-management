"""
微调前后模型对比评估

对比：
1. 基础模型：BAAI/bge-large-zh-v1.5 (未微调)
2. 微调模型：./models/bge-large-zh-travel-finetuned

评估指标：
- Accuracy@1：Top-1准确率
- Recall@5：Top-5召回率
- NDCG@5：归一化折损累积增益
- MRR：平均倒数排名
"""
import json
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Tuple, Dict
import time

# 设置离线模式，避免网络请求
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

class EmbeddingEvaluator:
    def __init__(self, model_path: str, model_name: str):
        """初始化评估器"""
        self.model_name = model_name
        print(f"\n[INFO] Loading model: {model_name}")
        print(f"       Path: {model_path}")
        start_time = time.time()
        self.model = SentenceTransformer(model_path)
        load_time = time.time() - start_time
        print(f"       Load time: {load_time:.2f}s")

    def encode_documents(self, documents: List[str]) -> np.ndarray:
        """编码文档库"""
        print(f"[INFO] Encoding {len(documents)} documents...")
        return self.model.encode(documents, show_progress_bar=True)

    def encode_queries(self, queries: List[str]) -> np.ndarray:
        """编码查询"""
        print(f"[INFO] Encoding {len(queries)} queries...")
        return self.model.encode(queries, show_progress_bar=True)

    def retrieve_top_k(self, query_emb: np.ndarray, doc_embs: np.ndarray, k: int = 5) -> Tuple[List[int], List[float]]:
        """检索Top-K文档"""
        similarities = cosine_similarity([query_emb], doc_embs)[0]
        top_k_indices = np.argsort(similarities)[::-1][:k]
        top_k_scores = similarities[top_k_indices]
        return top_k_indices.tolist(), top_k_scores.tolist()

    def calculate_accuracy_at_1(self, results: List[Dict]) -> float:
        """计算Accuracy@1"""
        correct = sum(1 for r in results if r['rank'] == 1)
        return correct / len(results) if results else 0.0

    def calculate_recall_at_k(self, results: List[Dict], k: int = 5) -> float:
        """计算Recall@K"""
        correct = sum(1 for r in results if r['rank'] <= k and r['rank'] > 0)
        return correct / len(results) if results else 0.0

    def calculate_mrr(self, results: List[Dict]) -> float:
        """计算MRR (Mean Reciprocal Rank)"""
        reciprocal_ranks = [1.0 / r['rank'] if r['rank'] > 0 else 0.0 for r in results]
        return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0

    def calculate_ndcg_at_k(self, results: List[Dict], k: int = 5) -> float:
        """计算NDCG@K"""
        ndcg_scores = []
        for r in results:
            if r['rank'] > 0 and r['rank'] <= k:
                # DCG: relevance / log2(rank + 1)
                dcg = 1.0 / np.log2(r['rank'] + 1)
                # IDCG: ideal DCG (best case: rank=1)
                idcg = 1.0 / np.log2(2)
                ndcg = dcg / idcg
            else:
                ndcg = 0.0
            ndcg_scores.append(ndcg)
        return sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0

    def evaluate(self, test_set: Dict, documents: List[str]) -> Dict:
        """完整评估流程"""
        print(f"\n{'='*70}")
        print(f"Evaluating: {self.model_name}")
        print(f"{'='*70}")

        # 编码文档库
        doc_embs = self.encode_documents(documents)

        # 编码查询
        queries = [q['query'] for q in test_set['test_queries']]
        query_embs = self.encode_queries(queries)

        # 逐个查询评估
        results = []
        print(f"\n[INFO] Evaluating {len(queries)} queries...")

        for idx, (query_data, query_emb) in enumerate(zip(test_set['test_queries'], query_embs)):
            query_text = query_data['query']
            difficulty = query_data['difficulty']
            expected_contains = query_data['expected_doc_contains']

            # 检索Top-5
            top_k_indices, top_k_scores = self.retrieve_top_k(query_emb, doc_embs, k=5)

            # 查找正确文档的排名
            rank = -1
            retrieved_docs = []

            for rank_idx, (doc_idx, score) in enumerate(zip(top_k_indices, top_k_scores), start=1):
                retrieved_doc = documents[doc_idx]
                retrieved_docs.append({
                    'rank': rank_idx,
                    'doc': retrieved_doc[:100],
                    'score': float(score)
                })

                # 检查是否是正确文档
                if expected_contains and expected_contains in retrieved_doc:
                    if rank == -1:  # 只记录第一次出现
                        rank = rank_idx

            # 对于干扰样本，期望没有匹配
            if difficulty == 'distractor':
                rank = 1 if rank == -1 else -1  # 反转：没找到=正确

            result = {
                'query_id': query_data['id'],
                'query': query_text,
                'difficulty': difficulty,
                'rank': rank,
                'top_1_score': float(top_k_scores[0]),
                'retrieved_docs': retrieved_docs
            }
            results.append(result)

        # 计算指标
        metrics = {
            'accuracy_at_1': self.calculate_accuracy_at_1(results),
            'recall_at_5': self.calculate_recall_at_k(results, k=5),
            'mrr': self.calculate_mrr(results),
            'ndcg_at_5': self.calculate_ndcg_at_k(results, k=5)
        }

        # 按难度分组统计
        difficulty_breakdown = {}
        for diff in ['easy', 'medium', 'hard', 'distractor']:
            diff_results = [r for r in results if r['difficulty'] == diff]
            if diff_results:
                difficulty_breakdown[diff] = {
                    'accuracy_at_1': self.calculate_accuracy_at_1(diff_results),
                    'recall_at_5': self.calculate_recall_at_k(diff_results, k=5),
                    'count': len(diff_results)
                }

        return {
            'model_name': self.model_name,
            'metrics': metrics,
            'difficulty_breakdown': difficulty_breakdown,
            'detailed_results': results
        }


def print_comparison_report(baseline_result: Dict, finetuned_result: Dict):
    """打印对比报告"""
    print(f"\n{'='*70}")
    print(f"EVALUATION REPORT: Baseline vs Finetuned")
    print(f"{'='*70}")

    # 总体指标对比
    print(f"\n--- Overall Metrics ---")
    print(f"{'Metric':<20} {'Baseline':<15} {'Finetuned':<15} {'Improvement':<15}")
    print(f"{'-'*70}")

    baseline_metrics = baseline_result['metrics']
    finetuned_metrics = finetuned_result['metrics']

    for metric in ['accuracy_at_1', 'recall_at_5', 'mrr', 'ndcg_at_5']:
        baseline_val = baseline_metrics[metric]
        finetuned_val = finetuned_metrics[metric]
        improvement = finetuned_val - baseline_val
        improvement_pct = (improvement / baseline_val * 100) if baseline_val > 0 else 0

        print(f"{metric:<20} {baseline_val:<15.2%} {finetuned_val:<15.2%} {improvement_pct:+.1f}%")

    # 难度分组对比
    print(f"\n--- Accuracy by Difficulty ---")
    print(f"{'Difficulty':<15} {'Baseline':<15} {'Finetuned':<15} {'Improvement':<15}")
    print(f"{'-'*70}")

    for diff in ['easy', 'medium', 'hard', 'distractor']:
        baseline_diff = baseline_result['difficulty_breakdown'].get(diff, {})
        finetuned_diff = finetuned_result['difficulty_breakdown'].get(diff, {})

        baseline_acc = baseline_diff.get('accuracy_at_1', 0)
        finetuned_acc = finetuned_diff.get('accuracy_at_1', 0)
        improvement = finetuned_acc - baseline_acc
        improvement_pct = (improvement / baseline_acc * 100) if baseline_acc > 0 else 0

        print(f"{diff:<15} {baseline_acc:<15.2%} {finetuned_acc:<15.2%} {improvement_pct:+.1f}%")

    # 详细失败案例
    print(f"\n--- Failed Cases (Baseline) ---")
    baseline_failures = [r for r in baseline_result['detailed_results'] if r['rank'] != 1 and r['difficulty'] != 'distractor']
    for failure in baseline_failures[:5]:  # 只显示前5个
        print(f"  Query: {failure['query']}")
        print(f"  Difficulty: {failure['difficulty']} | Rank: {failure['rank']}")
        print()

    print(f"\n--- Failed Cases (Finetuned) ---")
    finetuned_failures = [r for r in finetuned_result['detailed_results'] if r['rank'] != 1 and r['difficulty'] != 'distractor']
    for failure in finetuned_failures[:5]:
        print(f"  Query: {failure['query']}")
        print(f"  Difficulty: {failure['difficulty']} | Rank: {failure['rank']}")
        print()


def main():
    print(f"{'='*70}")
    print(f"Embedding Model Evaluation: Before vs After Fine-tuning")
    print(f"{'='*70}")

    # 加载测试集
    test_set_file = Path(__file__).parent / "enhanced_test_set.json"
    with open(test_set_file, 'r', encoding='utf-8') as f:
        test_set = json.load(f)

    documents = test_set['document_corpus']
    print(f"\n[INFO] Test set loaded")
    print(f"       Queries: {len(test_set['test_queries'])}")
    print(f"       Documents: {len(documents)}")

    # 评估基础模型
    baseline_evaluator = EmbeddingEvaluator(
        model_path='BAAI/bge-large-zh-v1.5',
        model_name='Baseline (bge-large-zh-v1.5)'
    )
    baseline_result = baseline_evaluator.evaluate(test_set, documents)

    # 评估微调模型
    finetuned_model_path = Path(__file__).parent.parent.parent.parent / "learning/models/bge-large-zh-travel-finetuned"
    finetuned_evaluator = EmbeddingEvaluator(
        model_path=str(finetuned_model_path),
        model_name='Finetuned (bge-large-zh-travel)'
    )
    finetuned_result = finetuned_evaluator.evaluate(test_set, documents)

    # 打印对比报告
    print_comparison_report(baseline_result, finetuned_result)

    # 保存详细结果
    output_file = Path(__file__).parent / "evaluation_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'baseline': baseline_result,
            'finetuned': finetuned_result
        }, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Detailed results saved to: {output_file}")
    print(f"\n{'='*70}")
    print(f"Evaluation Complete!")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
