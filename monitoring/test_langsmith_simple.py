"""简单的LangSmith测试"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=== LangSmith配置检查 ===")
print(f"LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2')}")
print(f"LANGCHAIN_API_KEY: {os.getenv('LANGCHAIN_API_KEY', 'NOT_SET')[:30]}...")
print(f"LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT')}")
print()

# 测试LangChain导入
try:
    from langchain_core.messages import HumanMessage
    from langchain_openai import ChatOpenAI
    print("✅ LangChain导入成功")
    
    # 简单调用测试
    llm = ChatOpenAI(
        model="qwen-plus",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DASHSCOPE_BASE_URL")
    )
    
    print("\n发送测试消息到LLM...")
    response = llm.invoke([HumanMessage(content="Hello, 这是监控测试")])
    print(f"✅ LLM响应: {response.content[:50]}...")
    print(f"\n🎯 访问 https://smith.langchain.com/projects 查看追踪记录")
    print(f"   项目名称: {os.getenv('LANGCHAIN_PROJECT')}")
    
except Exception as e:
    print(f"❌ 错误: {e}")
