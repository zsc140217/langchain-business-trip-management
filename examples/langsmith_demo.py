"""
LangSmith快速上手示例
演示如何使用LangSmith追踪LangChain调用
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 验证LangSmith配置
print("=" * 60)
print("LangSmith配置检查")
print("=" * 60)

langsmith_enabled = os.getenv("LANGCHAIN_TRACING_V2")
langsmith_key = os.getenv("LANGCHAIN_API_KEY")
langsmith_project = os.getenv("LANGCHAIN_PROJECT")

if langsmith_enabled == "true" and langsmith_key:
    print(f"[OK] LangSmith已启用")
    print(f"[OK] API Key: {langsmith_key[:20]}...")
    print(f"[OK] 项目名称: {langsmith_project}")
else:
    print("[FAIL] LangSmith未配置")
    sys.exit(1)

print("\n" + "=" * 60)
print("示例1: 简单的LLM调用")
print("=" * 60)

try:
    from langchain_community.chat_models import ChatTongyi
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema.output_parser import StrOutputParser

    # 创建一个简单的链
    llm = ChatTongyi(
        model="qwen-plus",
        temperature=0.7
    )

    prompt = ChatPromptTemplate.from_template(
        "你是一个旅行助手。用户问：{question}\n请简短回答（不超过50字）："
    )

    chain = prompt | llm | StrOutputParser()

    # 运行查询（自动追踪到LangSmith）
    print("\n运行查询: '北京明天天气怎么样？'")
    result = chain.invoke({"question": "北京明天天气怎么样？"})

    print(f"\n回答: {result}")

    print("\n" + "=" * 60)
    print("[SUCCESS] 调用成功！")
    print("=" * 60)
    print("\n现在去LangSmith查看Trace:")
    print("1. 访问: https://smith.langchain.com/")
    print("2. 点击左侧 'Projects'")
    print(f"3. 选择项目: {langsmith_project}")
    print("4. 看到刚才的调用记录")
    print("\n你会看到:")
    print("  - 完整的调用链（Prompt → LLM → Parser）")
    print("  - 每个步骤的输入输出")
    print("  - 耗时统计")
    print("  - Token使用量")

except ImportError as e:
    print(f"\n[FAIL] 缺少依赖: {e}")
    print("\n请安装: pip install langchain-community")
except Exception as e:
    print(f"\n[FAIL] 运行出错: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("示例2: 带记忆的对话")
print("=" * 60)

try:
    from langchain.memory import ConversationBufferMemory
    from langchain.chains import ConversationChain

    # 创建带记忆的对话链
    memory = ConversationBufferMemory()
    conversation = ConversationChain(
        llm=llm,
        memory=memory,
        verbose=False
    )

    # 多轮对话
    print("\n第1轮对话:")
    response1 = conversation.predict(input="我要去北京出差")
    print(f"用户: 我要去北京出差")
    print(f"助手: {response1[:100]}...")

    print("\n第2轮对话:")
    response2 = conversation.predict(input="那里的天气怎么样？")
    print(f"用户: 那里的天气怎么样？")
    print(f"助手: {response2[:100]}...")

    print("\n" + "=" * 60)
    print("[SUCCESS] 对话成功！")
    print("=" * 60)
    print("\n在LangSmith中你会看到:")
    print("  - 两次对话的完整Trace")
    print("  - 记忆系统如何工作")
    print("  - 上下文如何传递")

except Exception as e:
    print(f"\n[FAIL] 运行出错: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("下一步:")
print("=" * 60)
print("1. 访问 https://smith.langchain.com/")
print("2. 查看刚才的Trace")
print("3. 点击任意节点，查看输入输出")
print("4. 体验可视化调试的威力！")
print("\n" + "=" * 60)
