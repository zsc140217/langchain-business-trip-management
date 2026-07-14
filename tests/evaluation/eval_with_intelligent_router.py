"""评估脚本 - 使用智能路由器进行召回率评估

关键改动：让所有查询通过intelligent_router，而不是直接调用vectorstore

使用方式：
    python tests/evaluation/eval_with_intelligent_router.py

预期效果：
    - GRAPH查询被正确路由到Neo4j
    - 召回率从47.7%提升到70%+
"""
import json
import sys
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.models.llm import get_llm
from src.rag.loader import load_documents
from src.rag.retriever import load_vectorstore, get_retriever
from src.agents.intelligent_router import IntelligentRouter


def check_recall(retrieved_docs: List[str], expected_chunks: List[str]) -> bool:
    """检查是否召回"""
    if not expected_chunks:
        return len(retrieved_docs) == 0

    if not retrieved_docs:
        return False

    retrieved_text = " ".join(retrieved_docs).lower()
    for chunk in expected_chunks:
        if chunk.lower() in retrieved_text:
            return True
    return False


def main():
    """主函数"""
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=" * 80)
    print("RAG召回率评估 - 使用智能路由器")
    print("=" * 80)

    # 1. 加载测试查询
    test_queries_path = project_root / "data" / "test_queries.json"
    print(f"\n[1/5] 加载测试查询: {test_queries_path}")
    with open(test_queries_path, "r", encoding="utf-8") as f:
        test_queries = json.load(f)
    print(f"      {len(test_queries)} 个查询")

    # 2. 初始化LLM
    print(f"\n[2/5] 初始化LLM...")
    llm = get_llm(temperature=0.1)

    # 3. 加载向量库
    print(f"\n[3/5] 加载向量库...")
    vectorstore_path = project_root / "src" / "data" / "vectorstore"
    vectorstore = load_vectorstore(str(vectorstore_path))
    retriever = get_retriever(vectorstore, k=10)
    print(f"      向量库共 {vectorstore.index.ntotal} 个向量")

    # 4. 创建智能路由器
    print(f"\n[4/5] 创建智能路由器...")
    router = IntelligentRouter(
        llm=llm,
        retriever=retriever
    )

    # 5. 执行评估
    print(f"\n[5/5] 执行评估...\n")
    print(f"{'='*80}")
    print(f"评估结果")
    print(f"{'='*80}\n")

    results = []
    stats = {
        "total": 0,
        "retrieved": 0,
        "graph_queries": 0,
        "graph_retrieved": 0,
        "factual_queries": 0,
        "factual_retrieved": 0,
    }
    failure_reasons = defaultdict(int)

    for i, query_data in enumerate(test_queries, 1):
        query = query_data["query"]
        expected_chunks = query_data.get("expected_chunks", [])
        retrieval_type = query_data.get("retrieval_type", "")

        # 只评估需要检索的查询（跳过闲聊和工具调用）
        if retrieval_type == "NONE":
            print(f"[{i:2d}/50] SKIP (闲聊/工具): {query}")
            continue

        print(f"[{i:2d}/50] {query[:50]}...", end=" ")

        # 使用路由器处理查询
        try:
            result = router.route(query)
        except Exception as e:
            print(f"[ERROR] {e}")
            continue

        route = result.get("route", "unknown")
        sources = result.get("sources", [])

        # 提取检索到的文档内容
        retrieved_docs = []
        if sources:
            for s in sources:
                if hasattr(s, "page_content"):
                    retrieved_docs.append(s.page_content)
                elif isinstance(s, str):
                    retrieved_docs.append(s)
                elif isinstance(s, dict) and "page_content" in s:
                    retrieved_docs.append(s["page_content"])

        # 此外，如果route是graph，也保留graph检索结果
        if route == "graph" and not retrieved_docs:
            retrieved_docs = result.get("graph_docs", [])

        # 检查召回
        recall = check_recall(retrieved_docs, expected_chunks)

        result_data = {
            "id": query_data["id"],
            "query": query,
            "route": route,
            "classification": result.get("classification", {}),
            "recall": recall,
            "retrieved_docs": retrieved_docs[:3],
            "retrieval_type": retrieval_type,
        }
        results.append(result_data)

        # 统计
        stats["total"] += 1
        if recall:
            stats["retrieved"] += 1

        if retrieval_type == "GRAPH":
            stats["graph_queries"] += 1
            if recall:
                stats["graph_retrieved"] += 1
        elif retrieval_type == "VECTOR":
            stats["factual_queries"] += 1
            if recall:
                stats["factual_retrieved"] += 1

        if not recall:
            if route == "chitchat" or route == "fallback":
                failure_reasons["误路由(非检索路径)"] += 1
            elif route == "graph" and retrieval_type == "VECTOR":
                failure_reasons["误路由(GRAPH→FACTUAL)"] += 1
            elif route != "graph" and retrieval_type == "GRAPH":
                failure_reasons["GRAPH查询未被路由到图谱"] += 1
            else:
                failure_reasons["检索结果不包含期望内容"] += 1

            print(f"[FAIL] (路由={route})")
        else:
            print(f"[OK] (路由={route})")

    # 6. 输出统计结果
    print(f"\n{'='*80}")
    print(f"统计摘要")
    print(f"{'='*80}\n")

    recall_rate = stats["retrieved"] / stats["total"] * 100 if stats["total"] > 0 else 0
    graph_recall = stats["graph_retrieved"] / stats["graph_queries"] * 100 if stats["graph_queries"] > 0 else 0
    factual_recall = stats["factual_retrieved"] / stats["factual_queries"] * 100 if stats["factual_queries"] > 0 else 0

    print(f"总体召回率:    {recall_rate:.1f}% ({stats['retrieved']}/{stats['total']})")
    print(f"GRAPH召回率:   {graph_recall:.1f}% ({stats['graph_retrieved']}/{stats['graph_queries']})")
    print(f"FACTUAL召回率: {factual_recall:.1f}% ({stats['factual_retrieved']}/{stats['factual_queries']})")

    print(f"\n失败原因分布:")
    for reason, count in sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True):
        pct = count / (stats["total"] - stats["retrieved"]) * 100 if (stats["total"] - stats["retrieved"]) > 0 else 0
        print(f"  {reason}: {count} ({pct:.1f}%)")

    # 7. 保存结果
    output_path = project_root / "tests" / "evaluation" / "eval_router_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total": stats["total"],
                "retrieved": stats["retrieved"],
                "recall_rate": f"{recall_rate:.1f}%",
                "graph_recall": f"{graph_recall:.1f}%",
                "factual_recall": f"{factual_recall:.1f}%",
            },
            "failure_reasons": dict(failure_reasons),
            "results": results,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存: {output_path}")
    print(f"\n{'='*80}")
    print(f"评估完成！")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
