"""
Self-RAG使用示例

演示如何使用查询分类器和自适应RAG系统
"""
from src.rag.query_classifier import QueryClassifier
from src.rag.self_rag import SelfRAG
from src.rag.loader import load_documents_from_text
from src.rag.retriever import create_vectorstore, get_retriever


def demo_query_classifier():
    """演示查询分类器"""
    print("=" * 60)
    print("演示1: 查询分类器")
    print("=" * 60)

    classifier = QueryClassifier()

    test_queries = [
        "你好",
        "去上海出差住宿能报多少钱",
        "今天天气怎么样",
        "北京出差住宿标准",
        "出差能报销多少钱",
        "你能做什么",
        "如何申请差旅报销"
    ]

    for query in test_queries:
        result = classifier.classify(query)
        print(f"\n查询: {query}")
        print(f"  类型: {result['type']}")
        print(f"  置信度: {result['confidence']:.2f}")
        print(f"  原因: {result['reason']}")


def demo_self_rag():
    """演示Self-RAG自适应检索"""
    print("\n\n" + "=" * 60)
    print("演示2: Self-RAG自适应检索")
    print("=" * 60)

    # 准备测试文档
    test_text = """
企业差旅管理规章

第一章 住宿标准
1. 一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚
2. 二线城市（杭州、成都、武汉等）：标准间不超过400元/晚
3. 三线及以下城市：标准间不超过300元/晚

第二章 交通标准
1. 市内交通：实报实销，需提供发票
2. 城际交通：
   - 距离<500公里：高铁二等座
   - 距离≥500公里：飞机经济舱

第三章 餐饮补贴
1. 早餐：30元/天
2. 午餐：50元/天
3. 晚餐：50元/天
4. 总计：130元/天
    """

    print("\n初始化RAG组件...")
    # 创建向量存储
    docs = load_documents_from_text(test_text, chunk_size=200)
    vectorstore = create_vectorstore(docs)
    retriever = get_retriever(vectorstore, k=3)

    # 创建Self-RAG
    self_rag = SelfRAG(retriever=retriever)

    # 测试不同类型的查询
    test_cases = [
        ("你好", "期望：CHITCHAT，不检索"),
        ("去上海出差住宿能报多少钱", "期望：FACTUAL，执行检索"),
        ("今天天气怎么样", "期望：CHITCHAT，不检索"),
        ("北京出差住宿标准是多少", "期望：FACTUAL，执行检索"),
        ("出差期间每天餐补多少钱", "期望：FACTUAL，执行检索")
    ]

    for query, expected in test_cases:
        print(f"\n{'-' * 60}")
        print(f"查询: {query}")
        print(f"{expected}")

        result = self_rag.query(query)

        print(f"\n结果:")
        print(f"  分类类型: {result['classification']['type']}")
        print(f"  置信度: {result['classification']['confidence']:.2f}")
        print(f"  是否检索: {'是' if result['retrieved'] else '否'}")
        print(f"  来源文档数: {len(result['sources'])}")
        print(f"\n  回答:")
        print(f"  {result['answer'][:200]}...")


def demo_comparison():
    """演示Self-RAG vs 传统RAG的优势"""
    print("\n\n" + "=" * 60)
    print("演示3: Self-RAG优势对比")
    print("=" * 60)

    print("\n传统RAG:")
    print("  - 所有查询都执行检索")
    print("  - '你好' -> 检索知识库 -> 可能返回不相关信息")
    print("  - 效率低，成本高")

    print("\nSelf-RAG:")
    print("  - 智能判断是否需要检索")
    print("  - '你好' -> 直接回答 -> 快速响应")
    print("  - '住宿标准' -> 检索知识库 -> 准确回答")
    print("  - 效率高，成本低，用户体验好")


if __name__ == "__main__":
    """运行所有演示"""
    try:
        # 演示1: 查询分类器
        demo_query_classifier()

        # 演示2: Self-RAG
        demo_self_rag()

        # 演示3: 优势对比
        demo_comparison()

        print("\n\n" + "=" * 60)
        print("所有演示完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        print("\n请确保:")
        print("1. 已配置.env文件中的DASHSCOPE_API_KEY和DASHSCOPE_BASE_URL")
        print("2. 已安装所有依赖: pip install -r requirements.txt")
        import traceback
        traceback.print_exc()
