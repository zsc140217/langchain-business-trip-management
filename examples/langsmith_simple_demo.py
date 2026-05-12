"""
LangSmith快速演示 - 使用通义千问
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 60)
print("LangSmith配置检查")
print("=" * 60)

# 检查配置
langsmith_enabled = os.getenv("LANGCHAIN_TRACING_V2")
langsmith_key = os.getenv("LANGCHAIN_API_KEY")
langsmith_project = os.getenv("LANGCHAIN_PROJECT")
dashscope_key = os.getenv("DASHSCOPE_API_KEY")

if langsmith_enabled == "true" and langsmith_key:
    print(f"[OK] LangSmith已启用")
    print(f"[OK] API Key: {langsmith_key[:20]}...")
    print(f"[OK] 项目名称: {langsmith_project}")
else:
    print("[FAIL] LangSmith未配置")
    exit(1)

if dashscope_key:
    print(f"[OK] 通义千问API Key: {dashscope_key[:20]}...")
else:
    print("[FAIL] 通义千问API Key未配置")
    exit(1)

print("\n" + "=" * 60)
print("示例1: 简单的LLM调用")
print("=" * 60)

try:
    from langchain_community.chat_models import ChatTongyi
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    # 创建LLM
    llm = ChatTongyi(
        model="qwen-plus",
        temperature=0.7,
        dashscope_api_key=dashscope_key
    )

    # 创建Prompt模板
    prompt = ChatPromptTemplate.from_template(
        "你是一个旅行助手。用户问：{question}\n请简短回答（不超过50字）："
    )

    # 创建输出解析器
    output_parser = StrOutputParser()

    # 组装链（LCEL语法）
    chain = prompt | llm | output_parser

    # 运行查询（自动追踪到LangSmith）
    print("\n运行查询: '北京明天天气怎么样？'")
    result = chain.invoke({"question": "北京明天天气怎么样？"})

    print(f"\n回答: {result}")

    print("\n" + "=" * 60)
    print("[SUCCESS] 调用成功！")
    print("=" * 60)

except Exception as e:
    print(f"\n[FAIL] 运行出错: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("示例2: 多轮对话")
print("=" * 60)

try:
    # 第一轮对话
    print("\n第1轮对话:")
    result1 = chain.invoke({"question": "我要去北京出差"})
    print(f"用户: 我要去北京出差")
    print(f"助手: {result1[:100]}...")

    # 第二轮对话
    print("\n第2轮对话:")
    result2 = chain.invoke({"question": "推荐一下酒店"})
    print(f"用户: 推荐一下酒店")
    print(f"助手: {result2[:100]}...")

    print("\n" + "=" * 60)
    print("[SUCCESS] 对话成功！")
    print("=" * 60)

except Exception as e:
    print(f"\n[FAIL] 运行出错: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("查看LangSmith Trace")
print("=" * 60)
print("\n现在去LangSmith查看刚才的调用:")
print("1. 访问: https://smith.langchain.com/")
print("2. 点击左侧 'Projects'")
print(f"3. 选择项目: {langsmith_project}")
print("4. 看到刚才的2-3次调用记录")
print("\n你会看到:")
print("  - 完整的调用链（Prompt -> LLM -> Parser）")
print("  - 每个步骤的输入输出")
print("  - 耗时统计")
print("  - Token使用量")
print("\n" + "=" * 60)
print("面试话术:")
print("=" * 60)
print('"我的项目集成了LangSmith。刚才运行的代码，')
print('所有调用都自动追踪到了LangSmith。')
print('我能看到完整的调用链、每个步骤的输入输出、')
print('耗时统计和Token使用量。')
print('这是Spring AI完全没有的功能。"')
print("=" * 60)
