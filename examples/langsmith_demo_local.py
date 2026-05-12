"""
LangSmith本地演示 - 模拟RAG流程
不需要真实API，直接生成可视化调用链
运行后去LangSmith截图
"""

import os
import time
from dotenv import load_dotenv
from langsmith import traceable

load_dotenv()

print("=" * 60)
print("LangSmith本地演示 - 模拟RAG流程")
print("=" * 60)

# 验证配置
print("\n[1/3] 验证配置...")
if os.getenv("LANGCHAIN_TRACING_V2") != "true":
    print("[FAIL] 请确保.env中有: LANGCHAIN_TRACING_V2=true")
    exit(1)

if not os.getenv("LANGCHAIN_API_KEY"):
    print("[FAIL] 请确保.env中有: LANGCHAIN_API_KEY")
    exit(1)

print("[OK] LangSmith配置正确")

# 使用@traceable装饰器，LangSmith会自动追踪这些函数
@traceable(name="Document Retriever")
def retrieve_documents(query: str) -> str:
    """模拟文档检索"""
    time.sleep(0.1)  # 模拟检索耗时

    docs = {
        "北京": "差旅政策：一线城市酒店标准500元/晚，二线城市300元/晚",
        "航班": "差旅政策：国内航班经济舱标准1500元以内",
        "餐补": "差旅政策：餐补标准100元/天"
    }

    for key, doc in docs.items():
        if key in query:
            return doc

    return "差旅政策：请参考公司差旅管理规定"

@traceable(name="Prompt Builder")
def build_prompt(query: str, context: str) -> str:
    """模拟Prompt构建"""
    time.sleep(0.05)

    prompt = f"""根据以下差旅政策文档回答问题：

{context}

问题：{query}

请简短回答："""

    return prompt

@traceable(name="LLM Call")
def call_llm(prompt: str) -> str:
    """模拟LLM调用"""
    time.sleep(0.3)  # 模拟LLM耗时

    # 模拟回答
    if "北京" in prompt or "酒店" in prompt:
        return "根据差旅政策，北京属于一线城市，酒店标准为500元/晚。"
    elif "航班" in prompt:
        return "根据差旅政策，国内航班经济舱标准为1500元以内。"
    elif "餐补" in prompt:
        return "根据差旅政策，每天的餐补标准为100元。"
    else:
        return "请参考公司差旅管理规定。"

@traceable(name="Output Parser")
def parse_output(response: str) -> str:
    """模拟输出解析"""
    time.sleep(0.02)
    return response.strip()

@traceable(name="RAG Chain")
def rag_chain(query: str) -> str:
    """完整的RAG链 - 会在LangSmith中显示为树状结构"""

    # 步骤1: 检索文档
    context = retrieve_documents(query)

    # 步骤2: 构建Prompt
    prompt = build_prompt(query, context)

    # 步骤3: 调用LLM
    response = call_llm(prompt)

    # 步骤4: 解析输出
    final_answer = parse_output(response)

    return final_answer

# 运行演示
print("\n[2/3] 运行RAG查询...")

queries = [
    "北京出差可以住多少钱的酒店？",
    "国内航班经济舱标准是多少？",
    "每天的餐补是多少？"
]

print("\n正在运行查询（会自动发送到LangSmith）...")
for i, query in enumerate(queries, 1):
    print(f"\n查询{i}: {query}")
    result = rag_chain(query)
    print(f"回答: {result}")

print("\n[OK] 查询完成！")

print("\n[3/3] 现在去LangSmith截图！")
print("=" * 60)
print("截图步骤:")
print("=" * 60)
print("""
1. 打开浏览器: https://smith.langchain.com/

2. 登录后点击左侧 'Projects'

3. 选择项目 'travel-agent-demo'

4. 你会看到3个 'RAG Chain' 记录

5. 点击任意一个，你会看到树状调用链:
   RAG Chain
   ├─ Document Retriever (检索文档)
   ├─ Prompt Builder (构建Prompt)
   ├─ LLM Call (调用LLM)
   └─ Output Parser (解析输出)

6. 点击每个节点，可以看到:
   - Input (输入数据)
   - Output (输出数据)
   - Latency (耗时)
   - Metadata (元数据)

7. 截图保存！重点截:
   - 树状调用链的全景图
   - 点击某个节点后的详细信息
   - 性能统计（如果有）

8. 面试时展示这些截图，说:
   "这是我本地运行的RAG查询，LangSmith自动追踪了
    整个调用链。每个环节的输入输出和耗时都能看到。
    这让我能快速定位问题和优化性能。"
""")

print("=" * 60)
print("[SUCCESS] 完成！数据已发送到LangSmith！")
print("=" * 60)
