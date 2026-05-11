"""
向量检索模块
创建向量存储和检索器

对应Spring AI的：
@Bean
public VectorStore vectorStore(EmbeddingModel embeddingModel) {
    return new SimpleVectorStore(embeddingModel);
}
"""
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain.schema import Document
from typing import List
import os


def create_vectorstore(documents: List[Document]):
    """
    创建FAISS向量存储

    这是RAG的核心：向量化和存储

    什么是向量存储？
    - 把文本转换成向量（一串数字）
    - 相似的文本，向量也相似
    - 通过向量相似度快速找到相关文档

    FAISS vs 其他向量数据库：
    - FAISS：Facebook开源，本地运行，速度快
    - Chroma：更现代，支持持久化
    - Pinecone：云服务，适合生产环境
    - Milvus：分布式，适合大规模

    对比Spring AI：
    - Spring AI用SimpleVectorStore（内存）
    - LangChain的FAISS更强大，支持多种索引算法
    - 两者都需要Embedding模型来生成向量

    Args:
        documents: 文档列表

    Returns:
        FAISS向量存储实例
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        raise ValueError("未找到DASHSCOPE_API_KEY环境变量")

    print("🔄 创建向量存储...")

    # 创建Embedding模型
    # text-embedding-v1是通义千问的向量模型
    embeddings = DashScopeEmbeddings(
        model="text-embedding-v1",
        dashscope_api_key=api_key
    )

    print(f"   使用Embedding模型：text-embedding-v1")
    print(f"   文档数量：{len(documents)}")

    # 从文档创建FAISS向量存储
    # 这一步会：
    # 1. 对每个文档调用Embedding模型生成向量
    # 2. 把向量存入FAISS索引
    vectorstore = FAISS.from_documents(documents, embeddings)

    print("✅ 向量存储创建成功！")

    return vectorstore


def get_retriever(vectorstore, k=5, score_threshold=None):
    """
    获取检索器

    检索器是向量存储的查询接口

    参数说明：
    - k: 返回最相似的k个文档（Top-K检索）
    - score_threshold: 相似度阈值，低于此值的文档会被过滤

    对比Spring AI：
    vectorStore.similaritySearch(
        SearchRequest.query("住宿标准").withTopK(5)
    )

    LangChain的方式：
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    docs = retriever.get_relevant_documents("住宿标准")

    Args:
        vectorstore: 向量存储实例
        k: 返回文档数量
        score_threshold: 相似度阈值（可选）

    Returns:
        检索器实例
    """
    search_kwargs = {"k": k}

    # 如果设置了阈值，只返回相似度高于阈值的文档
    if score_threshold is not None:
        search_kwargs["score_threshold"] = score_threshold

    print(f"🔍 创建检索器（Top-K={k}）")

    return vectorstore.as_retriever(search_kwargs=search_kwargs)


def save_vectorstore(vectorstore, path: str):
    """
    保存向量存储到本地

    FAISS支持持久化，避免每次都重新生成向量

    Args:
        vectorstore: 向量存储实例
        path: 保存路径
    """
    vectorstore.save_local(path)
    print(f"💾 向量存储已保存到：{path}")


def load_vectorstore(path: str):
    """
    从本地加载向量存储

    Args:
        path: 保存路径

    Returns:
        向量存储实例
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        raise ValueError("未找到DASHSCOPE_API_KEY环境变量")

    embeddings = DashScopeEmbeddings(
        model="text-embedding-v1",
        dashscope_api_key=api_key
    )

    vectorstore = FAISS.load_local(
        path,
        embeddings,
        allow_dangerous_deserialization=True  # FAISS需要这个参数
    )

    print(f"📂 向量存储已加载：{path}")

    return vectorstore


# 测试代码
if __name__ == "__main__":
    """
    测试向量检索功能
    """
    print("测试向量检索模块...\n")

    from src.rag.loader import load_documents_from_text

    # 准备测试文档
    test_text = """
企业差旅管理规章

第一章 住宿标准
1. 一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚
2. 二线城市（杭州、成都、武汉等）：标准间不超过400元/晚
3. 三线及以下城市：标准间不超过300元/晚

第二章 交通标准
1. 市内交通：实报实销，需提供发票
2. 城际交通：距离<500公里用高铁二等座，距离≥500公里用飞机经济舱
    """

    try:
        # 1. 加载文档
        docs = load_documents_from_text(test_text, chunk_size=200)

        # 2. 创建向量存储
        vectorstore = create_vectorstore(docs)

        # 3. 创建检索器
        retriever = get_retriever(vectorstore, k=2)

        # 4. 测试检索
        print("\n测试查询：去上海出差住宿标准是多少？")
        results = retriever.get_relevant_documents("去上海出差住宿标准是多少")

        print(f"\n检索到 {len(results)} 个相关文档：")
        for i, doc in enumerate(results, 1):
            print(f"\n--- 文档 {i} ---")
            print(doc.page_content)

        print("\n✅ 向量检索测试成功！")

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        print("\n请检查：")
        print("1. 是否已配置DASHSCOPE_API_KEY")
        print("2. 是否已安装faiss-cpu：pip install faiss-cpu")
