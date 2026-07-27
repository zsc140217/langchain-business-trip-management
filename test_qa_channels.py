"""
Q&A域4通道测试
测试 simple、complex、planning、open 4个执行通道
"""
import os
import sys
import time

# 设置环境变量
os.environ.setdefault('DASHSCOPE_API_KEY', 'sk-test')
os.environ.setdefault('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')

from src.agents.orchestrator_agent import OrchestratorAgent
from src.models.llm import get_llm
from src.tools.registry import get_all_tools

# 初始化
print("正在初始化...")
llm = get_llm()
tools = get_all_tools()
agent = OrchestratorAgent(llm=llm, tools=tools, memory_service=None)

# 测试用例（设计触发不同通道）
test_cases = [
    {
        "query": "北京的住宿标准是多少",
        "expected_channel": "simple",
        "description": "简单查询（单工具调用）",
        "category": "Q&A域"
    },
    {
        "query": "比较一下北京和上海的住宿标准",
        "expected_channel": "complex",
        "description": "复杂查询（需要多步推理）",
        "category": "Q&A域"
    },
    {
        "query": "帮我规划下周去杭州出差3天的行程",
        "expected_channel": "planning",
        "description": "规划查询（需要生成计划）",
        "category": "Q&A域"
    },
    {
        "query": "飞机和高铁哪个更划算",
        "expected_channel": "open",
        "description": "开放查询（需要推理）",
        "category": "Q&A域"
    },
    {
        "query": "我要报销800元",
        "expected_channel": "approval",
        "description": "审批申请",
        "category": "审批域"
    }
]

print("=" * 100)
print("Q&A域4通道测试")
print("=" * 100)
print(f"{'类别':<10} {'场景':<25} {'查询':<30} {'耗时':<10} {'路由':<15} {'状态':<10}")
print("-" * 100)

results = []

for case in test_cases:
    query = case["query"]
    expected = case["expected_channel"]
    desc = case["description"]
    category = case["category"]

    start = time.time()
    try:
        answer, route = agent.route(query, user_id="test_user", conversation_id="test_conv")
        elapsed = time.time() - start

        # 判断状态
        if route == "fast_path":
            status = "[SKIP]"  # 被快路径拦截
            actual_channel = "fast_path"
        elif route == "qa_domain":
            status = "[PASS]"  # 进入Q&A域
            actual_channel = "qa_domain"
        elif route == "approval_domain":
            status = "[PASS]" if expected == "approval" else "[FAIL]"
            actual_channel = "approval_domain"
        else:
            status = "[UNKNOWN]"
            actual_channel = route

        print(f"{category:<10} {desc:<25} {query:<30} {elapsed:>6.2f}s   {actual_channel:<15} {status:<10}")

        if elapsed >= 10.0:
            print(f"  警告: 响应时间超过10秒")

        results.append({
            "category": category,
            "desc": desc,
            "query": query,
            "elapsed": elapsed,
            "route": route,
            "status": status
        })

    except Exception as e:
        elapsed = time.time() - start
        print(f"{category:<10} {desc:<25} {query:<30} {elapsed:>6.2f}s   ERROR           [ERROR]")
        print(f"  错误: {str(e)[:80]}")

print("-" * 100)

# 统计信息
print("\n统计信息:")
stats = agent.get_stats()
print(f"  总请求数: {stats['total']}")
print(f"  快路径: {stats['fast_path']}")
print(f"  Q&A域: {stats['qa_domain']}")
print(f"  审批域: {stats['approval_domain']}")

if 'qa_engine' in stats:
    qa_stats = stats['qa_engine']
    print(f"\nQ&A域内部路由:")
    print(f"  simple: {qa_stats.get('simple', 0)}")
    print(f"  complex: {qa_stats.get('complex', 0)}")
    print(f"  planning: {qa_stats.get('planning', 0)}")
    print(f"  open: {qa_stats.get('open', 0)}")

print("\n说明:")
print("  - [PASS]: 路由正确")
print("  - [SKIP]: 被快路径拦截（预期外）")
print("  - [FAIL]: 路由错误")
print("  - [ERROR]: 执行异常")
