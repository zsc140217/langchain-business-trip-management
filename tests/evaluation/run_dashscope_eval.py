"""
云端API评估脚本 - DashScope Embedding
使用与微调模型相同的测试集和评估方法，确保公平对比

配置：
- Embedding: DashScope text-embedding-v2 (云端API)
- 检索架构: 单路Dense检索（与简化版微调模型对比）
- Query重写: SimpleQueryRewriter（规则化）
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import time

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from src.modules.module_2_advanced_rag.query_rewriter import SimpleQueryRewriter


class DashScopeEvaluator:
    """DashScope云端API评估器"""

    def __init__(self):
        """初始化评估器"""
        print("[INFO] Initializing DashScope Embedding API...")

        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("未找到DASHSCOPE_API_KEY环境变量")

        # 初始化DashScope Embedding
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=api_key
        )

        # 初始化查询重写器（与微调模型保持一致）
        self.query_rewriter = SimpleQueryRewriter()

        print("[INFO] DashScope API initialized")

    def create_vectorstore(self, documents: List[Dict]):
        """
        创建向量存储

        Args:
            documents: 文档列表
        """
        print(f"[INFO] Creating vectorstore with {len(documents)} documents...")

        # 转换为Document对象
        doc_objects = []
        for i, doc in enumerate(documents):
            if isinstance(doc, str):
                doc_objects.append(Document(
                    page_content=doc,
                    metadata={"doc_id": f"doc_{i+1:02d}"}
                ))
            else:
                doc_objects.append(Document(
                    page_content=doc["content"],
                    metadata={"doc_id": doc["doc_id"]}
                ))

        self.documents = doc_objects

        # 创建FAISS向量存储
        print("[INFO] Embedding documents with DashScope API...")
        start_time = time.time()

        self.vectorstore = FAISS.from_documents(
            documents=doc_objects,
            embedding=self.embeddings
        )

        embed_time = time.time() - start_time
        print(f"[INFO] Documents embedded in {embed_time:.2f}s")
        print(f"[INFO] Average time per document: {embed_time/len(doc_objects)*1000:.1f}ms")
        print("[INFO] Vectorstore ready!")

    def retrieve(self, query: str, k: int = 5) -> Tuple[List[str], str]:
        """
        执行检索

        Args:
            query: 原始查询
            k: 返回Top-K结果

        Returns:
            (retrieved_doc_ids, rewritten_query)
        """
        # Query重写
        rewritten_query = self.query_rewriter.rewrite(query)

        # Dense检索
        results = self.vectorstore.similarity_search(rewritten_query, k=k)

        retrieved_doc_ids = [
            doc.metadata.get("doc_id", str(hash(doc.page_content)))
            for doc in results
        ]

        return retrieved_doc_ids, rewritten_query

    def evaluate(self, test_data: Dict) -> Dict:
        """执行评估"""
        test_queries = test_data["queries"]
        documents = test_data["documents"]

        print("\n" + "="*70)
        print("云端API评估 - DashScope text-embedding-v2 + 单路Dense检索")
        print("="*70)
        print(f"[INFO] Test queries: {len(test_queries)}")
        print(f"[INFO] Document corpus: {len(documents)}")

        # 创建向量存储
        self.create_vectorstore(documents)

        # 执行评估
        print("\n[INFO] Evaluating queries...")
        results = []
        query_rewrites = []

        for i, query_data in enumerate(test_queries, 1):
            query = query_data["query"]
            expected_content = query_data.get("expected_doc_contains")
            difficulty = query_data["difficulty"]

            # 检索
            start_time = time.time()
            retrieved_ids, rewritten_query = self.retrieve(query, k=5)
            retrieve_time = (time.time() - start_time) * 1000  # ms

            # 查找包含期望内容的文档
            expected_doc_id = None
            if expected_content:
                for doc in self.documents:
                    if expected_content in doc.page_content:
                        expected_doc_id = doc.metadata["doc_id"]
                        break

            # 计算rank
            rank = -1
            if expected_doc_id and expected_doc_id in retrieved_ids:
                rank = retrieved_ids.index(expected_doc_id) + 1

            is_correct = (len(retrieved_ids) > 0 and expected_doc_id and retrieved_ids[0] == expected_doc_id)

            # 记录结果
            result = {
                "query": query,
                "rewritten_query": rewritten_query,
                "expected_doc_id": expected_doc_id,
                "retrieved_doc_ids": retrieved_ids,
                "rank": rank,
                "is_correct": is_correct,
                "difficulty": difficulty,
                "retrieve_time_ms": retrieve_time
            }
            results.append(result)

            # 记录重写
            query_rewrites.append({
                "original": query,
                "rewritten": rewritten_query,
                "difficulty": difficulty
            })

            # 打印进度
            status = "[OK]" if is_correct else "[FAIL]"
            print(f"  [{i:2d}/{len(test_queries)}] {status} {query} ({retrieve_time:.1f}ms)")
            if query != rewritten_query:
                print(f"       -> {rewritten_query}")
            if not is_correct and expected_doc_id:
                print(f"       Expected: {expected_doc_id} | Got: {retrieved_ids[0] if retrieved_ids else 'None'} | Rank: {rank}")

        # 计算指标
        metrics = self.calculate_metrics(results)

        # 收集失败案例
        failed_queries = [
            {
                "query": r["query"],
                "rewritten_query": r["rewritten_query"],
                "expected": r["expected_doc_id"],
                "got": r["retrieved_doc_ids"][0] if r["retrieved_doc_ids"] else "None",
                "rank": r["rank"],
                "difficulty": r["difficulty"]
            }
            for r in results
            if not r["is_correct"] and r["difficulty"] != "distractor" and r["expected_doc_id"] is not None
        ]

        # 计算平均延迟
        avg_latency = sum(r["retrieve_time_ms"] for r in results) / len(results)

        # 打印结果
        self._print_summary(metrics, query_rewrites, failed_queries, avg_latency)

        return {
            "config": "dashscope_cloud_api_with_simple_rewriter",
            "model": "text-embedding-v2",
            "provider": "DashScope",
            "accuracy_at_1": metrics["accuracy_at_1"],
            "recall_at_5": metrics["recall_at_5"],
            "mrr": metrics["mrr"],
            "avg_latency_ms": avg_latency,
            "by_difficulty": metrics["by_difficulty"],
            "query_rewrites": query_rewrites,
            "failed_queries": failed_queries,
            "detailed_results": results
        }

    def calculate_metrics(self, results: List[Dict]) -> Dict:
        """计算评估指标"""
        accuracy_at_1 = 0
        recall_at_5 = 0
        mrr_sum = 0.0
        total = 0

        by_difficulty = {
            "easy": {"correct": 0, "total": 0, "recall": 0},
            "medium": {"correct": 0, "total": 0, "recall": 0},
            "hard": {"correct": 0, "total": 0, "recall": 0},
            "distractor": {"correct": 0, "total": 0}
        }

        for result in results:
            difficulty = result["difficulty"]

            # 跳过没有预期答案的查询
            if result["expected_doc_id"] is None:
                continue

            # 跳过distractor
            if difficulty == "distractor":
                by_difficulty[difficulty]["total"] += 1
                if result["is_correct"]:
                    by_difficulty[difficulty]["correct"] += 1
                continue

            total += 1
            by_difficulty[difficulty]["total"] += 1

            # Accuracy@1
            if result["is_correct"]:
                accuracy_at_1 += 1
                by_difficulty[difficulty]["correct"] += 1

            # Recall@5
            if result["rank"] > 0 and result["rank"] <= 5:
                recall_at_5 += 1
                by_difficulty[difficulty]["recall"] += 1

            # MRR
            if result["rank"] > 0:
                mrr_sum += 1.0 / result["rank"]

        return {
            "accuracy_at_1": accuracy_at_1 / total if total > 0 else 0,
            "recall_at_5": recall_at_5 / total if total > 0 else 0,
            "mrr": mrr_sum / total if total > 0 else 0,
            "by_difficulty": {
                diff: {
                    "accuracy_at_1": stats["correct"] / stats["total"] if stats["total"] > 0 else 0,
                    "recall_at_5": stats.get("recall", 0) / stats["total"] if stats["total"] > 0 else 0,
                    "count": stats["total"]
                }
                for diff, stats in by_difficulty.items()
            }
        }

    def _print_summary(self, metrics: Dict, query_rewrites: List[Dict], failed_queries: List[Dict], avg_latency: float):
        """打印评估结果摘要"""
        print("\n" + "="*70)
        print("EVALUATION RESULTS - DashScope Cloud API")
        print("="*70)

        print("\n--- Overall Metrics ---")
        print(f"Accuracy@1:  {metrics['accuracy_at_1']:.2%}")
        print(f"Recall@5:    {metrics['recall_at_5']:.2%}")
        print(f"MRR:         {metrics['mrr']:.4f}")
        print(f"Avg Latency: {avg_latency:.1f}ms")

        print("\n--- By Difficulty ---")
        for difficulty in ["easy", "medium", "hard", "distractor"]:
            stats = metrics["by_difficulty"][difficulty]
            if stats["count"] > 0:
                if "recall_at_5" in stats and difficulty != "distractor":
                    print(f"{difficulty.capitalize():12s} Accuracy@1: {stats['accuracy_at_1']:6.2%}  Recall@5: {stats['recall_at_5']:6.2%}  (n={stats['count']})")
                else:
                    print(f"{difficulty.capitalize():12s} Accuracy@1: {stats['accuracy_at_1']:6.2%}  (n={stats['count']})")

        print("\n--- Query Rewrites (Sample) ---")
        for qr in query_rewrites[:5]:
            if qr["original"] != qr["rewritten"]:
                print(f"  Original:  {qr['original']}")
                print(f"  Rewritten: {qr['rewritten']}\n")

        print(f"\n--- Failed Queries ({len(failed_queries)}) ---")
        for fail in failed_queries[:5]:
            print(f"  Query: {fail['query']}")
            print(f"  Rewritten: {fail['rewritten_query']}")
            print(f"  Expected: {fail['expected']} | Got: {fail['got']} | Rank: {fail['rank']}\n")


def load_test_data():
    """加载测试数据"""
    test_set_path = project_root / "learning" / "T2_LLM_Finetuning" / "embedding_finetune" / "enhanced_test_set.json"

    with open(test_set_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 转换格式
    return {
        "queries": data["test_queries"],
        "documents": data["document_corpus"]
    }


def main():
    """主评估流程"""

    # 加载测试数据
    print("[INFO] Loading test data...")
    test_data = load_test_data()
    print(f"[INFO] Loaded {len(test_data['queries'])} queries and {len(test_data['documents'])} documents")

    # 创建评估器
    evaluator = DashScopeEvaluator()

    # 执行评估
    result = evaluator.evaluate(test_data)

    # 保存结果
    output_file = Path(__file__).parent / "dashscope_evaluation_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Results saved to: {output_file}")
    print("="*70)


if __name__ == "__main__":
    main()
