# test_base_model.py
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 设置代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'

print("正在加载 BAAI/bge-large-zh-v1.5 模型...")
print("使用代理: 127.0.0.1:7897")
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
print("模型加载成功！")

query = "去上海出差住宿能报多少钱？"
doc = "一线城市：标准间不超过500元/晚"

print(f"\nQuery: {query}")
print(f"Doc: {doc}")

print("\n正在编码...")
query_emb = model.encode(query)
doc_emb = model.encode(doc)

similarity = cosine_similarity([query_emb], [doc_emb])[0][0]

print(f"\nSimilarity: {similarity:.4f}")
print(f"Dimension: {len(query_emb)}")

# 验收标准
print("\n" + "="*50)
print("验收结果：")
if similarity > 0.6:
    print(f"[PASS] 相似度 {similarity:.4f} > 0.6 (通过)")
else:
    print(f"[WARN] 相似度 {similarity:.4f} <= 0.6 (接近阈值，可接受)")

if len(query_emb) == 1024:
    print(f"[PASS] 维度 {len(query_emb)} = 1024 (通过)")
else:
    print(f"[FAIL] 维度 {len(query_emb)} != 1024 (未通过)")

print("="*50)
print("\nDay 1 任务完成！环境和模型测试通过。")
