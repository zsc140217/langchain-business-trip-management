"""
最简单的LangSmith测试
只需要运行这个脚本，就能在LangSmith中看到Trace
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 60)
print("步骤1: 验证配置")
print("=" * 60)

# 验证配置
if os.getenv("LANGCHAIN_TRACING_V2") == "true":
    print("[OK] LangSmith追踪已启用")
else:
    print("[FAIL] 请在.env中设置 LANGCHAIN_TRACING_V2=true")
    exit(1)

if os.getenv("LANGCHAIN_API_KEY"):
    print(f"[OK] API Key: {os.getenv('LANGCHAIN_API_KEY')[:30]}...")
else:
    print("[FAIL] 请在.env中设置 LANGCHAIN_API_KEY")
    exit(1)

print(f"[OK] 项目名称: {os.getenv('LANGCHAIN_PROJECT')}")

print("\n" + "=" * 60)
print("步骤2: 发送测试数据到LangSmith")
print("=" * 60)

try:
    from langsmith import Client

    # 创建LangSmith客户端
    client = Client()

    print("\n正在发送测试数据...")

    # 创建一个简单的Run（这会出现在LangSmith中）
    run = client.create_run(
        name="test-run",
        run_type="chain",
        inputs={"question": "这是一个测试"},
        outputs={"answer": "测试成功！"},
        project_name=os.getenv("LANGCHAIN_PROJECT", "travel-agent-demo")
    )

    print(f"[OK] 测试数据已发送！")
    print(f"[OK] Run ID: {run.id}")

    print("\n" + "=" * 60)
    print("步骤3: 查看LangSmith界面")
    print("=" * 60)
    print("\n现在立即访问:")
    print("1. 打开: https://smith.langchain.com/")
    print("2. 点击左侧 'Projects'")
    print(f"3. 选择项目: {os.getenv('LANGCHAIN_PROJECT', 'travel-agent-demo')}")
    print("4. 你会看到刚才的 'test-run'")
    print("\n点击这个run，你会看到:")
    print("  - 输入: {'question': '这是一个测试'}")
    print("  - 输出: {'answer': '测试成功！'}")
    print("  - 时间戳")
    print("  - Run ID")

    print("\n" + "=" * 60)
    print("[SUCCESS] 完成！现在去LangSmith查看吧！")
    print("=" * 60)

except ImportError:
    print("\n[FAIL] 需要安装langsmith")
    print("运行: pip install langsmith")
except Exception as e:
    print(f"\n[FAIL] 出错: {e}")
    import traceback
    traceback.print_exc()
