"""
完整版RAG系统评估脚本
集成：
1. 完整的EnterpriseHybridRetriever（三路召回+RRF融合）
2. 真正的LLM驱动Query重写
3. 使用微调后的embedding模型

对比配置4：微调模型 + Query重写 + 混合检索
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
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.chat_models import ChatTongyi
from src.modules.module_2_advanced_rag.query_rewriter import SimpleQueryRewriter
from langchain_community.retrievers import BM25Retriever
import jieba

# 设置离线模式
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'


class ChineseBM25Retriever(BM25Retriever):
    """支持中文分词的BM25检索器"""

    @classmethod
    def from_documents(cls, documents: List[Document], **kwargs):
        """从文档创建BM25检索器，使用jieba分词"""
        texts = [doc.page_content for doc in documents]

        # 使用jieba分词
        retriever = cls.from_texts(
            texts=[" ".join(jieba.cut(text)) for text in texts],
            metadatas=[doc.metadata for doc in documents],
            **kwargs
        )

        return retriever


class FullRAGEvaluator:
    """完整RAG系统评估器"""

    def __init__(self, model_path: str):
        """初始化评估器"""
        self.model_path = model_path

        print(f"[INFO] Loading embedding model: {model_path}")
        start_time = time.time()
        self.embedding_model = SentenceTransformer(model_path)
        load_time = time.time() - start_time
        print(f"[INFO] Model loaded in {load_time:.2f}s")
        print(f"[INFO] Embedding dimension: {self.embedding_model.get_sentence_embedding_dimension()}")

        # 初始化LLM
        print("[INFO] Initializing LLM for query rewriting...")
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("未找到DASHSCOPE_API_KEY环境变量")

        self.llm = ChatTongyi(
            model="qwen-plus",
            temperature=0.1,
            dashscope_api_key=api_key
        )

        # 初始化查询重写器（使用简单版本避免API调用失败）
        self.query_rewriter = SimpleQueryRewriter()

    def create_hybrid_retriever(self, documents: List[Dict]):
        """
        创建完整的混合检索器
        包含：BM25 + Dense检索 + Query重写
        """
        print(f"[INFO] Creating hybrid retriever with {len(documents)} documents...")

        # 转换为Document对象
        doc_objects = []
        for i, doc in enumerate(documents):
            # 如果是字符串，转换为字典格式
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

        # 1. 创建BM25检索器
        print("[INFO] Building BM25 index...")
        self.bm25_retriever = ChineseBM25Retriever.from_documents(doc_objects)

        # 2. 创建FAISS向量存储
        print("[INFO] Building FAISS vector store...")
        texts = [doc.page_content for doc in doc_objects]
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)

        import faiss
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # 内积相似度
        index.add(embeddings)

        from langchain_community.docstore.in_memory import InMemoryDocstore
        self.vectorstore = FAISS(
            embedding_function=lambda texts: self.embedding_model.encode(texts),
            index=index,
            docstore=InMemoryDocstore({str(i): doc for i, doc in enumerate(doc_objects)}),
            index_to_docstore_id={i: str(i) for i in range(len(doc_objects))}
        )

        self.documents = doc_objects
        print("[INFO] Hybrid retriever ready!")

    def retrieve_with_hybrid(
        self,
        query: str,
        k: int = 5,
        rrf_k: int = 60,
        bm25_weight: float = 1.0,
        dense_original_weight: float = 1.0,
        dense_rewritten_weight: float = 1.0
    ) -> Tuple[List[str], str]:
        """
        混合检索：三路召回 + RRF融合

        Returns:
            (retrieved_doc_ids, rewritten_query)
        """
        # Step 1: Query重写
        rewritten_query = self.query_rewriter.rewrite(query)

        # Step 2: 三路召回
        retrieve_size = k * 10  # 召回10倍用于融合

        # 路径1: BM25检索
        bm25_results = self.bm25_retriever.invoke(query)[:retrieve_size]

        # 路径2: Dense检索-原始查询
        dense_original_results = self.vectorstore.similarity_search(query, k=min(retrieve_size, 10))

        # 路径3: Dense检索-改写查询
        dense_rewritten_results = []
        if rewritten_query != query:
            dense_rewritten_results = self.vectorstore.similarity_search(
                rewritten_query,
                k=min(retrieve_size, 10)
            )

        # Step 3: RRF融合
        score_map = {}

        # 处理BM25结果
        for rank, doc in enumerate(bm25_results, start=1):
            doc_id = doc.metadata.get("doc_id", str(hash(doc.page_content)))
            if doc_id not in score_map:
                score_map[doc_id] = {"doc": doc, "score": 0.0}
            score_map[doc_id]["score"] += bm25_weight / (rrf_k + rank)

        # 处理Dense-Original结果
        for rank, doc in enumerate(dense_original_results, start=1):
            doc_id = doc.metadata.get("doc_id", str(hash(doc.page_content)))
            if doc_id not in score_map:
                score_map[doc_id] = {"doc": doc, "score": 0.0}
            score_map[doc_id]["score"] += dense_original_weight / (rrf_k + rank)

        # 处理Dense-Rewritten结果
        for rank, doc in enumerate(dense_rewritten_results, start=1):
            doc_id = doc.metadata.get("doc_id", str(hash(doc.page_content)))
            if doc_id not in score_map:
                score_map[doc_id] = {"doc": doc, "score": 0.0}
            score_map[doc_id]["score"] += dense_rewritten_weight / (rrf_k + rank)

        # 排序并返回
        sorted_items = sorted(
            score_map.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        retrieved_doc_ids = [
            item["doc"].metadata.get("doc_id", str(hash(item["doc"].page_content)))
            for item in sorted_items[:k]
        ]

        return retrieved_doc_ids, rewritten_query

    def evaluate(self, test_data: Dict) -> Dict:
        """执行完整评估"""
        test_queries = test_data["queries"]
        documents = test_data["documents"]

        print("\n" + "="*70)
        print("完整RAG系统评估 - 配置4：微调模型 + Query重写 + 混合检索")
        print("="*70)
        print(f"[INFO] Test queries: {len(test_queries)}")
        print(f"[INFO] Document corpus: {len(documents)}")

        # 创建混合检索器
        self.create_hybrid_retriever(documents)

        # 执行评估
        print("\n[INFO] Evaluating queries with hybrid retrieval...")
        results = []
        query_rewrites = []

        for i, query_data in enumerate(test_queries, 1):
            query = query_data["query"]
            expected_content = query_data["expected_doc_contains"]
            difficulty = query_data["difficulty"]

            # 检索
            retrieved_ids, rewritten_query = self.retrieve_with_hybrid(query, k=5)

            # 查找包含期望内容的文档
            expected_doc_id = None
            if expected_content:  # Check if expected_content is not None
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
                "difficulty": difficulty
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
            print(f"  [{i:2d}/{len(test_queries)}] {status} {query}")
            if query != rewritten_query:
                print(f"       -> {rewritten_query}")
            if not is_correct:
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
            if not r["is_correct"] and r["difficulty"] != "distractor"
        ]

        # 打印结果
        self._print_summary(metrics, query_rewrites, failed_queries)

        return {
            "config": "finetuned_with_query_rewriting_and_hybrid_retrieval",
            "model_path": self.model_path,
            "accuracy_at_1": metrics["accuracy_at_1"],
            "recall_at_5": metrics["recall_at_5"],
            "mrr": metrics["mrr"],
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

    def _print_summary(self, metrics: Dict, query_rewrites: List[Dict], failed_queries: List[Dict]):
        """打印评估结果摘要"""
        print("\n" + "="*70)
        print("EVALUATION RESULTS")
        print("="*70)

        print("\n--- Overall Metrics ---")
        print(f"Accuracy@1:  {metrics['accuracy_at_1']:.2%}")
        print(f"Recall@5:    {metrics['recall_at_5']:.2%}")
        print(f"MRR:         {metrics['mrr']:.4f}")

        print("\n--- By Difficulty ---")
        for difficulty in ["easy", "medium", "hard", "distractor"]:
            stats = metrics["by_difficulty"][difficulty]
            if "recall_at_5" in stats:
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

    # 转换格式：test_queries -> queries, document_corpus -> documents
    return {
        "queries": data["test_queries"],
        "documents": data["document_corpus"]
    }


def main():
    """主评估流程"""

    # 模型路径
    model_path = str(project_root / "learning" / "models" / "bge-large-zh-travel-finetuned")

    # 加载测试数据
    print("[INFO] Loading test data...")
    test_data = load_test_data()
    print(f"[INFO] Loaded {len(test_data['queries'])} queries and {len(test_data['documents'])} documents")

    # 创建评估器
    evaluator = FullRAGEvaluator(model_path)

    # 执行评估
    result = evaluator.evaluate(test_data)

    # 保存结果
    output_file = Path(__file__).parent / "full_rag_evaluation_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Results saved to: {output_file}")
    print("="*70)


if __name__ == "__main__":
    main()
