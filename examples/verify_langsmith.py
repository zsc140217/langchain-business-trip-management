"""
LangSmith配置验证
验证LangSmith是否正确配置
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 60)
print("LangSmith配置验证")
print("=" * 60)

# 检查环境变量
langsmith_enabled = os.getenv("LANGCHAIN_TRACING_V2")
langsmith_key = os.getenv("LANGCHAIN_API_KEY")
langsmith_project = os.getenv("LANGCHAIN_PROJECT")

print(f"\n1. LANGCHAIN_TRACING_V2: {langsmith_enabled}")
print(f"2. LANGCHAIN_API_KEY: {langsmith_key[:30] if langsmith_key else 'None'}...")
print(f"3. LANGCHAIN_PROJECT: {langsmith_project}")

if langsmith_enabled == "true" and langsmith_key:
    print("\n" + "=" * 60)
    print("[SUCCESS] LangSmith配置正确！")
    print("=" * 60)

    print("\n下一步:")
    print("1. 运行任何使用LangChain的代码")
    print("2. 访问 https://smith.langchain.com/")
    print(f"3. 在项目 '{langsmith_project}' 中查看Trace")

    print("\n" + "=" * 60)
    print("面试话术:")
    print("=" * 60)
    print("\n你可以说:")
    print('"我的项目集成了LangSmith。')
    print('只需要3行配置（展示.env文件）：')
    print('  LANGCHAIN_TRACING_V2=true')
    print('  LANGCHAIN_API_KEY=...')
    print('  LANGCHAIN_PROJECT=travel-agent-demo')
    print('')
    print('之后所有LangChain调用都会自动追踪到LangSmith。')
    print('我能看到：')
    print('  - 完整的调用链（树状结构）')
    print('  - 每个步骤的输入输出')
    print('  - 耗时统计和Token使用量')
    print('')
    print('这是Spring AI完全没有的功能。')
    print('没有可观测性，AI应用就是黑盒。"')

else:
    print("\n[FAIL] LangSmith配置不完整")
    print("\n请检查.env文件是否包含:")
    print("  LANGCHAIN_TRACING_V2=true")
    print("  LANGCHAIN_API_KEY=your_key")
    print("  LANGCHAIN_PROJECT=your_project")

print("\n" + "=" * 60)
