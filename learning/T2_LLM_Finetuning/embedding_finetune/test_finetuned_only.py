"""
简化版评估脚本 - 仅测试微调后的模型
避免网络问题，直接使用本地模型
"""
import os

# 强制离线模式 - 必须在 import 之前设置
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

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

    # 正确答案索引
    ground_truth = [0, 1, 2, 3, 4]

    return test_queries, documents, ground_truth

def compute_retrieval_accuracy(model, queries, documents, ground_truth):
    """计算检索准确率"""
    print("\n正在编码查询和文档...")
    query_embeddings = model.encode(queries, show_progress_bar=True)
    doc_embeddings = model.encode(documents, show_progress_bar=True)

    print("\n计算相似度矩阵...")
    similarities = cosine_similarity(query_embeddings, doc_embeddings)

    predictions = np.argmax(similarities, axis=1)

    correct = sum([1 for pred, truth in zip(predictions, ground_truth) if pred == truth])
    accuracy = correct / len(ground_truth) * 100

    print("\n" + "="*60)
    print("检索结果详情:")
    print("="*60)
    for i, (query, pred, truth) in enumerate(zip(queries, predictions, ground_truth)):
        is_correct = "[OK]" if pred == truth else "[X]"
        print(f"\n{i+1}. 查询: {query}")
        print(f"   预测文档 #{pred} | 正确文档 #{truth} | {is_correct}")
        print(f"   相似度分数: {similarities[i][pred]:.4f}")
        if pred == truth:
            print(f"   匹配内容: {documents[pred][:50]}...")

    return accuracy, predictions, similarities

def main():
    print("="*60)
    print("微调后Embedding模型评估")
    print("="*60)

    # 加载测试数据
    print("\n[1/3] 加载测试数据...")
    queries, documents, ground_truth = load_test_data()
    print(f"[OK] 测试查询: {len(queries)} 条")
    print(f"[OK] 文档库: {len(documents)} 条")

    # 加载微调后模型
    print("\n[2/3] 加载微调后的模型...")
    # 使用正确的 large 模型路径
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'bge-large-zh-travel-finetuned'))
    print(f"模型路径: {model_path}")

    try:
        model = SentenceTransformer(model_path)
        print(f"[OK] 模型加载成功")
        print(f"  - 模型维度: {model.get_sentence_embedding_dimension()}")

        # 执行评估
        print("\n[3/3] 执行检索评估...")
        accuracy, _, _ = compute_retrieval_accuracy(model, queries, documents, ground_truth)

        print("\n" + "="*60)
        print("评估结果")
        print("="*60)
        print(f"准确率: {accuracy:.1f}% ({int(accuracy * len(ground_truth) / 100)}/{len(ground_truth)} 正确)")

        if accuracy == 100.0:
            print("\n[OK] 完美！微调模型在所有测试查询上都检索到了正确的文档")
        elif accuracy >= 80.0:
            print("\n[OK] 优秀！微调模型在差旅政策检索任务上表现良好")
        elif accuracy >= 60.0:
            print("\n[!] 良好，但仍有改进空间")
        else:
            print("\n[X] 准确率较低，可能需要更多训练数据或调整超参数")

        print("\n" + "="*60)
        print("说明:")
        print("- 此评估测试模型在差旅政策检索任务上的表现")
        print("- 通过对比查询和文档的语义相似度进行检索")
        print("- 准确率 = 检索到正确文档的查询数 / 总查询数")
        print("="*60)

    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        print("请确保微调训练已完成")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
