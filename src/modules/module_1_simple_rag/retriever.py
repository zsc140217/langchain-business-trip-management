"""
Module 1: Simple RAG - FAISS Retriever
向量检索器模块

核心功能：
1. 使用DashScope Embeddings生成向量
2. 创建FAISS向量存储
3. 提供检索接口
"""
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document
from typing import List, Optional
import os


def create_faiss_vectorstore(
    documents: List[Document],
    embedding_model: str = "text-embedding-v1"
) -> FAISS:
    """
    创建FAISS向量存储

    FAISS (Facebook AI Similarity Search)：
    - 高效的向量相似度搜索库
    - 支持本地运行，无需外部服务
    - 适合中小规模数据（<100万条）

    工作流程：
    1. 使用Embedding模型将文本转换为向量
    2. 将向量存储到FAISS索引中
    3. 支持快速相似度检索

    Args:
        documents: Document列表
        embedding_model: 嵌入模型名称

    Returns:
        FAISS向量存储实例
    """
    # 获取API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未设置DASHSCOPE_API_KEY环境变量")

    print(f"[INFO] Creating FAISS vectorstore...")
    print(f"   Embedding model: {embedding_model}")
    print(f"   Documents: {len(documents)}")

    # 创建Embedding模型
    embeddings = DashScopeEmbeddings(
        model=embedding_model,
        dashscope_api_key=api_key
    )

    # 从文档创建FAISS向量存储
    # 这会调用Embedding API为每个文档生成向量
    vectorstore = FAISS.from_documents(documents, embeddings)

    print("[OK] Vectorstore created successfully!")

    return vectorstore


def create_retriever(
    vectorstore: FAISS,
    k: int = 5,
    score_threshold: Optional[float] = None
):
    """
    创建检索器

    检索策略：
    - search_type="similarity": 基于余弦相似度的Top-K检索
    - k: 返回最相似的k个文档
    - score_threshold: 可选的相似度阈值过滤

    Args:
        vectorstore: FAISS向量存储
        k: 返回文档数量
        score_threshold: 相似度阈值（可选）

    Returns:
        Retriever实例
    """
    search_kwargs = {"k": k}

    if score_threshold is not None:
        search_kwargs["score_threshold"] = score_threshold

    print(f"[INFO] Creating retriever (Top-K={k})")

    return vectorstore.as_retriever(search_kwargs=search_kwargs)


def save_vectorstore(vectorstore: FAISS, path: str):
    """
    保存向量存储到本地

    Args:
        vectorstore: FAISS向量存储
        path: 保存路径
    """
    vectorstore.save_local(path)
    print(f"[SAVE] Vectorstore saved to: {path}")


def load_vectorstore(path: str, embedding_model: str = "text-embedding-v1") -> FAISS:
    """
    从本地加载向量存储

    Args:
        path: 保存路径
        embedding_model: 嵌入模型名称

    Returns:
        FAISS向量存储实例
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未设置DASHSCOPE_API_KEY环境变量")

    embeddings = DashScopeEmbeddings(
        model=embedding_model,
        dashscope_api_key=api_key
    )

    vectorstore = FAISS.load_local(
        path,
        embeddings,
        allow_dangerous_deserialization=True
    )

    print(f"[LOAD] Vectorstore loaded from: {path}")

    return vectorstore


# 示例和测试
if __name__ == "__main__":
    print("=== Module 1: FAISS Retriever 测试 ===\n")

    from loader import load_documents_from_text

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

第三章 餐饮补贴
1. 早餐：30元/天
2. 午餐：50元/天
3. 晚餐：50元/天
    """

    try:
        # 1. 加载文档
        print("Step 1: Loading documents...")
        docs = load_documents_from_text(test_text, chunk_size=200)

        # 2. 创建向量存储
        print("\nStep 2: Creating vectorstore...")
        vectorstore = create_faiss_vectorstore(docs)

        # 3. 创建检索器
        print("\nStep 3: Creating retriever...")
        retriever = create_retriever(vectorstore, k=3)

        # 4. 测试检索
        print("\nStep 4: Testing retrieval...")
        query = "去上海出差住宿能报多少钱？"
        print(f"查询：{query}")

        results = retriever.get_relevant_documents(query)

        print(f"\n检索到 {len(results)} 个相关文档：")
        for i, doc in enumerate(results, 1):
            print(f"\n--- 文档 {i} ---")
            print(doc.page_content)

        print("\n[PASS] All tests passed!")

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        print("\n请检查：")
        print("1. 环境变量DASHSCOPE_API_KEY是否已设置")
        print("2. 是否已安装依赖：pip install faiss-cpu dashscope")
