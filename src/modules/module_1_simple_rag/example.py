"""
Module 1: Simple RAG - Complete Integration Example
完整的RAG系统示例

演示如何将loader、retriever和chain组合使用
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from loader import load_and_split_documents, load_documents_from_text
from retriever import create_faiss_vectorstore, create_retriever, save_vectorstore, load_vectorstore
from chain import create_rag_chain_lcel, create_rag_chain_with_sources


def create_simple_rag_system(file_path: str = None, text: str = None):
    """
    创建完整的RAG系统

    Args:
        file_path: 文档文件路径（与text二选一）
        text: 文档文本内容（与file_path二选一）

    Returns:
        RAG链实例
    """
    print("=== 创建Simple RAG系统 ===\n")

    # 1. 加载文档
    if file_path:
        print("Step 1: 从文件加载文档...")
        documents = load_and_split_documents(file_path, chunk_size=500, chunk_overlap=50)
    elif text:
        print("Step 1: 从文本加载文档...")
        documents = load_documents_from_text(text, chunk_size=500, chunk_overlap=50)
    else:
        raise ValueError("必须提供file_path或text参数")

    # 2. 创建向量存储
    print("\nStep 2: 创建向量存储...")
    vectorstore = create_faiss_vectorstore(documents)

    # 3. 创建检索器
    print("\nStep 3: 创建检索器...")
    retriever = create_retriever(vectorstore, k=5)

    # 4. 创建RAG链
    print("\nStep 4: 创建RAG链...")
    rag_chain = create_rag_chain_lcel(retriever)

    print("\n[OK] RAG系统创建完成！\n")

    return rag_chain


def demo_basic_usage():
    """
    基础使用示例
    """
    print("=" * 60)
    print("示例1：基础RAG问答")
    print("=" * 60 + "\n")

    # 准备政策文档
    policy_text = """
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
3. 出租车：仅限机场、火车站往返酒店

第三章 餐饮补贴
1. 早餐：30元/天
2. 午餐：50元/天
3. 晚餐：50元/天
4. 总计：130元/天

第四章 其他规定
1. 出差需提前3天申请
2. 出差结束后7天内提交报销
3. 超标部分自行承担
4. 特殊情况需经部门经理批准
    """

    # 创建RAG系统
    rag_chain = create_simple_rag_system(text=policy_text)

    # 测试问题
    questions = [
        "去上海出差，酒店最多能报销多少钱？",
        "从北京到广州出差应该坐什么交通工具？",
        "出差期间每天能拿多少餐补？",
        "出差申请需要提前几天？"
    ]

    for i, question in enumerate(questions, 1):
        print(f"问题 {i}：{question}")
        answer = rag_chain.invoke(question)
        print(f"回答：{answer}\n")


def demo_with_sources():
    """
    带来源文档的示例
    """
    print("=" * 60)
    print("示例2：带来源文档的RAG")
    print("=" * 60 + "\n")

    # 使用政策文件
    policy_path = os.path.join("..", "..", "..", "data", "travel_policy.txt")

    if not os.path.exists(policy_path):
        print(f"政策文件不存在：{policy_path}")
        print("使用测试文本代替...\n")
        demo_basic_usage()
        return

    # 加载文档
    print("Step 1: 加载文档...")
    documents = load_and_split_documents(policy_path, chunk_size=500, chunk_overlap=50)

    # 创建向量存储
    print("\nStep 2: 创建向量存储...")
    vectorstore = create_faiss_vectorstore(documents)

    # 创建检索器
    print("\nStep 3: 创建检索器...")
    retriever = create_retriever(vectorstore, k=3)

    # 创建带来源的RAG链
    print("\nStep 4: 创建RAG链（带来源）...")
    rag_chain = create_rag_chain_with_sources(retriever)

    # 测试
    print("\nStep 5: 测试问答...\n")
    question = "二线城市出差住宿标准是多少？"
    print(f"❓ 问题：{question}\n")

    result = rag_chain.invoke(question)

    print(f"💡 答案：{result['answer']}\n")
    print(f"📚 参考了 {len(result['source_documents'])} 个文档：")

    for i, doc in enumerate(result['source_documents'], 1):
        print(f"\n【来源 {i}】")
        print(doc.page_content)


def demo_persistence():
    """
    向量存储持久化示例
    """
    print("=" * 60)
    print("示例3：向量存储持久化")
    print("=" * 60 + "\n")

    policy_text = """
企业差旅管理规章
第一章 住宿标准
1. 一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚
2. 二线城市（杭州、成都、武汉等）：标准间不超过400元/晚
    """

    # 创建向量存储
    print("Step 1: 创建向量存储...")
    documents = load_documents_from_text(policy_text, chunk_size=200)
    vectorstore = create_faiss_vectorstore(documents)

    # 保存到本地
    save_path = "./vectorstore_cache"
    print(f"\nStep 2: 保存向量存储...")
    save_vectorstore(vectorstore, save_path)

    # 从本地加载
    print(f"\nStep 3: 从本地加载向量存储...")
    loaded_vectorstore = load_vectorstore(save_path)

    # 测试加载的向量存储
    print(f"\nStep 4: 测试加载的向量存储...")
    retriever = create_retriever(loaded_vectorstore, k=2)
    rag_chain = create_rag_chain_lcel(retriever)

    question = "一线城市住宿标准是多少？"
    print(f"\n❓ {question}")
    answer = rag_chain.invoke(question)
    print(f"💡 {answer}")

    print("\n[OK] 持久化测试成功！")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Module 1: Simple RAG - 完整示例")
    print("=" * 60 + "\n")

    try:
        # 运行示例1：基础用法
        demo_basic_usage()

        print("\n" + "=" * 60 + "\n")

        # 运行示例2：带来源文档
        demo_with_sources()

        print("\n" + "=" * 60 + "\n")

        # 运行示例3：持久化
        demo_persistence()

        print("\n" + "=" * 60)
        print("[OK] 所有示例运行成功！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] 运行失败：{e}")
        import traceback
        traceback.print_exc()
        print("\n请检查：")
        print("1. 环境变量DASHSCOPE_API_KEY是否已设置")
        print("2. 是否已安装所有依赖")
        print("3. API Key是否有效且有余额")
