"""
本地运行LangSmith演示
运行这个脚本，然后去LangSmith网页截图
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("LangSmith本地演示")
print("=" * 60)

# 验证配置
print("\n[1/4] 验证配置...")
if os.getenv("LANGCHAIN_TRACING_V2") != "true":
    print("[FAIL] 请确保.env中有: LANGCHAIN_TRACING_V2=true")
    exit(1)

if not os.getenv("LANGCHAIN_API_KEY"):
    print("[FAIL] 请确保.env中有: LANGCHAIN_API_KEY")
    exit(1)

print("[OK] LangSmith配置正确")

# 运行一个真实的RAG示例
print("\n[2/4] 运行RAG查询...")

try:
    from langchain_community.chat_models import ChatTongyi
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough

    # 创建LLM
    llm = ChatTongyi(
        model="qwen-plus",
        temperature=0.7,
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
    )

    # 创建一个简单的RAG链
    # 模拟检索到的文档
    def fake_retriever(query):
        """模拟检索器"""
        docs = """
        差旅政策文档：
        1. 经济舱标准：国内航班1500元以内
        2. 酒店标准：一线城市500元/晚，二线城市300元/晚
        3. 餐补标准：100元/天
        """
        return docs

    # 创建Prompt模板
    prompt = ChatPromptTemplate.from_template("""
    根据以下差旅政策文档回答问题：

    {context}

    问题：{question}

    请简短回答（不超过100字）：
    """)

    # 组装RAG链（这会在LangSmith中显示为树状结构）
    rag_chain = (
        {
            "context": lambda x: fake_retriever(x["question"]),
            "question": lambda x: x["question"]
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    # 运行3个查询（会在LangSmith中显示3个Trace）
    queries = [
        "北京出差可以住多少钱的酒店？",
        "国内航班经济舱标准是多少？",
        "每天的餐补是多少？"
    ]

    print("\n正在运行查询...")
    for i, query in enumerate(queries, 1):
        print(f"\n查询{i}: {query}")
        result = rag_chain.invoke({"question": query})
        print(f"回答: {result[:80]}...")

    print("\n[OK] 查询完成！")

except Exception as e:
    print(f"\n[FAIL] 运行出错: {e}")
    print("\n可能的原因:")
    print("1. 通义千问API Key无效")
    print("2. 网络连接问题")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n[3/4] 数据已发送到LangSmith")

print("\n[4/4] 现在去截图！")
print("=" * 60)
print("截图步骤:")
print("=" * 60)
print("\n1. 打开浏览器访问: https://smith.langchain.com/")
print("2. 登录后点击左侧 'Projects'")
print("3. 选择项目 'travel-agent-demo'")
print("4. 你会看到3个查询记录")
print("\n5. 点击任意一个查询，你会看到:")
print("   - 调用链的树状结构")
print("   - RunnableParallel (并行执行)")
print("   - ChatPromptTemplate (Prompt构建)")
print("   - ChatTongyi (LLM调用)")
print("   - StrOutputParser (输出解析)")
print("\n6. 点击每个节点，可以看到:")
print("   - 输入数据")
print("   - 输出数据")
print("   - 耗时")
print("\n7. 截图保存，面试时展示！")

print("\n" + "=" * 60)
print("面试话术:")
print("=" * 60)
print("""
"这是我本地运行的RAG查询（展示截图）。

看，LangSmith自动追踪了整个调用链：
1. 检索器获取文档
2. Prompt模板构建
3. LLM调用
4. 输出解析

每个节点都能点击查看输入输出和耗时。

这让我能快速定位问题：
- 如果回答不准确，点击检索器看文档是否相关
- 如果响应慢，看哪个环节耗时长
- 如果成本高，看Token使用量

这就是可观测性的价值。Spring AI只能靠日志，
看不到这样的可视化调用链。"
""")

print("=" * 60)
print("[SUCCESS] 完成！现在去LangSmith截图吧！")
print("=" * 60)
