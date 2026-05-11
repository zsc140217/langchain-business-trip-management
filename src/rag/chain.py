"""
RAG链模块
组装完整的RAG（检索增强生成）流程

对应Spring AI的：
chatClient.prompt()
    .user("根据以下内容回答：\n" + context + "\n问题：住宿标准")
    .advisors(new QuestionAnswerAdvisor(vectorStore))
    .call()
    .content()
"""
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser


def create_rag_chain(llm, retriever):
    """
    创建RAG链

    这是LangChain的核心概念：Chain（链）

    什么是Chain？
    - 把多个组件串联起来
    - 数据像流水线一样经过每个组件
    - 每个组件处理后传给下一个

    RAG链的流程：
    1. 用户提问
    2. 检索器找到相关文档
    3. 把文档和问题组合成Prompt
    4. LLM生成答案
    5. 返回答案和来源文档

    对比Spring AI：
    - Spring AI用Advisor模式（QuestionAnswerAdvisor）
    - LangChain用Chain模式（RetrievalQA）
    - Spring AI需要手动组装，LangChain有现成的链

    Args:
        llm: 语言模型实例
        retriever: 检索器实例

    Returns:
        RAG链实例
    """

    # 自定义Prompt模板
    # 这个模板定义了如何把检索到的文档和用户问题组合起来
    template = """你是一个企业差旅助手。请根据以下企业差旅规章回答用户的问题。

规章内容：
{context}

用户问题：{question}

请给出准确、详细的回答。如果规章中没有相关信息，请明确告知用户。
"""

    prompt = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )

    # 创建RetrievalQA链
    # chain_type="stuff"表示把所有检索到的文档都塞进Prompt
    # 其他选项：map_reduce（分别处理再合并）、refine（逐步优化）
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",  # 最简单的方式：把所有文档拼接
        retriever=retriever,
        return_source_documents=True,  # 返回来源文档
        chain_type_kwargs={"prompt": prompt}
    )

    return qa_chain


def create_rag_chain_lcel(llm, retriever):
    """
    使用LCEL（LangChain Expression Language）创建RAG链

    LCEL是LangChain 0.1+的新语法，更灵活

    语法：用管道符（|）连接组件
    chain = component1 | component2 | component3

    这个链的流程：
    1. retriever：检索相关文档
    2. format_docs：格式化文档
    3. prompt：生成Prompt
    4. llm：调用模型
    5. StrOutputParser：解析输出

    对比传统方式：
    - 传统：RetrievalQA.from_chain_type()
    - LCEL：用|连接组件
    - LCEL更灵活，可以自由组合

    Args:
        llm: 语言模型实例
        retriever: 检索器实例

    Returns:
        RAG链实例
    """

    # 格式化文档的函数
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Prompt模板
    template = """你是一个企业差旅助手。请根据以下企业差旅规章回答用户的问题。

规章内容：
{context}

用户问题：{question}

请给出准确、详细的回答。如果规章中没有相关信息，请明确告知用户。
"""

    prompt = PromptTemplate.from_template(template)

    # 使用LCEL组装链
    # RunnablePassthrough.assign()用于添加新字段
    rag_chain = (
        {
            "context": retriever | format_docs,  # 检索并格式化文档
            "question": RunnablePassthrough()  # 直接传递问题
        }
        | prompt  # 生成Prompt
        | llm  # 调用LLM
        | StrOutputParser()  # 解析输出为字符串
    )

    return rag_chain


# 测试代码
if __name__ == "__main__":
    """
    测试RAG链
    """
    print("测试RAG链模块...\n")

    from src.models.llm import get_llm
    from src.rag.loader import load_documents_from_text
    from src.rag.retriever import create_vectorstore, get_retriever

    # 准备测试数据
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
    """

    try:
        print("1️⃣ 初始化组件...")
        # 1. 加载文档
        docs = load_documents_from_text(test_text, chunk_size=300)

        # 2. 创建向量存储
        vectorstore = create_vectorstore(docs)

        # 3. 创建检索器
        retriever = get_retriever(vectorstore, k=3)

        # 4. 创建LLM
        llm = get_llm(temperature=0.3)  # 降低温度，让回答更准确

        # 5. 创建RAG链
        print("\n2️⃣ 创建RAG链...")
        rag_chain = create_rag_chain(llm, retriever)

        # 6. 测试查询
        print("\n3️⃣ 测试查询...")
        test_questions = [
            "去上海出差住宿能报多少钱？",
            "从北京到上海出差应该坐什么交通工具？",
            "出差期间每天的餐补是多少？"
        ]

        for question in test_questions:
            print(f"\n❓ 问题：{question}")
            result = rag_chain.invoke({"query": question})

            print(f"💡 回答：{result['result']}")
            print(f"📚 来源文档数：{len(result['source_documents'])}")

        print("\n✅ RAG链测试成功！")

        # 7. 测试LCEL版本
        print("\n4️⃣ 测试LCEL版本...")
        rag_chain_lcel = create_rag_chain_lcel(llm, retriever)
        answer = rag_chain_lcel.invoke("去杭州出差住宿标准是多少")
        print(f"💡 LCEL回答：{answer}")

        print("\n✅ 所有测试通过！")

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
