"""
Hard Negative Mining for Embedding Fine-tuning
为每个query添加3个难负样本（最相似但不是正样本的文档）
"""

import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from tqdm import tqdm

# 1. 加载基础模型
print("加载BGE-large-zh-v1.5模型...")
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

# 2. 加载政策文档和训练数据
print("加载数据...")
with open('policy_docs.json', 'r', encoding='utf-8') as f:
    policy_docs = json.load(f)

with open('training_data_raw.json', 'r', encoding='utf-8') as f:
    training_data = json.load(f)

# 3. 对所有政策文档进行编码（只需编码一次）
print("编码所有政策文档...")
doc_embeddings = model.encode(policy_docs, show_progress_bar=True)

# 4. 为每个训练样本添加hard negatives
print("\n开始Hard Negative Mining...")
for idx, item in enumerate(tqdm(training_data, desc="处理训练数据")):
    query = item['query']
    positive_doc = item['positive']

    # 编码query
    query_embedding = model.encode(query)

    # 计算query与所有文档的相似度
    similarities = cosine_similarity([query_embedding], doc_embeddings)[0]

    # 创建(索引, 相似度)对列表
    doc_sim_pairs = [(i, sim) for i, sim in enumerate(similarities)]

    # 按相似度降序排序
    doc_sim_pairs.sort(key=lambda x: x[1], reverse=True)

    # 找出positive文档在policy_docs中的索引
    positive_idx = policy_docs.index(positive_doc)

    # 选择3个hard negatives（排除positive文档）
    hard_negatives = []
    for doc_idx, sim in doc_sim_pairs:
        if doc_idx != positive_idx:  # 排除正样本
            hard_negatives.append(policy_docs[doc_idx])
            if len(hard_negatives) == 3:
                break

    # 添加到训练数据
    item['negatives'] = hard_negatives

    # 每20个样本打印一次示例
    if idx % 20 == 0:
        print(f"\n示例 {idx}:")
        print(f"Query: {query}")
        print(f"Positive: {positive_doc[:50]}...")
        print(f"Hard Negatives:")
        for i, neg in enumerate(hard_negatives, 1):
            print(f"  {i}. {neg[:50]}...")

# 5. 保存最终的训练数据
output_file = 'training_data_final.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(training_data, f, ensure_ascii=False, indent=2)

print(f"\n[OK] Hard Negative Mining完成！")
print(f"[统计信息]")
print(f"  - 总样本数: {len(training_data)}")
print(f"  - 政策文档数: {len(policy_docs)}")
print(f"  - 每个样本的hard negatives数量: 3")
print(f"  - 输出文件: {output_file}")

# 6. 验证数据质量
print("\n[数据质量验证]")
all_have_negatives = all(len(item['negatives']) == 3 for item in training_data)
no_positive_in_negatives = all(
    item['positive'] not in item['negatives']
    for item in training_data
)

print(f"  - 所有样本都有3个negatives: {all_have_negatives}")
print(f"  - 所有negatives都不包含positive: {no_positive_in_negatives}")

if all_have_negatives and no_positive_in_negatives:
    print("\n[OK] 数据质量验证通过！")
else:
    print("\n[ERROR] 数据质量验证失败，请检查！")
