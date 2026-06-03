"""
Module 1: Simple RAG - RAG Chain with LCEL
基础RAG链实现

核心功能：
1. 使用LCEL (LangChain Expression Language) 构建RAG链
2. 组合检索器、Prompt、LLM和输出解析器
3. 提供问答接口

LCEL语法：
- 使用管道符 | 连接组件
- 数据从左到右流动
- 每个组件处理数据并传给下一个
"""
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms import Tongyi
from typing import List
from langchain_core.documents import Document
import os


def format_docs(docs: List[Document]) -> str:
    """
    格式化文档列表为字符串

    Args:
        docs: Document列表

    Returns:
        格式化后的字符串
    """
    return "\n\n".join(doc.page_content for doc in docs)


def create_rag_chain_lcel(retriever, llm=None):
    """
    使用LCEL创建RAG链

    LCEL架构：

    输入(question)
        ↓
    { context: retriever | format_docs, question: passthrough }
        ↓
    prompt模板
        ↓
    LLM
        ↓
    输出解析器
        ↓
    最终答案(string)

    优势：
    - 声明式语法，清晰易懂
    - 自动处理数据流转
    - 支持流式输出
    - 易于组合和扩展

    Args:
        retriever: 检索器实例
        llm: 语言模型实例（可选，默认使用通义千问）

    Returns:
        RAG链实例
    """
    # 创建LLM（如果未提供）
    if llm is None:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("未设置DASHSCOPE_API_KEY环境变量")

        llm = Tongyi(
            model_name="qwen-plus",
            dashscope_api_key=api_key,
            temperature=0.3  # 降低温度使回答更准确
        )

    # 定义Prompt模板
    template = """你是一个企业差旅助手。请根据以下企业差旅规章准确回答用户的问题。

企业差旅规章：
{context}

用户问题：{question}

请基于上述规章给出准确、详细的回答。如果规章中没有相关信息，请明确告知用户。
"""

    prompt = PromptTemplate.from_template(template)

    # 使用LCEL组装链
    # 语法说明：
    # 1. {context: ..., question: ...} 创建包含两个字段的字典
    # 2. retriever | format_docs：先检索文档，再格式化
    # 3. RunnablePassthrough()：直接传递输入
    # 4. | prompt：将字典传入Prompt模板
    # 5. | llm：调用语言模型
    # 6. | StrOutputParser()：解析输出为字符串
    rag_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    print("[OK] RAG链创建成功（LCEL）")

    return rag_chain


def create_rag_chain_with_sources(retriever, llm=None):
    """
    创建带来源文档的RAG链

    与基础版本的区别：
    - 同时返回答案和来源文档
    - 便于验证答案的准确性

    Args:
        retriever: 检索器实例
        llm: 语言模型实例（可选）

    Returns:
        RAG链实例，返回 {"answer": str, "source_documents": List[Document]}
    """
    if llm is None:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("未设置DASHSCOPE_API_KEY环境变量")

        llm = Tongyi(
            model_name="qwen-plus",
            dashscope_api_key=api_key,
            temperature=0.3
        )

    template = """你是一个企业差旅助手。请根据以下企业差旅规章准确回答用户的问题。

企业差旅规章：
{context}

用户问题：{question}

请基于上述规章给出准确、详细的回答。如果规章中没有相关信息，请明确告知用户。
"""

    prompt = PromptTemplate.from_template(template)

    # 使用RunnablePassthrough.assign()保留检索的文档
    from langchain_core.runnables import RunnableParallel

    # 并行执行检索和问题传递
    rag_chain = RunnableParallel(
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
            "source_documents": retriever
        }
    ).assign(
        # 在保留source_documents的同时生成答案
        answer=lambda x: (prompt | llm | StrOutputParser()).invoke({
            "context": x["context"],
            "question": x["question"]
        })
    )

    print("[OK] RAG链创建成功（带来源）")

    return rag_chain


# 示例和测试
if __name__ == "__main__":
    print("=== Module 1: RAG Chain with LCEL 测试 ===\n")

    from loader import load_documents_from_text
    from retriever import create_faiss_vectorstore, create_retriever

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
3. 出租车：仅限机场、火车站往返酒店

第三章 餐饮补贴
1. 早餐：30元/天
2. 午餐：50元/天
3. 晚餐：50元/天
4. 总计：130元/天

第四章 其他规定
1. 出差需提前3天申请
2. 出差结束后7天内提交报销
    """

    try:
        # 1. 加载文档
        print("Step 1: 加载文档...")
        docs = load_documents_from_text(test_text, chunk_size=300, chunk_overlap=50)

        # 2. 创建向量存储
        print("\nStep 2: 创建向量存储...")
        vectorstore = create_faiss_vectorstore(docs)

        # 3. 创建检索器
        print("\nStep 3: 创建检索器...")
        retriever = create_retriever(vectorstore, k=3)

        # 4. 创建RAG链
        print("\nStep 4: 创建RAG链...")
        rag_chain = create_rag_chain_lcel(retriever)

        # 5. 测试问答
        print("\nStep 5: 测试问答...")
        test_questions = [
            "去上海出差住宿能报多少钱？",
            "从北京到上海应该坐什么交通工具？",
            "出差期间每天的餐补是多少？"
        ]

        for question in test_questions:
            print(f"\n❓ {question}")
            answer = rag_chain.invoke(question)
            print(f"💡 {answer}")

        # 6. 测试带来源的链
        print("\n\nStep 6: 测试带来源的RAG链...")
        rag_chain_with_sources = create_rag_chain_with_sources(retriever)

        question = "出差报销有什么时间要求？"
        print(f"\n❓ {question}")
        result = rag_chain_with_sources.invoke(question)

        print(f"💡 答案：{result['answer']}")
        print(f"\n📚 来源文档数：{len(result['source_documents'])}")
        for i, doc in enumerate(result['source_documents'], 1):
            print(f"\n--- 来源 {i} ---")
            print(doc.page_content[:100] + "...")

        print("\n[OK] 所有测试通过！")

    except Exception as e:
        print(f"\n[FAIL] 测试失败：{e}")
        import traceback
        traceback.print_exc()
        print("\n请检查：")
        print("1. 环境变量DASHSCOPE_API_KEY是否已设置")
        print("2. API Key是否有效且有余额")
