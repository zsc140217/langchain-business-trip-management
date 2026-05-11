"""
完整功能测试脚本
测试所有已实现的高级功能
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.llm import get_llm
from src.agents.complexity_assessor import ComplexityAssessor, QueryComplexity
from src.agents.task_decomposer import TaskDecomposer
from src.agents.workflow_orchestrator import WorkflowOrchestrator
from src.rag.loader import load_documents
from src.rag.retriever import create_vectorstore, get_retriever
from src.rag.chain import create_rag_chain
from src.rag.hybrid_retriever import EnterpriseHybridRetriever, EnterpriseQueryRewriter
from src.tools.weather import query_weather


def test_complexity_assessor():
    """测试复杂度评估器"""
    print("\n" + "="*60)
    print("测试1：ComplexityAssessor（复杂度评估器）")
    print("="*60)

    llm = get_llm(temperature=0.0)
    assessor = ComplexityAssessor(llm)

    test_cases = [
        ("北京天气", QueryComplexity.SIMPLE),
        ("上海和广州天气对比", QueryComplexity.MEDIUM),
        ("去杭州出差，查天气并推荐酒店", QueryComplexity.COMPLEX),
    ]

    passed = 0
    for query, expected in test_cases:
        result = assessor.assess(query)
        status = "✅" if result == expected else "❌"
        print(f"{status} {query} → {result.value} (期望:{expected.value})")
        if result == expected:
            passed += 1

    print(f"\n结果：{passed}/{len(test_cases)} 通过")
    return passed == len(test_cases)


def test_task_decomposer():
    """测试任务分解器"""
    print("\n" + "="*60)
    print("测试2：TaskDecomposer（任务分解器）")
    print("="*60)

    llm = get_llm(temperature=0.3)
    decomposer = TaskDecomposer(llm)

    query = "去杭州出差，查天气并推荐酒店"
    tasks = decomposer.decompose(query)

    print(f"\n查询：{query}")
    print(f"分解为 {len(tasks)} 个子任务：")
    for task in tasks:
        print(f"  - 任务{task.id}: {task.description}")

    # 测试拓扑排序
    batches = decomposer.sort_tasks_by_dependency(tasks)
    print(f"\n执行计划（{len(batches)}个批次）：")
    for i, batch in enumerate(batches, 1):
        task_ids = [t.id for t in batch]
        print(f"  批次{i}: 任务{task_ids}")

    return len(tasks) >= 2


def test_workflow_orchestrator():
    """测试工作流编排器"""
    print("\n" + "="*60)
    print("测试3：WorkflowOrchestrator（工作流编排器）")
    print("="*60)

    llm = get_llm(temperature=0.3)
    complexity_assessor = ComplexityAssessor(llm)
    task_decomposer = TaskDecomposer(llm)

    # 加载RAG
    documents = load_documents("data/travel_policy.txt")
    vectorstore = create_vectorstore(documents)
    retriever = get_retriever(vectorstore)
    rag_chain = create_rag_chain(llm, retriever)

    # 创建编排器
    orchestrator = WorkflowOrchestrator(
        llm=llm,
        complexity_assessor=complexity_assessor,
        task_decomposer=task_decomposer,
        rag_chain=rag_chain,
        tools={"query_weather": query_weather}
    )

    # 测试不同复杂度的查询
    test_queries = [
        "去上海出差住宿标准",  # SIMPLE - RAG
        "北京天气怎么样",  # SIMPLE - 天气工具
    ]

    for query in test_queries:
        result = orchestrator.route(query, "test123")
        print(f"\n查询：{query}")
        print(f"结果：{result[:200]}...")

    return True


def test_hybrid_retriever():
    """测试混合检索器"""
    print("\n" + "="*60)
    print("测试4：EnterpriseHybridRetriever（混合检索器）")
    print("="*60)

    llm = get_llm(temperature=0.1)

    # 加载文档
    documents = load_documents("data/travel_policy.txt")
    vectorstore = create_vectorstore(documents)

    # 创建查询改写器
    query_rewriter = EnterpriseQueryRewriter(llm)

    # 创建混合检索器
    hybrid_retriever = EnterpriseHybridRetriever(
        vector_store=vectorstore,
        documents=documents,
        query_rewriter=query_rewriter
    )

    # 测试查询
    query = "去上海出差住宿能报多少"
    results = hybrid_retriever.retrieve(query, top_k=3)

    print(f"\n查询：{query}")
    print(f"返回Top-3文档：")
    for i, doc in enumerate(results, 1):
        preview = doc.page_content[:80].replace('\n', ' ')
        print(f"  {i}. {preview}...")

    return len(results) > 0


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("LangChain企业差旅智能体 - 完整功能测试")
    print("="*60)

    # 检查环境
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("\n⚠️  警告：未找到DASHSCOPE_API_KEY环境变量")
        print("请先配置.env文件")
        return

    results = {}

    try:
        # 测试1：复杂度评估器
        results['complexity_assessor'] = test_complexity_assessor()
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        results['complexity_assessor'] = False

    try:
        # 测试2：任务分解器
        results['task_decomposer'] = test_task_decomposer()
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        results['task_decomposer'] = False

    try:
        # 测试3：工作流编排器
        results['workflow_orchestrator'] = test_workflow_orchestrator()
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        results['workflow_orchestrator'] = False

    try:
        # 测试4：混合检索器
        results['hybrid_retriever'] = test_hybrid_retriever()
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        results['hybrid_retriever'] = False

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")

    total_passed = sum(results.values())
    total_tests = len(results)
    print(f"\n总计：{total_passed}/{total_tests} 通过")

    if total_passed == total_tests:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  {total_tests - total_passed} 个测试失败")


if __name__ == "__main__":
    main()
