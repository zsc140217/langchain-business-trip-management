"""
文档加载模块
负责加载企业差旅规章文档并进行切分

对应Spring AI的：
Resource resource = new ClassPathResource("data/travel_policy.txt");
List<Document> documents = textSplitter.split(resource);
"""
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
from langchain.schema import Document


def load_documents(file_path: str) -> List[Document]:
    """
    加载并切分文档

    这是RAG的第一步：文档加载和切分

    为什么要切分文档？
    - 向量数据库对每个文档块（chunk）生成向量
    - 太大的块会导致检索不精确
    - 太小的块会丢失上下文信息
    - 通常500-1000字符是个好的平衡点

    切分策略：
    1. 优先按段落切分（\n\n）
    2. 其次按句子切分（。！？）
    3. 最后按字符切分
    4. chunk_overlap保证相邻块有重叠，避免信息断裂

    对比Spring AI：
    - Spring AI也有类似的TextSplitter
    - 但LangChain的RecursiveCharacterTextSplitter更智能
    - 它会递归尝试不同的分隔符，直到块大小合适

    Args:
        file_path: 文档路径

    Returns:
        切分后的文档列表
    """
    # 1. 加载文档
    loader = TextLoader(file_path, encoding='utf-8')
    documents = loader.load()

    print(f"📄 加载文档：{file_path}")
    print(f"   原始文档数量：{len(documents)}")

    # 2. 文档切分
    # RecursiveCharacterTextSplitter是LangChain的核心工具
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # 每个块的最大字符数
        chunk_overlap=50,  # 相邻块的重叠字符数
        # 分隔符优先级：段落 > 句子 > 逗号 > 空格
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )

    split_docs = text_splitter.split_documents(documents)

    print(f"   切分后文档数量：{len(split_docs)}")
    print(f"   平均块大小：{sum(len(doc.page_content) for doc in split_docs) // len(split_docs)} 字符")

    return split_docs


def load_documents_from_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[Document]:
    """
    从文本字符串加载文档（用于测试）

    Args:
        text: 文本内容
        chunk_size: 块大小
        chunk_overlap: 重叠大小

    Returns:
        切分后的文档列表
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )

    # 创建Document对象
    doc = Document(page_content=text)
    split_docs = text_splitter.split_documents([doc])

    return split_docs


# 测试代码
if __name__ == "__main__":
    """
    测试文档加载功能
    """
    print("测试文档加载模块...\n")

    # 测试示例文本
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
    """

    docs = load_documents_from_text(test_text, chunk_size=200, chunk_overlap=20)

    print("\n切分结果：")
    for i, doc in enumerate(docs, 1):
        print(f"\n--- 块 {i} ---")
        print(doc.page_content)

    print("\n✅ 文档加载测试成功！")
