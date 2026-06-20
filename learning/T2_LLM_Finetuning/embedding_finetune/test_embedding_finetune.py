"""
Embedding微调效果测试
对比微调前后模型在差旅政策检索任务上的表现
"""
import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 强制使用本地缓存，避免网络超时
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'

def load_test_data():
    """加载测试数据"""
    test_queries = [
        "经济舱机票能报销吗",
        "出差每天补贴标准",
        "商务舱预订条件",
        "住宿费用上限",
        "高铁商务座报销规定"
    ]

    documents = [
        "国内航班经济舱可以全额报销，但需要提供正规发票和行程单。",
        "出差补贴标准：国内出差每天200元，包含市内交通和餐饮补贴。",
        "商务舱仅限副总裁及以上级别，或飞行时间超过4小时的国际航班。",
        "酒店住宿标准：一线城市不超过500元/晚，二线城市不超过300元/晚。",
        "高铁出行优先选择二等座。商务座仅在总监及以上级别或特殊情况允许。",
        "机票预订需提前3天申请，紧急出差需部门经理审批。",
        "周末出差补贴标准与工作日相同，每天200元。",
        "国际出差需提前7天申请，并提交详细行程和预算。"
    ]

    # 正确答案索引 (每个query对应的最相关document)
    ground_truth = [0, 1, 2, 3, 4]

    return test_queries, documents, ground_truth

def compute_retrieval_accuracy(model, queries, documents, ground_truth):
    """计算检索准确率"""
    # 编码query和documents
    query_embeddings = model.encode(queries)
    doc_embeddings = model.encode(documents)

    # 计算相似度矩阵
    similarities = cosine_similarity(query_embeddings, doc_embeddings)

    # 对每个query找最相似的document
    predictions = np.argmax(similarities, axis=1)

    # 计算准确率
    correct = sum([1 for pred, truth in zip(predictions, ground_truth) if pred == truth])
    accuracy = correct / len(ground_truth) * 100

    # 打印详细结果
    print("\n检索结果详情:")
    for i, (query, pred, truth) in enumerate(zip(queries, predictions, ground_truth)):
        is_correct = "OK" if pred == truth else "X"
        print(f"{i+1}. Query: {query[:20]}...")
        print(f"   预测文档#{pred} | 正确文档#{truth} | {is_correct}")
        print(f"   相似度分数: {similarities[i][pred]:.4f}")

    return accuracy, predictions, similarities

def test_embedding_finetune():
    """测试微调前后的效果对比"""
    print("="*60)
    print("Embedding微调效果测试")
    print("="*60)

    # 加载测试数据
    print("\n[Step 1] 加载测试数据...")
    queries, documents, ground_truth = load_test_data()
    print(f"[OK] 测试查询: {len(queries)} 条")
    print(f"[OK] 文档库: {len(documents)} 条")

    # 测试基础模型（微调前）
    print("\n[Step 2] 测试基础模型（微调前）...")
    print("加载模型: BAAI/bge-large-zh-v1.5")
    base_model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
    acc_before, _, _ = compute_retrieval_accuracy(base_model, queries, documents, ground_truth)
    print(f"\n基础模型准确率: {acc_before:.1f}%")

    # 测试微调后模型
    print("\n" + "="*60)
    print("[Step 3] 测试微调后的模型...")

    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, 'finetuned_model')
    print(f"加载模型: {model_path}")

    try:
        finetuned_model = SentenceTransformer(model_path)
        acc_after, _, _ = compute_retrieval_accuracy(finetuned_model, queries, documents, ground_truth)
        print(f"\n微调后准确率: {acc_after:.1f}%")

        # 对比结果
        print("\n" + "="*60)
        print("效果对比")
        print("="*60)
        print(f"基础模型: {acc_before:.1f}%")
        print(f"微调后: {acc_after:.1f}%")
        print(f"提升: {'+' if acc_after >= acc_before else ''}{acc_after - acc_before:.1f}%")

        if acc_after > acc_before:
            print("\n[OK] 微调成功！模型在差旅政策检索任务上表现提升")
        elif acc_after == acc_before:
            print("\n[!] 微调后准确率持平，可能需要更多训练数据或调整超参数")
        else:
            print("\n[!] 微调后准确率下降，可能过拟合或数据质量问题")

    except Exception as e:
        print(f"[ERROR] 无法加载微调后的模型: {e}")
        print("请先运行 finetune_embedding.py 完成模型微调")
        return

    print("\n" + "="*60)
    print("[!] 这就是微调验证：用测试集量化模型改进效果")
    print("与YOLOv8类比：用验证集测量mAP50提升")
    print("="*60)

if __name__ == "__main__":
    test_embedding_finetune()
