"""
评估配置2：基础模型 + Query重写流程

任务：
1. 加载基础模型：BAAI/bge-large-zh-v1.5
2. 创建混合检索器（启用EnterpriseQueryRewriter）
3. 对20个测试查询执行检索
4. 记录重写前后的查询对比
5. 计算指标：Accuracy@1, Recall@5, MRR
6. 按难度分级统计，特别关注Medium级别改善
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import os

# 添加项目根目录到path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.chat_models import ChatTongyi
from src.modules.module_2_advanced_rag.query_rewriter import EnterpriseQueryRewriter


def load_base_model(model_path: str) -> HuggingFaceEmbeddings:
    """加载基础embedding模型"""
    print(f"Loading base model: {model_path}")
    embeddings = HuggingFaceEmbeddings(
        model_name=model_path,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    return embeddings


def create_vector_store(documents: List[Dict], embeddings: HuggingFaceEmbeddings) -> FAISS:
    """创建向量存储"""
    print(f"Creating vector store with {len(documents)} documents...")

    # 转换为Document对象
    docs = []
    for doc in documents:
        docs.append(Document(
            page_content=doc["content"],
            metadata={"doc_id": doc["doc_id"]}
        ))

    # 创建FAISS索引
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore


def setup_query_rewriter() -> EnterpriseQueryRewriter:
    """设置查询重写器"""
    print("Setting up query rewriter...")

    # 使用Tongyi Qwen作为重写LLM
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未找到DASHSCOPE_API_KEY环境变量")

    llm = ChatTongyi(
        model="qwen-plus",
        temperature=0.1,
        dashscope_api_key=api_key
    )

    rewriter = EnterpriseQueryRewriter(llm)
    return rewriter


def retrieve_with_rewriting(
    query: str,
    vectorstore: FAISS,
    rewriter: EnterpriseQueryRewriter,
    k: int = 5
) -> Tuple[str, List[str]]:
    """
    使用查询重写进行检索

    Returns:
        (rewritten_query, retrieved_doc_ids)
    """
    # 重写查询
    rewritten_query = rewriter.rewrite(query)

    # 检索
    results = vectorstore.similarity_search(rewritten_query, k=k)
    doc_ids = [doc.metadata["doc_id"] for doc in results]

    return rewritten_query, doc_ids


def calculate_metrics(
    test_queries: List[Dict],
    retrieval_results: List[Dict]
) -> Dict[str, Any]:
    """
    计算评估指标

    指标：
    - Accuracy@1: top-1准确率
    - Recall@5: top-5召回率
    - MRR: Mean Reciprocal Rank
    """
    accuracy_at_1 = 0
    recall_at_5 = 0
    mrr_sum = 0.0
    total = 0

    # 按难度分级统计
    by_difficulty = {
        "easy": {"correct": 0, "total": 0},
        "medium": {"correct": 0, "total": 0},
        "hard": {"correct": 0, "total": 0},
        "distractor": {"correct": 0, "total": 0}
    }

    failed_queries = []

    for query_data, result in zip(test_queries, retrieval_results):
        expected_doc_id = query_data["expected_doc_id"]
        difficulty = query_data["difficulty"]
        retrieved_ids = result["retrieved_doc_ids"]

        # 跳过distractor查询
        if difficulty == "distractor":
            by_difficulty[difficulty]["total"] += 1
            continue

        total += 1
        by_difficulty[difficulty]["total"] += 1

        # Accuracy@1
        if len(retrieved_ids) > 0 and retrieved_ids[0] == expected_doc_id:
            accuracy_at_1 += 1
            by_difficulty[difficulty]["correct"] += 1

        # Recall@5
        if expected_doc_id in retrieved_ids[:5]:
            recall_at_5 += 1

        # MRR
        try:
            rank = retrieved_ids.index(expected_doc_id) + 1
            mrr_sum += 1.0 / rank
        except ValueError:
            # 未检索到，记录失败案例
            failed_queries.append({
                "query": query_data["query"],
                "expected": expected_doc_id,
                "retrieved": retrieved_ids[:3],
                "difficulty": difficulty,
                "rewritten_query": result["rewritten_query"]
            })

    # 计算指标
    metrics = {
        "accuracy_at_1": accuracy_at_1 / total if total > 0 else 0,
        "recall_at_5": recall_at_5 / total if total > 0 else 0,
        "mrr": mrr_sum / total if total > 0 else 0,
        "by_difficulty": {},
        "failed_queries": failed_queries
    }

    # 按难度计算准确率
    for difficulty, stats in by_difficulty.items():
        if stats["total"] > 0:
            metrics["by_difficulty"][difficulty] = {
                "accuracy": stats["correct"] / stats["total"],
                "correct": stats["correct"],
                "total": stats["total"]
            }
        else:
            metrics["by_difficulty"][difficulty] = {
                "accuracy": 0,
                "correct": 0,
                "total": 0
            }

    return metrics


def main():
    """主评估流程"""

    # 测试数据
    test_data = {
        "base_model_path": "BAAI/bge-large-zh-v1.5",
        "test_queries": [
            {"query": "去北京出差能住什么价位的酒店？", "expected_doc_id": "doc_06", "difficulty": "easy"},
            {"query": "经济舱的机票可以报销吗？", "expected_doc_id": "doc_05", "difficulty": "easy"},
            {"query": "出差补贴一天给多少钱？", "expected_doc_id": "doc_02", "difficulty": "easy"},
            {"query": "火车票能报销吗？", "expected_doc_id": "doc_09", "difficulty": "easy"},
            {"query": "出差住宿发票丢了怎么办？", "expected_doc_id": "doc_01", "difficulty": "easy"},
            {"query": "去魔都出差住宿预算多少？", "expected_doc_id": "doc_08", "difficulty": "medium"},
            {"query": "副总裁能坐商务舱吗？", "expected_doc_id": "doc_23", "difficulty": "medium"},
            {"query": "从北京到成都应该坐飞机还是高铁？", "expected_doc_id": "doc_15", "difficulty": "medium"},
            {"query": "周末加班出差有额外补贴吗？", "expected_doc_id": "doc_13", "difficulty": "medium"},
            {"query": "出差期间生病就医费用能报吗？", "expected_doc_id": "doc_01", "difficulty": "medium"},
            {"query": "一次出差去多个城市，住宿标准怎么算？", "expected_doc_id": "doc_08", "difficulty": "medium"},
            {"query": "提前预订机票有折扣吗？", "expected_doc_id": "doc_03", "difficulty": "medium"},
            {"query": "商务舱和经济舱的差别是什么？", "expected_doc_id": "doc_23", "difficulty": "hard"},
            {"query": "杭州属于几线城市？住宿标准是多少？", "expected_doc_id": "doc_08", "difficulty": "hard"},
            {"query": "国际出差的政策和国内一样吗？", "expected_doc_id": "doc_14", "difficulty": "hard"},
            {"query": "出差超过一个月，标准有变化吗？", "expected_doc_id": "doc_20", "difficulty": "hard"},
            {"query": "CEO出差有什么特殊待遇？", "expected_doc_id": "doc_28", "difficulty": "hard"},
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

    print("="*80)
    print("评估配置2：基础模型 + Query重写流程")
    print("="*80)

    # Step 1: 加载基础模型
    embeddings = load_base_model(test_data["base_model_path"])

    # Step 2: 创建向量存储
    vectorstore = create_vector_store(test_data["documents"], embeddings)

    # Step 3: 设置查询重写器
    rewriter = setup_query_rewriter()

    # Step 4: 执行检索并记录结果
    print("\n" + "="*80)
    print("执行检索（共20个查询）")
    print("="*80)

    retrieval_results = []
    query_rewrites = []

    for i, query_data in enumerate(test_data["test_queries"], 1):
        query = query_data["query"]
        expected = query_data["expected_doc_id"]
        difficulty = query_data["difficulty"]

        print(f"\n[{i}/20] Query: {query}")
        print(f"Expected: {expected} | Difficulty: {difficulty}")

        # 检索
        rewritten_query, retrieved_ids = retrieve_with_rewriting(
            query, vectorstore, rewriter, k=5
        )

        print(f"Rewritten: {rewritten_query}")
        print(f"Retrieved: {retrieved_ids[:3]}")

        # 记录结果
        retrieval_results.append({
            "query": query,
            "rewritten_query": rewritten_query,
            "retrieved_doc_ids": retrieved_ids,
            "expected_doc_id": expected,
            "difficulty": difficulty
        })

        # 记录查询重写对比
        query_rewrites.append({
            "original": query,
            "rewritten": rewritten_query,
            "changed": query != rewritten_query
        })

    # Step 5: 计算指标
    print("\n" + "="*80)
    print("计算评估指标")
    print("="*80)

    metrics = calculate_metrics(test_data["test_queries"], retrieval_results)

    # Step 6: 输出结果
    print("\n" + "="*80)
    print("评估结果")
    print("="*80)

    print(f"\n【总体指标】")
    print(f"Accuracy@1: {metrics['accuracy_at_1']:.2%}")
    print(f"Recall@5: {metrics['recall_at_5']:.2%}")
    print(f"MRR: {metrics['mrr']:.4f}")

    print(f"\n【按难度分级】")
    for difficulty in ["easy", "medium", "hard"]:
        stats = metrics["by_difficulty"][difficulty]
        print(f"{difficulty.upper()}: {stats['accuracy']:.2%} ({stats['correct']}/{stats['total']})")

    print(f"\n【查询重写统计】")
    total_rewrites = sum(1 for qr in query_rewrites if qr["changed"])
    print(f"重写率: {total_rewrites}/{len(query_rewrites)} ({total_rewrites/len(query_rewrites):.1%})")

    print(f"\n【失败案例】({len(metrics['failed_queries'])}个)")
    for fail in metrics["failed_queries"][:5]:  # 只显示前5个
        print(f"\nQuery: {fail['query']}")
        print(f"Rewritten: {fail['rewritten_query']}")
        print(f"Expected: {fail['expected']}")
        print(f"Retrieved: {fail['retrieved']}")

    # 构建返回的JSON结果
    result = {
        "config": "base_model_with_query_rewriting",
        "accuracy_at_1": metrics["accuracy_at_1"],
        "recall_at_5": metrics["recall_at_5"],
        "mrr": metrics["mrr"],
        "by_difficulty": metrics["by_difficulty"],
        "query_rewrites": query_rewrites,
        "failed_queries": metrics["failed_queries"]
    }

    # 输出JSON结果
    print("\n" + "="*80)
    print("JSON结果")
    print("="*80)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result


if __name__ == "__main__":
    result = main()
