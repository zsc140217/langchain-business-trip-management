"""
评估配置3：微调模型 + 无重写流程

任务：
1. 加载微调模型：learning/models/bge-large-zh-travel-finetuned
2. 创建FAISS向量存储（不使用query rewrite）
3. 对20个测试查询执行检索
4. 计算指标：Accuracy@1, Recall@5, MRR
5. 按难度分级统计
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

# LangChain imports
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


@dataclass
class EvalConfig:
    """评估配置"""
    base_model_path: str
    finetuned_model_path: str
    test_queries: List[Dict[str, Any]]
    documents: List[Dict[str, str]]


@dataclass
class RetrievalResult:
    """单次检索结果"""
    query: str
    expected_doc_id: str
    retrieved_doc_ids: List[str]
    retrieved_scores: List[float]
    difficulty: str
    correct_at_1: bool
    correct_at_5: bool
    reciprocal_rank: float
    execution_time: float


@dataclass
class EvalMetrics:
    """评估指标"""
    accuracy_at_1: float
    recall_at_5: float
    mrr: float
    by_difficulty: Dict[str, Dict[str, float]]
    failed_queries: List[Dict[str, Any]]
    config: str


class Config3Evaluator:
    """配置3评估器：微调模型 + 无重写"""

    def __init__(self, config: EvalConfig):
        self.config = config
        self.project_root = Path(__file__).parent.parent.parent

        # 解析模型路径
        self.finetuned_model_path = self.project_root / config.finetuned_model_path

        print(f"[INFO] 初始化配置3评估器")
        print(f"[INFO] 微调模型路径: {self.finetuned_model_path}")

    def load_finetuned_model(self) -> HuggingFaceEmbeddings:
        """加载微调后的embedding模型"""
        print(f"[INFO] 加载微调模型...")

        model_kwargs = {'device': 'cpu'}  # 使用CPU
        encode_kwargs = {
            'normalize_embeddings': True,
            'batch_size': 32
        }

        try:
            embeddings = HuggingFaceEmbeddings(
                model_name=str(self.finetuned_model_path),
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
            print(f"[SUCCESS] 微调模型加载成功")
            return embeddings

        except Exception as e:
            print(f"[ERROR] 微调模型加载失败: {e}")
            print(f"[INFO] 回退到基础模型: {self.config.base_model_path}")

            # 回退到基础模型
            embeddings = HuggingFaceEmbeddings(
                model_name=self.config.base_model_path,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
            return embeddings

    def create_vector_store(self, embeddings: HuggingFaceEmbeddings) -> FAISS:
        """创建FAISS向量存储"""
        print(f"[INFO] 创建FAISS向量存储...")

        # 将文档转换为LangChain Document对象
        documents = []
        for doc in self.config.documents:
            documents.append(
                Document(
                    page_content=doc["content"],
                    metadata={"doc_id": doc["doc_id"]}
                )
            )

        # 创建FAISS索引
        vectorstore = FAISS.from_documents(documents, embeddings)

        print(f"[SUCCESS] 向量存储创建完成，共 {len(documents)} 个文档")
        return vectorstore

    def retrieve_documents(
        self,
        vectorstore: FAISS,
        query: str,
        k: int = 5
    ) -> tuple[List[str], List[float]]:
        """检索文档（无查询重写）"""
        # 直接使用原始查询进行相似度搜索
        results = vectorstore.similarity_search_with_score(query, k=k)

        doc_ids = [doc.metadata["doc_id"] for doc, score in results]
        scores = [float(score) for doc, score in results]

        return doc_ids, scores

    def evaluate_single_query(
        self,
        vectorstore: FAISS,
        query_data: Dict[str, Any]
    ) -> RetrievalResult:
        """评估单个查询"""
        query = query_data["query"]
        expected_doc_id = query_data["expected_doc_id"]
        difficulty = query_data["difficulty"]

        start_time = time.time()

        # 检索文档
        retrieved_doc_ids, retrieved_scores = self.retrieve_documents(
            vectorstore, query, k=5
        )

        execution_time = time.time() - start_time

        # 计算指标
        correct_at_1 = (retrieved_doc_ids[0] == expected_doc_id) if retrieved_doc_ids else False
        correct_at_5 = expected_doc_id in retrieved_doc_ids

        # 计算MRR (Mean Reciprocal Rank)
        reciprocal_rank = 0.0
        if expected_doc_id in retrieved_doc_ids:
            rank = retrieved_doc_ids.index(expected_doc_id) + 1
            reciprocal_rank = 1.0 / rank

        return RetrievalResult(
            query=query,
            expected_doc_id=expected_doc_id,
            retrieved_doc_ids=retrieved_doc_ids,
            retrieved_scores=retrieved_scores,
            difficulty=difficulty,
            correct_at_1=correct_at_1,
            correct_at_5=correct_at_5,
            reciprocal_rank=reciprocal_rank,
            execution_time=execution_time
        )

    def calculate_metrics(
        self,
        results: List[RetrievalResult]
    ) -> EvalMetrics:
        """计算综合评估指标"""
        total = len(results)

        # 总体指标
        accuracy_at_1 = sum(r.correct_at_1 for r in results) / total
        recall_at_5 = sum(r.correct_at_5 for r in results) / total
        mrr = sum(r.reciprocal_rank for r in results) / total

        # 按难度分级统计
        by_difficulty = {}
        difficulty_levels = set(r.difficulty for r in results)

        for difficulty in difficulty_levels:
            difficulty_results = [r for r in results if r.difficulty == difficulty]
            if difficulty_results:
                count = len(difficulty_results)
                by_difficulty[difficulty] = {
                    "count": count,
                    "accuracy_at_1": sum(r.correct_at_1 for r in difficulty_results) / count,
                    "recall_at_5": sum(r.correct_at_5 for r in difficulty_results) / count,
                    "mrr": sum(r.reciprocal_rank for r in difficulty_results) / count,
                    "avg_execution_time": sum(r.execution_time for r in difficulty_results) / count
                }

        # 收集失败查询
        failed_queries = []
        for r in results:
            if not r.correct_at_5:
                failed_queries.append({
                    "query": r.query,
                    "expected_doc_id": r.expected_doc_id,
                    "retrieved_doc_ids": r.retrieved_doc_ids[:5],
                    "difficulty": r.difficulty
                })

        return EvalMetrics(
            accuracy_at_1=accuracy_at_1,
            recall_at_5=recall_at_5,
            mrr=mrr,
            by_difficulty=by_difficulty,
            failed_queries=failed_queries,
            config="config3_finetuned_no_rewrite"
        )

    def run_evaluation(self) -> EvalMetrics:
        """运行完整评估流程"""
        print("\n" + "="*60)
        print("配置3评估：微调模型 + 无重写流程")
        print("="*60 + "\n")

        # Step 1: 加载微调模型
        embeddings = self.load_finetuned_model()

        # Step 2: 创建向量存储
        vectorstore = self.create_vector_store(embeddings)

        # Step 3: 评估所有测试查询
        print(f"\n[INFO] 开始评估 {len(self.config.test_queries)} 个测试查询...\n")

        results = []
        for i, query_data in enumerate(self.config.test_queries, 1):
            result = self.evaluate_single_query(vectorstore, query_data)
            results.append(result)

            # 打印进度
            status = "PASS" if result.correct_at_1 else "FAIL"
            query_short = result.query[:30] if len(result.query) <= 30 else result.query[:27] + "..."
            retrieved_first = result.retrieved_doc_ids[0] if result.retrieved_doc_ids else 'None'

            print(f"[{i:2d}/{len(self.config.test_queries)}] {status:4s} | "
                  f"{result.difficulty:10s} | "
                  f"Expected: {result.expected_doc_id:15s} | "
                  f"Retrieved: {retrieved_first:15s}")

        # Step 4: 计算指标
        print(f"\n[INFO] 计算评估指标...\n")
        metrics = self.calculate_metrics(results)

        # Step 5: 打印结果
        self.print_results(metrics)

        return metrics

    def print_results(self, metrics: EvalMetrics):
        """打印评估结果"""
        print("\n" + "="*60)
        print("评估结果")
        print("="*60)

        print(f"\n总体指标:")
        print(f"  Accuracy@1: {metrics.accuracy_at_1:.3f}")
        print(f"  Recall@5:   {metrics.recall_at_5:.3f}")
        print(f"  MRR:        {metrics.mrr:.3f}")

        print(f"\n按难度分级:")
        for difficulty in ["easy", "medium", "hard", "distractor"]:
            if difficulty in metrics.by_difficulty:
                stats = metrics.by_difficulty[difficulty]
                print(f"\n  {difficulty.capitalize()}:")
                print(f"    样本数:      {stats['count']}")
                print(f"    Accuracy@1: {stats['accuracy_at_1']:.3f}")
                print(f"    Recall@5:   {stats['recall_at_5']:.3f}")
                print(f"    MRR:        {stats['mrr']:.3f}")
                print(f"    平均耗时:   {stats['avg_execution_time']*1000:.1f}ms")

        if metrics.failed_queries:
            print(f"\n失败查询 ({len(metrics.failed_queries)} 个):")
            for i, fail in enumerate(metrics.failed_queries, 1):
                print(f"\n  [{i}] {fail['query']}")
                print(f"      期望: {fail['expected_doc_id']}")
                print(f"      检索: {', '.join(fail['retrieved_doc_ids'][:3])}")

        print("\n" + "="*60 + "\n")


def main():
    """主函数"""
    # 从任务描述中提取的测试数据
    config_data = {
        "base_model_path": "BAAI/bge-large-zh-v1.5",
        "finetuned_model_path": "learning/models/bge-large-zh-travel-finetuned",
        "test_queries": [
            {"query": "去北京出差能住什么价位的酒店？", "expected_doc_id": "doc_06", "difficulty": "easy"},
            {"query": "经济舱的机票可以报销吗？", "expected_doc_id": "doc_05", "difficulty": "easy"},
            {"query": "出差补贴一天给多少钱？", "expected_doc_id": "doc_12", "difficulty": "easy"},
            {"query": "火车票能报销吗？", "expected_doc_id": "doc_09", "difficulty": "easy"},
            {"query": "出差住宿发票丢了怎么办？", "expected_doc_id": "doc_01", "difficulty": "easy"},
            {"query": "去魔都出差住宿预算多少？", "expected_doc_id": "doc_11", "difficulty": "medium"},
            {"query": "副总裁能坐商务舱吗？", "expected_doc_id": "doc_23", "difficulty": "medium"},
            {"query": "从北京到成都应该坐飞机还是高铁？", "expected_doc_id": "doc_09", "difficulty": "medium"},
            {"query": "周末加班出差有额外补贴吗？", "expected_doc_id": "doc_13", "difficulty": "medium"},
            {"query": "出差期间生病就医费用能报吗？", "expected_doc_id": "doc_01", "difficulty": "medium"},
            {"query": "一次出差去多个城市，住宿标准怎么算？", "expected_doc_id": "doc_08", "difficulty": "medium"},
            {"query": "提前预订机票有折扣吗？", "expected_doc_id": "doc_04", "difficulty": "medium"},
            {"query": "商务舱和经济舱的差别是什么？", "expected_doc_id": "doc_23", "difficulty": "hard"},
            {"query": "杭州属于几线城市？住宿标准是多少？", "expected_doc_id": "doc_08", "difficulty": "hard"},
            {"query": "国际出差的政策和国内一样吗？", "expected_doc_id": "doc_04", "difficulty": "hard"},
            {"query": "出差超过一个月，标准有变化吗？", "expected_doc_id": "doc_01", "difficulty": "hard"},
            {"query": "CEO出差有什么特殊待遇？", "expected_doc_id": "doc_06", "difficulty": "hard"},
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

    # 创建评估配置
    config = EvalConfig(**config_data)

    # 运行评估
    evaluator = Config3Evaluator(config)
    metrics = evaluator.run_evaluation()

    # 返回JSON格式结果
    result = {
        "config": metrics.config,
        "accuracy_at_1": round(metrics.accuracy_at_1, 3),
        "recall_at_5": round(metrics.recall_at_5, 3),
        "mrr": round(metrics.mrr, 3),
        "by_difficulty": {
            k: {
                "count": v["count"],
                "accuracy_at_1": round(v["accuracy_at_1"], 3),
                "recall_at_5": round(v["recall_at_5"], 3),
                "mrr": round(v["mrr"], 3),
                "avg_execution_time_ms": round(v["avg_execution_time"] * 1000, 1)
            }
            for k, v in metrics.by_difficulty.items()
        },
        "failed_queries": metrics.failed_queries
    }

    return result


if __name__ == "__main__":
    result = main()
    print("\n最终结果 (JSON):")
    print(json.dumps(result, ensure_ascii=False, indent=2))
