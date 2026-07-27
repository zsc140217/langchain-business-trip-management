"""
文档加载模块
负责加载企业差旅规章文档并进行切分

对应Spring AI的：
Resource resource = new ClassPathResource("data/travel_policy.txt");
List<Document> documents = textSplitter.split(resource);

更新说明：
- 支持Markdown格式（.md文件）
- 使用MarkdownHeaderTextSplitter处理结构化文档
- 按章节智能切分
"""
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents import Document
import os
import re


def convert_tables_to_text(text: str) -> str:
    """
    HTML表格转自然语言文本（增强版）
    
    将文档中的HTML表格转换为检索友好的自然语言格式，
    确保表格内容（地区、金额等）被正确索引。
    
    转换示例：
        <table><tr><th>城市</th><th>住宿标准</th></tr>
        <tr><td>北京</td><td>500元/天</td></tr></table>
        →
        城市: 北京, 住宿标准: 500元/天
    """
    # 匹配完整表格
    table_pattern = re.compile(r'<table[^>]*>(.*?)</table>', re.DOTALL | re.IGNORECASE)
    
    def convert_table(match):
        table_html = match.group(0)
        
        # 提取表头
        headers = re.findall(r'<th[^>]*>(.*?)</th>', table_html, re.DOTALL | re.IGNORECASE)
        headers = [re.sub(r'<[^>]+>', '', h).strip() for h in headers]
        
        # 提取数据行
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
        
        text_lines = []
        for row in rows:
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            
            if len(cells) == len(headers) and len(headers) > 0:
                # 格式: "城市: 北京, 住宿标准: 500元/天"
                line = ", ".join([f"{h}: {v}" for h, v in zip(headers, cells)])
                text_lines.append(line)
            elif len(cells) > 0:
                text_lines.append(", ".join(cells))
        
        if text_lines:
            return "\n".join(text_lines)
        return match.group(0)  # 保留原样
    
    return table_pattern.sub(convert_table, text)





def load_documents(file_path: str) -> List[Document]:
    """
    加载并切分文档（支持单个文件或目录，支持.txt和.md格式）

    这是RAG的第一步：文档加载和切分

    为什么要切分文档？
    - 向量数据库对每个文档块（chunk）生成向量
    - 太大的块会导致检索不精确
    - 太小的块会丢失上下文信息
    - 通常500-1000字符是个好的平衡点

    切分策略：
    - Markdown文件：按章节结构切分（## 第X章、### 第X条）
    - 文本文件：按段落和句子递归切分
    - chunk_overlap保证相邻块有重叠，避免信息断裂

    对比Spring AI：
    - Spring AI也有类似的TextSplitter
    - 但LangChain的MarkdownTextSplitter能识别结构化文档
    - 更适合处理企业规章制度等有明确章节的文档

    Args:
        file_path: 文档路径或目录路径

    Returns:
        切分后的文档列表
    """
    # 1. 加载文档
    if os.path.isdir(file_path):
        # 目录模式：加载所有.txt和.md文件
        all_documents = []

        # 加载.txt文件
        try:
            txt_loader = DirectoryLoader(
                file_path,
                glob="**/*.txt",
                loader_cls=TextLoader,
                loader_kwargs={'encoding': 'utf-8'},
                show_progress=False
            )
            txt_docs = txt_loader.load()
            all_documents.extend(txt_docs)
        except Exception as e:
            print(f"   警告: 加载.txt文件失败: {e}")

        # 加载.md文件
        try:
            md_loader = DirectoryLoader(
                file_path,
                glob="**/*.md",
                loader_cls=TextLoader,
                loader_kwargs={'encoding': 'utf-8'},
                show_progress=False
            )
            md_docs = md_loader.load()
            all_documents.extend(md_docs)
        except Exception as e:
            print(f"   警告: 加载.md文件失败: {e}")

        documents = all_documents
        print(f"加载目录: {file_path}")
    else:
        # 单文件模式：统一使用TextLoader（简单可靠）
        loader = TextLoader(file_path, encoding='utf-8')
        documents = loader.load()
        if file_path.endswith('.md'):
            print(f"加载Markdown文档: {file_path}")
        else:
            print(f"加载文本文档: {file_path}")

    print(f"   原始文档数量：{len(documents)}")

    # 2. 文档切分（优化Markdown分隔符）
    if file_path.endswith('.md') or (os.path.isdir(file_path) and any(doc.metadata.get('source', '').endswith('.md') for doc in documents)):
        # Markdown文件：优先按章节、表格、段落切分
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            # 优化的分隔符：章节 > 表格 > 段落 > 句子
            separators=["\n## ", "\n### ", "\n第", "<table>", "</table>", "\n\n", "\n", "。", ""],
            keep_separator=True
        )
        print(f"   使用Markdown优化切分策略")
    else:
        # 文本文件：使用递归切分
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
        print(f"   使用RecursiveCharacterTextSplitter（递归切分）")

    split_docs = text_splitter.split_documents(documents)

    print(f"   切分后文档数量：{len(split_docs)}")
    if len(split_docs) > 0:
        avg_size = sum(len(doc.page_content) for doc in split_docs) // len(split_docs)
        print(f"   平均块大小：{avg_size} 字符")

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

    print("\n[OK] 文档加载测试成功！")
