"""
Module 1: Simple RAG - Document Loader
文档加载和分块模块

核心功能：
1. 加载文本文档
2. 使用RecursiveCharacterTextSplitter切分文档
3. 返回Document对象列表供向量化使用
"""
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List


def load_and_split_documents(
    file_path: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Document]:
    """
    加载并切分文档

    工作流程：
    1. 使用TextLoader加载文本文件
    2. 使用RecursiveCharacterTextSplitter递归切分
    3. 返回切分后的Document列表

    参数说明：
    - chunk_size: 每个文档块的最大字符数（推荐500-1000）
    - chunk_overlap: 相邻块的重叠字符数（推荐10-20%的chunk_size）

    为什么要切分？
    - 向量检索需要合适粒度的文档块
    - 太大：检索不精确，包含太多无关信息
    - 太小：上下文不完整，语义信息丢失

    Args:
        file_path: 文档路径
        chunk_size: 块大小
        chunk_overlap: 重叠大小

    Returns:
        Document列表
    """
    # 加载文档
    loader = TextLoader(file_path, encoding='utf-8')
    documents = loader.load()

    # 创建文本切分器
    # RecursiveCharacterTextSplitter会按优先级尝试不同分隔符
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # 中文友好的分隔符：段落 > 句子 > 标点 > 空格
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )

    # 切分文档
    split_docs = text_splitter.split_documents(documents)

    print(f"📄 文档加载完成：{file_path}")
    print(f"   原始文档数：{len(documents)}")
    print(f"   切分后块数：{len(split_docs)}")
    print(f"   平均块大小：{sum(len(d.page_content) for d in split_docs) // len(split_docs)} 字符")

    return split_docs


def load_documents_from_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Document]:
    """
    从字符串加载文档（用于测试）

    Args:
        text: 文本内容
        chunk_size: 块大小
        chunk_overlap: 重叠大小

    Returns:
        Document列表
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )

    # 创建Document对象并切分
    doc = Document(page_content=text, metadata={"source": "text_input"})
    split_docs = text_splitter.split_documents([doc])

    return split_docs


# 示例和测试
if __name__ == "__main__":
    print("=== Module 1: Document Loader 测试 ===\n")

    # 测试文本
    sample_text = """
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
    """

    # 测试切分
    docs = load_documents_from_text(sample_text, chunk_size=200, chunk_overlap=30)

    print("\n切分结果：")
    for i, doc in enumerate(docs, 1):
        print(f"\n--- 块 {i} ({len(doc.page_content)} 字符) ---")
        print(doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content)

    print("\n[OK] 测试通过！")
