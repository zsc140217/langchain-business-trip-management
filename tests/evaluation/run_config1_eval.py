"""
评估配置1：基础模型 + 无重写流程

评估RAG检索质量的核心指标：
- Accuracy@1: 第一个检索结果是否正确
- Recall@5: 前5个检索结果是否包含正确答案
- MRR (Mean Reciprocal Rank): 第一个正确结果的位置倒数的平均值

评估流程：
1. 加载基础嵌入模型（BAAI/bge-large-zh-v1.5）
2. 创建FAISS向量存储（使用提供的文档）
3. 对每个测试查询执行检索（k=5）
4. 计算评估指标
5. 按难度分级统计
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import time

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


def calculate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算评估指标"""
    total = len(results)

    # Accuracy@1: 第一个结果正确的比例
    accuracy_at_1 = sum(1 for r in results if r["rank"] == 1) / total if total > 0 else 0

    # Recall@5: 前5个结果包含正确答案的比例
    recall_at_5 = sum(1 for r in results if r["rank"] is not None and r["rank"] <= 5) / total if total > 0 else 0

    # MRR: Mean Reciprocal Rank
    mrr_sum = sum(1.0 / r["rank"] if r["rank"] is not None else 0 for r in results)
    mrr = mrr_sum / total if total > 0 else 0

    return {
        "accuracy_at_1": round(accuracy_at_1, 4),
        "recall_at_5": round(recall_at_5, 4),
        "mrr": round(mrr, 4)
    }


def calculate_by_difficulty(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """按难度分级统计"""
    by_difficulty = {}

    for difficulty in ["easy", "medium", "hard"]:
        filtered = [r for r in results if r["difficulty"] == difficulty]
        if filtered:
            by_difficulty[difficulty] = calculate_metrics(filtered)
        else:
            by_difficulty[difficulty] = {
                "accuracy_at_1": 0.0,
                "recall_at_5": 0.0,
                "mrr": 0.0
            }

    return by_difficulty


def load_embedding_model(model_path: str) -> HuggingFaceBgeEmbeddings:
    """加载嵌入模型"""
    print(f"Loading embedding model from: {model_path}")

    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": True}

    embeddings = HuggingFaceBgeEmbeddings(
        model_name=model_path,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    print("Model loaded successfully")
    return embeddings


def create_vector_store(documents: List[Dict[str, str]], embeddings) -> FAISS:
    """创建FAISS向量存储"""
    print(f"Creating FAISS vector store with {len(documents)} documents...")

    # 转换为LangChain Document对象
    docs = [
        Document(
            page_content=doc["content"],
            metadata={"doc_id": doc["doc_id"]}
        )
        for doc in documents
    ]

    # 创建FAISS向量存储
    vectorstore = FAISS.from_documents(docs, embeddings)

    print("Vector store created successfully")
    return vectorstore


def retrieve_and_evaluate(
    vectorstore: FAISS,
    test_queries: List[Dict[str, str]],
    k: int = 5
) -> List[Dict[str, Any]]:
    """执行检索并评估"""
    results = []
    failed_queries = []

    print(f"\nEvaluating {len(test_queries)} queries...")

    for i, query_info in enumerate(test_queries, 1):
        query = query_info["query"]
        expected_doc_id = query_info["expected_doc_id"]
        difficulty = query_info["difficulty"]

        # 跳过干扰项
        if difficulty == "distractor":
            continue

        print(f"[{i}/{len(test_queries)}] Query: {query}")

        try:
            # 执行检索
            retrieved_docs = vectorstore.similarity_search(query, k=k)

            # 提取doc_id
            retrieved_doc_ids = [doc.metadata.get("doc_id", "") for doc in retrieved_docs]

            # 查找正确答案的位置
            rank = None
            for idx, doc_id in enumerate(retrieved_doc_ids, 1):
                if expected_doc_id in doc_id or doc_id in expected_doc_id:
                    rank = idx
                    break

            result = {
                "query": query,
                "expected_doc_id": expected_doc_id,
                "difficulty": difficulty,
                "retrieved_doc_ids": retrieved_doc_ids,
                "rank": rank,
                "found": rank is not None
            }

            results.append(result)

            print(f"  Expected: {expected_doc_id}")
            print(f"  Retrieved: {retrieved_doc_ids}")
            print(f"  Rank: {rank if rank else 'Not found'}")

            if not rank:
                failed_queries.append({
                    "query": query,
                    "expected": expected_doc_id,
                    "retrieved": retrieved_doc_ids
                })

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "query": query,
                "expected_doc_id": expected_doc_id,
                "difficulty": difficulty,
                "retrieved_doc_ids": [],
                "rank": None,
                "found": False,
                "error": str(e)
            })

    return results, failed_queries


