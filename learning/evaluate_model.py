"""
模型评估脚本
对比 Baseline (原始BGE) vs Fine-tuned (微调后) 的效果
评估指标: Recall@5, NDCG@10
"""

import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

print("=" * 60)
print("模型效果评估")
print("=" * 60)

# 1. 加载测试数据
print("\n[1/5] 加载测试数据...")
with open('data_preparation/policy_docs.json', 'r', encoding='utf-8') as f:
    docs = json.load(f)

with open('data_preparation/training_data_final.json', 'r', encoding='utf-8') as f:
    test_data = json.load(f)

print(f"文档库: {len(docs)} 个政策")
print(f"测试查询: {len(test_data)} 个")

# 2. 加载模型
print("\n[2/5] 加载模型...")
print("  - Baseline: BAAI/bge-large-zh-v1.5")
baseline_model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

print("  - Fine-tuned: ./models/bge-large-zh-travel-finetuned")
finetuned_model = SentenceTransformer('./models/bge-large-zh-travel-finetuned')

# 3. 编码文档库（两个模型共享）
print("\n[3/5] 编码文档库...")
print("  - Baseline编码...")
baseline_doc_embeddings = baseline_model.encode(docs, show_progress_bar=True)

print("  - Fine-tuned编码...")
finetuned_doc_embeddings = finetuned_model.encode(docs, show_progress_bar=True)

# 4. 评估函数
def evaluate_model(model, doc_embeddings, test_data, docs, model_name):
    """评估单个模型"""
    print(f"\n评估 {model_name}...")

    recall_at_5 = []
    recall_at_10 = []
    ndcg_at_10 = []

    for item in test_data:
        query = item['query']
        positive_doc = item['positive']

        # 为BGE添加查询指令
        query_with_instruction = f"为这个句子生成表示以用于检索相关文章：{query}"

        # 编码query
        query_embedding = model.encode(query_with_instruction)

        # 计算相似度
        similarities = cosine_similarity([query_embedding], doc_embeddings)[0]

        # 排序获取top-k
        top_indices = np.argsort(similarities)[::-1]

        # 找到正确文档的排名
        correct_idx = docs.index(positive_doc)
        rank = np.where(top_indices == correct_idx)[0][0] + 1

        # Recall@5
        recall_at_5.append(1 if rank <= 5 else 0)

        # Recall@10
        recall_at_10.append(1 if rank <= 10 else 0)

        # NDCG@10
        if rank <= 10:
            ndcg_at_10.append(1.0 / np.log2(rank + 1))
        else:
            ndcg_at_10.append(0.0)

    return {
        'recall@5': np.mean(recall_at_5),
        'recall@10': np.mean(recall_at_10),
        'ndcg@10': np.mean(ndcg_at_10)
    }

# 5. 评估两个模型
print("\n[4/5] 开始评估...")

baseline_metrics = evaluate_model(
    baseline_model,
    baseline_doc_embeddings,
    test_data,
    docs,
    "Baseline"
)

finetuned_metrics = evaluate_model(
    finetuned_model,
    finetuned_doc_embeddings,
    test_data,
    docs,
    "Fine-tuned"
)

# 6. 结果对比
print("\n[5/5] 评估结果")
print("=" * 60)
print(f"\n{'指标':<15} {'Baseline':<15} {'Fine-tuned':<15} {'提升':<15}")
print("-" * 60)

for metric in ['recall@5', 'recall@10', 'ndcg@10']:
    baseline_val = baseline_metrics[metric]
    finetuned_val = finetuned_metrics[metric]
    improvement = ((finetuned_val - baseline_val) / baseline_val * 100) if baseline_val > 0 else 0

    print(f"{metric:<15} {baseline_val:<15.2%} {finetuned_val:<15.2%} {improvement:>+.1f}%")

print("=" * 60)

# 判断是否达标
recall_5_improvement = (finetuned_metrics['recall@5'] - baseline_metrics['recall@5']) * 100
if recall_5_improvement >= 10:
    print(f"\n[OK] 达标! Recall@5提升了 {recall_5_improvement:.1f}%，超过10%目标")
else:
    print(f"\n[WARNING] 未达标: Recall@5仅提升 {recall_5_improvement:.1f}%，低于10%目标")

# 保存结果
results = {
    'baseline': baseline_metrics,
    'finetuned': finetuned_metrics,
    'improvement': {
        'recall@5': recall_5_improvement,
        'recall@10': (finetuned_metrics['recall@10'] - baseline_metrics['recall@10']) * 100,
        'ndcg@10': (finetuned_metrics['ndcg@10'] - baseline_metrics['ndcg@10']) * 100
    }
}

with open('./models/bge-large-zh-travel-finetuned/evaluation_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n结果已保存: ./models/bge-large-zh-travel-finetuned/evaluation_results.json")
