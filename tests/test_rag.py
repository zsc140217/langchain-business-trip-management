"""
RAG功能测试
测试完整的RAG流程
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.rag.loader import load_documents
from src.rag.retriever import create_vectorstore, get_retriever
from src.rag.chain import create_rag_chain
from src.models.llm import get_llm


def test_rag_pipeline():
    """
    测试RAG完整流程

    这个测试展示了RAG的完整工作流程：
    1. 文档加载和切分
    2. 向量化和存储
    3. 检索相关文档
    4. 生成答案

    对比Spring AI：
    - Spring AI也是类似的流程
    - 但LangChain的组件更模块化
    - 每个步骤都可以单独测试和优化
    """
    print("=" * 60)
    print("RAG完整流程测试")
    print("=" * 60)

    try:
        # 1. 加载文档
        print("\n【步骤1】加载企业差旅规章文档")
        documents = load_documents("data/travel_policy.txt")
        assert len(documents) > 0, "文档加载失败"
        print(f"✅ 成功加载 {len(documents)} 个文档块")

        # 2. 创建向量存储
        print("\n【步骤2】创建向量存储")
        vectorstore = create_vectorstore(documents)
        assert vectorstore is not None, "向量存储创建失败"
        print("✅ 向量存储创建成功")

        # 3. 创建检索器
        print("\n【步骤3】创建检索器")
        retriever = get_retriever(vectorstore, k=3)
        print("✅ 检索器创建成功")

        # 4. 测试检索功能
        print("\n【步骤4】测试检索功能")
        test_query = "住宿标准"
        docs = retriever.get_relevant_documents(test_query)
        assert len(docs) > 0, "检索失败"
        print(f"✅ 检索到 {len(docs)} 个相关文档")
        print(f"\n最相关的文档内容：")
        print("-" * 60)
        print(docs[0].page_content)
        print("-" * 60)

        # 5. 创建LLM
        print("\n【步骤5】创建LLM")
        llm = get_llm(temperature=0.3)
        print("✅ LLM创建成功")

        # 6. 创建RAG链
        print("\n【步骤6】创建RAG链")
        rag_chain = create_rag_chain(llm, retriever)
        print("✅ RAG链创建成功")

        # 7. 测试查询
        print("\n【步骤7】测试RAG查询")
        print("=" * 60)

        test_questions = [
            "去上海出差住宿能报多少钱？",
            "从北京到深圳出差应该坐什么交通工具？",
            "出差期间每天的餐补是多少？",
            "出差报销有什么时间要求？"
        ]

        for i, question in enumerate(test_questions, 1):
            print(f"\n问题 {i}：{question}")
            result = rag_chain.invoke({"query": question})

            print(f"回答：{result['result']}")
            print(f"来源文档数：{len(result['source_documents'])}")
            print("-" * 60)

        print("\n" + "=" * 60)
        print("✅ RAG完整流程测试通过！")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_retrieval_accuracy():
    """
    测试检索准确性

    评估检索器是否能找到正确的文档
    """
    print("\n" + "=" * 60)
    print("检索准确性测试")
    print("=" * 60)

    try:
        # 加载文档
        documents = load_documents("data/travel_policy.txt")
        vectorstore = create_vectorstore(documents)
        retriever = get_retriever(vectorstore, k=3)

        # 测试用例：(查询, 期望关键词)
        test_cases = [
            ("住宿标准", ["住宿", "元/晚"]),
            ("交通", ["交通", "高铁", "飞机"]),
            ("餐补", ["餐饮", "元/天"]),
            ("报销", ["报销", "天内"])
        ]

        passed = 0
        for query, expected_keywords in test_cases:
            print(f"\n查询：{query}")
            docs = retriever.get_relevant_documents(query)

            # 检查是否包含期望的关键词
            content = " ".join([doc.page_content for doc in docs])
            found_keywords = [kw for kw in expected_keywords if kw in content]

            if len(found_keywords) >= len(expected_keywords) // 2:
                print(f"✅ 通过（找到关键词：{found_keywords}）")
                passed += 1
            else:
                print(f"❌ 失败（期望：{expected_keywords}，找到：{found_keywords}）")

        print(f"\n准确率：{passed}/{len(test_cases)} = {passed/len(test_cases)*100:.1f}%")

        return passed == len(test_cases)

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        return False


if __name__ == "__main__":
    """
    运行所有测试
    """
    print("\n🚀 开始测试LangChain RAG功能\n")

    # 检查环境
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("⚠️  警告：未找到DASHSCOPE_API_KEY环境变量")
        print("请先配置.env文件")
        sys.exit(1)

    # 运行测试
    test1 = test_rag_pipeline()
    test2 = test_retrieval_accuracy()

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"RAG完整流程：{'✅ 通过' if test1 else '❌ 失败'}")
    print(f"检索准确性：{'✅ 通过' if test2 else '❌ 失败'}")

    if test1 and test2:
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)
