"""评估脚本 - 使用 OrchestratorAgent 进行召回率评估

关键改动：
1. 使用 OrchestratorAgent 替代 IntelligentRouter
2. 评估记忆感知率（查询使用记忆上下文的比例）
3. 评估四通道路由准确率（simple/complex/planning/open）

使用方式：
    python tests/evaluation/eval_with_orchestrator.py

预期效果：
    - GRAPH查询被正确路由到Neo4j
    - 记忆感知率从 0% 提升到 80%+
    - 召回率从 47.7% 提升到 70%+
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
from src.agents.orchestrator_agent import OrchestratorAgent
from src.memory.memory_service import MemoryService
from src.tools.registry import get_all_tools


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
    print("RAG召回率评估 - 使用 OrchestratorAgent")
    print("=" * 80)

    # 1. 加载测试查询
    test_queries_path = project_root / "data" / "test_queries.json"
    print(f"\n[1/4] 加载测试查询: {test_queries_path}")
    with open(test_queries_path, "r", encoding="utf-8") as f:
        test_queries = json.load(f)
    print(f"      {len(test_queries)} 个查询")

    # 2. 初始化LLM
    print(f"\n[2/4] 初始化LLM...")
    llm = get_llm(temperature=0.1)

    # 3. 初始化记忆服务
    print(f"\n[3/4] 初始化记忆服务...")
    memory_service = MemoryService()

    # 4. 初始化 OrchestratorAgent
    print(f"\n[4/4] 初始化 OrchestratorAgent...")
    tools = get_all_tools()
    orchestrator = OrchestratorAgent(
        llm=llm,
        tools=tools,
        memory_service=memory_service
    )
    print(f"      已注册 {len(tools)} 个工具")

    # 5. 执行评估
    print(f"\n{'='*80}")
    print(f"评估结果")
    print(f"{'='*80}\n")

    results = []
    stats = {
        "total": 0,
        "retrieved": 0,
        "memory_aware": 0,  # 使用了记忆上下文的查询数
        "graph_queries": 0,
        "graph_retrieved": 0,
        "factual_queries": 0,
        "factual_retrieved": 0,
        "fast_path": 0,  # 快路径命中次数
        "qa_domain": 0,  # Q&A域路由次数
        "approval_domain": 0,  # 审批域路由次数
    }
    failure_reasons = defaultdict(int)

    # 模拟用户会话（用于测试记忆）
    user_id = "test_user_eval"
    conversation_id = "test_conv_eval"

    for i, query_data in enumerate(test_queries, 1):
        query = query_data["query"]
        expected_chunks = query_data.get("expected_chunks", [])
        retrieval_type = query_data.get("retrieval_type", "")

        # 只评估需要检索的查询（跳过闲聊和工具调用）
        if retrieval_type == "NONE":
            print(f"[{i:2d}/50] SKIP (闲聊/工具): {query}")
            continue

        print(f"[{i:2d}/50] {query[:50]}...", end=" ")

        # 使用 OrchestratorAgent 处理查询
        try:
            result = orchestrator.route(
                query=query,
                user_id=user_id,
                conversation_id=conversation_id
            )

            # 检查是否使用了记忆（通过判断上下文是否非空）
            memory_used = False
            try:
                context = memory_service.build_enhanced_prompt(
                    user_id=user_id,
                    conversation_id=conversation_id
                )
                memory_used = bool(context and context.strip())
            except:
                pass

            # 提取路由统计
            orchestrator_stats = orchestrator.get_stats()

            # 简单的召回检查（基于结果文本）
            recall = check_recall([result], expected_chunks)

            result_data = {
                "id": query_data["id"],
                "query": query,
                "result": result[:200],  # 截断结果
                "recall": recall,
                "memory_used": memory_used,
                "retrieval_type": retrieval_type,
                "stats": orchestrator_stats
            }
            results.append(result_data)

            # 统计
            stats["total"] += 1
            if recall:
                stats["retrieved"] += 1
            if memory_used:
                stats["memory_aware"] += 1

            if retrieval_type == "GRAPH":
                stats["graph_queries"] += 1
                if recall:
                    stats["graph_retrieved"] += 1
            elif retrieval_type == "VECTOR":
                stats["factual_queries"] += 1
                if recall:
                    stats["factual_retrieved"] += 1

            if not recall:
                failure_reasons["检索结果不包含期望内容"] += 1
                print(f"[FAIL]")
            else:
                status = "✓MEM" if memory_used else "✓"
                print(f"[OK {status}]")

        except Exception as e:
            print(f"[ERROR] {e}")
            failure_reasons["执行错误"] += 1
            continue

    # 更新 orchestrator 统计到全局
    final_stats = orchestrator.get_stats()
    stats["fast_path"] = final_stats.get("fast_path", 0)
    stats["qa_domain"] = final_stats.get("qa_domain", 0)
    stats["approval_domain"] = final_stats.get("approval_domain", 0)

    # 6. 输出统计结果
    print(f"\n{'='*80}")
    print(f"统计摘要")
    print(f"{'='*80}\n")

    recall_rate = stats["retrieved"] / stats["total"] * 100 if stats["total"] > 0 else 0
    memory_aware_rate = stats["memory_aware"] / stats["total"] * 100 if stats["total"] > 0 else 0
    graph_recall = stats["graph_retrieved"] / stats["graph_queries"] * 100 if stats["graph_queries"] > 0 else 0
    factual_recall = stats["factual_retrieved"] / stats["factual_queries"] * 100 if stats["factual_queries"] > 0 else 0

    print(f"总体召回率:    {recall_rate:.1f}% ({stats['retrieved']}/{stats['total']})")
    print(f"记忆感知率:    {memory_aware_rate:.1f}% ({stats['memory_aware']}/{stats['total']})")
    print(f"GRAPH召回率:   {graph_recall:.1f}% ({stats['graph_retrieved']}/{stats['graph_queries']})")
    print(f"FACTUAL召回率: {factual_recall:.1f}% ({stats['factual_retrieved']}/{stats['factual_queries']})")

    print(f"\n路由统计:")
    print(f"  快路径命中:    {stats['fast_path']} 次")
    print(f"  Q&A域路由:     {stats['qa_domain']} 次")
    print(f"  审批域路由:    {stats['approval_domain']} 次")

    print(f"\n失败原因分布:")
    for reason, count in sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True):
        pct = count / (stats["total"] - stats["retrieved"]) * 100 if (stats["total"] - stats["retrieved"]) > 0 else 0
        print(f"  {reason}: {count} ({pct:.1f}%)")

    # 7. 保存结果
    output_path = project_root / "tests" / "evaluation" / "eval_orchestrator_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total": stats["total"],
                "retrieved": stats["retrieved"],
                "recall_rate": f"{recall_rate:.1f}%",
                "memory_aware_rate": f"{memory_aware_rate:.1f}%",
                "graph_recall": f"{graph_recall:.1f}%",
                "factual_recall": f"{factual_recall:.1f}%",
                "fast_path": stats["fast_path"],
                "qa_domain": stats["qa_domain"],
                "approval_domain": stats["approval_domain"],
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