def run_evaluation(test_data: Dict[str, Any]) -> Dict[str, Any]:
    """运行完整评估流程"""
    print("="*80)
    print("评估配置1：基础模型 + 无重写流程")
    print("="*80)

    start_time = time.time()

    # 1. 加载嵌入模型
    embeddings = load_embedding_model(test_data["base_model_path"])

    # 2. 创建向量存储
    vectorstore = create_vector_store(test_data["documents"], embeddings)

    # 3. 执行检索和评估
    results, failed_queries = retrieve_and_evaluate(vectorstore, test_data["test_queries"])

    # 4. 计算指标
    overall_metrics = calculate_metrics(results)
    by_difficulty = calculate_by_difficulty(results)

    # 5. 构建最终结果
    evaluation_result = {
        "config": "config1_base_model_no_rewrite",
        "accuracy_at_1": overall_metrics["accuracy_at_1"],
        "recall_at_5": overall_metrics["recall_at_5"],
        "mrr": overall_metrics["mrr"],
        "by_difficulty": by_difficulty,
        "failed_queries": failed_queries,
        "metadata": {
            "total_queries": len(results),
            "model_path": test_data["base_model_path"],
            "evaluation_time": round(time.time() - start_time, 2),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    }

    # 6. 打印结果
    print("\n" + "="*80)
    print("评估结果")
    print("="*80)
    print(f"Accuracy@1: {overall_metrics['accuracy_at_1']:.4f}")
    print(f"Recall@5:   {overall_metrics['recall_at_5']:.4f}")
    print(f"MRR:        {overall_metrics['mrr']:.4f}")
    print("\n按难度分级:")
    for difficulty, metrics in by_difficulty.items():
        print(f"\n{difficulty.upper()}:")
        print(f"  Accuracy@1: {metrics['accuracy_at_1']:.4f}")
        print(f"  Recall@5:   {metrics['recall_at_5']:.4f}")
        print(f"  MRR:        {metrics['mrr']:.4f}")

    print(f"\n失败查询数: {len(failed_queries)}")
    print(f"评估耗时: {evaluation_result['metadata']['evaluation_time']}秒")
    print("="*80)

    return evaluation_result


def main():
    """主函数"""
    # 测试数据
    test_data = {
        "base_model_path": "BAAI/bge-large-zh-v1.5",
        "finetuned_model_path": "learning/T2_LLM_Finetuning/embedding_finetune/checkpoints",
        "test_queries": [
            {"query": "去北京出差能住什么价位的酒店？", "expected_doc_id": "一线城市", "difficulty": "easy"},
            {"query": "经济舱的机票可以报销吗？", "expected_doc_id": "经济舱", "difficulty": "easy"},
            {"query": "出差补贴一天给多少钱？", "expected_doc_id": "补贴标准", "difficulty": "easy"},
            {"query": "火车票能报销吗？", "expected_doc_id": "高铁", "difficulty": "easy"},
            {"query": "出差住宿发票丢了怎么办？", "expected_doc_id": "发票", "difficulty": "easy"},
            {"query": "去魔都出差住宿预算多少？", "expected_doc_id": "上海", "difficulty": "medium"},
            {"query": "副总裁能坐商务舱吗？", "expected_doc_id": "副总裁", "difficulty": "medium"},
            {"query": "从北京到成都应该坐飞机还是高铁？", "expected_doc_id": "500公里", "difficulty": "medium"},
            {"query": "周末加班出差有额外补贴吗？", "expected_doc_id": "周末", "difficulty": "medium"},
            {"query": "出差期间生病就医费用能报吗？", "expected_doc_id": "特殊情况", "difficulty": "medium"},
            {"query": "一次出差去多个城市，住宿标准怎么算？", "expected_doc_id": "城市", "difficulty": "medium"},
            {"query": "提前预订机票有折扣吗？", "expected_doc_id": "提前预订", "difficulty": "medium"},
            {"query": "商务舱和经济舱的差别是什么？", "expected_doc_id": "商务舱", "difficulty": "hard"},
            {"query": "杭州属于几线城市？住宿标准是多少？", "expected_doc_id": "二线城市", "difficulty": "hard"},
            {"query": "国际出差的政策和国内一样吗？", "expected_doc_id": "国际", "difficulty": "hard"},
            {"query": "出差超过一个月，标准有变化吗？", "expected_doc_id": "长期", "difficulty": "hard"},
            {"query": "CEO出差有什么特殊待遇？", "expected_doc_id": "CEO", "difficulty": "hard"},
            {"query": "公司年会预算是多少？", "expected_doc_id": "distractor", "difficulty": "distractor"},
            {"query": "员工入职需要什么材料？", "expected_doc_id": "distractor", "difficulty": "distractor"},
            {"query": "如何申请年假？", "expected_doc_id": "distractor", "difficulty": "distractor"}
        ],
        "documents": [
            {"doc_id": "doc_01", "content": "报销材料清单：1)差旅申请单（已审批）2)机票行程单或火车票 3)酒店发票 4)其他交通费发票 5)费用明细表。所有材料需在出差结束后10个工作日内提交。"},
            {"doc_id": "doc_02", "content": "每日200元出差补贴包含市内交通和餐饮补贴。机场往返可单独报销。"},
            {"doc_id": "doc_03", "content": "机票报销需提供行程单和发票。经济舱全额报销，商务舱需符合职级或航程要求。"},
            {"doc_id": "doc_04", "content": "国际出差需提前7天申请，并提交详细行程和预算。国内出差提前3天即可。"},
            {"doc_id": "doc_05", "content": "国内航班经济舱可以全额报销，需提供发票和行程单，票价应合理。"},
            {"doc_id": "doc_06", "content": "酒店住宿标准：一线城市（北上广深）不超过500元/晚，超出部分自付。"},
            {"doc_id": "doc_07", "content": "市内交通费用包含在每日200元补贴中。机场往返可单独报销出租车或机场大巴费用，需提供发票。"},
            {"doc_id": "doc_08", "content": "酒店住宿标准：一线城市500元/晚，二线300元/晚，三线200元/晚。超出部分需自付。"},
            {"doc_id": "doc_09", "content": "高铁出行优先选择二等座，可正常报销。商务座需总监级别或特殊情况。"},
            {"doc_id": "doc_10", "content": "国内航班经济舱可以全额报销，但需要提供正规发票和行程单。票价应在市场合理范围内。"},
            {"doc_id": "doc_11", "content": "一线城市（北上广深）酒店住宿不超过500元/晚。二线城市300元/晚，三线城市200元/晚。"},
            {"doc_id": "doc_12", "content": "国内出差每天补贴200元，包含市内交通和餐饮补贴。周末出差标准不变。"},
            {"doc_id": "doc_13", "content": "周末出差补贴标准与工作日相同，每天200元。如占用休息日，可申请调休，调休时长为实际出差天数。"},
            {"doc_id": "doc_14", "content": "国际航班：飞行时间4小时以内经济舱，4小时以上可申请商务舱（需总监审批）。跨洲际航班（8小时以上）商务舱自动批准。"},
            {"doc_id": "doc_15", "content": "高铁出行优先选择二等座。商务座仅在以下情况允许：1)总监及以上级别 2)特殊健康原因并提供证明 3)二等座已售罄。"},
            {"doc_id": "doc_16", "content": "差旅审批流程：国内出差需提前3天申请，国际出差需提前7天申请。紧急出差（48小时内）需部门经理特批。"},
            {"doc_id": "doc_17", "content": "机票报销需要提供正规发票和行程单。经济舱可全额报销，票价需在合理范围。"},
            {"doc_id": "doc_18", "content": "高铁优先二等座。商务座仅在以下情况允许：总监及以上级别、健康原因有证明、二等座售罄。"},
            {"doc_id": "doc_19", "content": "酒店住宿标准：一线城市（北上广深）不超过500元/晚，二线城市不超过300元/晚，三线城市不超过200元/晚。超出部分自付。"},
            {"doc_id": "doc_20", "content": "出差补贴标准：国内出差每天200元，涵盖市内交通和餐饮。周末出差补贴相同。"},
            {"doc_id": "doc_21", "content": "国内航班经济舱可以全额报销，但需要提供正规发票和行程单。经济舱票价应在市场合理范围内。"},
            {"doc_id": "doc_22", "content": "差旅审批流程：国内出差需提前3天申请。紧急出差（48小时内）需部门经理特批。"},
            {"doc_id": "doc_23", "content": "商务舱报销需满足：1)副总裁及以上 2)国际航班4小时+ 3)跨洲际8小时+。其他情况只能报销经济舱。"},
            {"doc_id": "doc_24", "content": "普通员工不得预订商务舱或头等舱。商务舱仅限副总裁及以上级别或长途国际航班。"},
            {"doc_id": "doc_25", "content": "出差补贴标准：国内出差每天200元，包含市内交通和餐饮补贴。周末出差补贴标准不变。"},
            {"doc_id": "doc_26", "content": "高铁商务座允许条件：1)总监及以上级别 2)特殊健康原因并提供证明 3)二等座已售罄。否则优先二等座。"},
            {"doc_id": "doc_27", "content": "商务舱仅限高管或长途国际航班。普通员工预订商务舱或头等舱不予报销。"},
            {"doc_id": "doc_28", "content": "商务舱预订条件：副总裁及以上级别，或国际航班飞行4小时以上。跨洲际航班（8小时+）商务舱自动批准。"},
            {"doc_id": "doc_29", "content": "商务舱仅限副总裁及以上级别，或飞行时间超过4小时的国际航班。普通员工不得预订商务舱或头等舱。"}
        ]
    }

    # 运行评估
    result = run_evaluation(test_data)

    # 输出JSON结果
    print("\n" + "="*80)
    print("JSON格式结果:")
    print("="*80)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result


if __name__ == "__main__":
    result = main()
