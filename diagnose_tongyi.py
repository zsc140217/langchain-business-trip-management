"""
通义千问API调用问题诊断

问题描述：
在langchain-business-trip-management项目中调用通义千问API时报错：
KeyError: 'request'

错误堆栈：
File "langchain_community/chat_models/tongyi.py", line 669, in _generate
    resp = self.completion_with_retry(**params)
...
KeyError: 'request'

请在你能正常运行的项目中测试以下代码，帮我找出问题：
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("通义千问API诊断测试")
print("=" * 60)

# 1. 检查API Key
print("\n[检查1] API Key配置")
api_key = os.getenv("DASHSCOPE_API_KEY")
if api_key:
    print(f"[OK] API Key存在: {api_key[:20]}...")
else:
    print("[FAIL] API Key不存在")
    exit(1)

# 2. 检查依赖版本
print("\n[检查2] 依赖版本")
try:
    import langchain_community
    print(f"[OK] langchain-community: {langchain_community.__version__}")
except:
    print("[FAIL] langchain-community未安装")

try:
    import dashscope
    print(f"[OK] dashscope: {dashscope.__version__}")
except:
    print("[FAIL] dashscope未安装")

try:
    import langchain_core
    print(f"[OK] langchain-core: {langchain_core.__version__}")
except:
    print("[FAIL] langchain-core未安装")

# 3. 测试最简单的调用
print("\n[检查3] 测试API调用")
try:
    from langchain_community.chat_models import ChatTongyi
    from langchain_core.messages import HumanMessage

    # 创建LLM（使用你项目中能工作的配置）
    llm = ChatTongyi(
        model="qwen-plus",
        temperature=0.7,
        dashscope_api_key=api_key
    )

    print("正在调用API...")

    # 最简单的调用
    messages = [HumanMessage(content="你好")]
    response = llm.invoke(messages)

    print(f"[OK] API调用成功")
    print(f"回答: {response.content[:50]}...")

except Exception as e:
    print(f"[FAIL] API调用失败: {e}")
    import traceback
    traceback.print_exc()

# 4. 测试LCEL链式调用
print("\n[检查4] 测试LCEL链式调用")
try:
    from langchain_community.chat_models import ChatTongyi
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    llm = ChatTongyi(
        model="qwen-plus",
        temperature=0.7,
        dashscope_api_key=api_key
    )

    prompt = ChatPromptTemplate.from_template("回答问题：{question}")

    chain = prompt | llm | StrOutputParser()

    print("正在测试链式调用...")
    result = chain.invoke({"question": "1+1等于几？"})

    print(f"[OK] 链式调用成功")
    print(f"回答: {result[:50]}...")

except Exception as e:
    print(f"[FAIL] 链式调用失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
print("\n请把上面的输出发给我，特别是：")
print("1. 依赖版本号")
print("2. 哪个测试失败了")
print("3. 完整的错误信息")
