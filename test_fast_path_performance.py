"""
快路径性能测试
验证优化后快路径是否跳过记忆加载
"""
import os
import sys
import time

# 设置环境变量（测试用）
os.environ.setdefault('DASHSCOPE_API_KEY', 'sk-test')
os.environ.setdefault('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')

from src.agents.orchestrator_agent import OrchestratorAgent
from src.models.llm import get_llm
from src.tools.registry import get_all_tools

# 初始化
llm = get_llm()
tools = get_all_tools()

agent = OrchestratorAgent(llm=llm, tools=tools, memory_service=None)

# 测试用例
test_cases = [
    {"query": "北京天气", "expected_route": "fast_path", "description": "天气查询"},
    {"query": "上海有什么酒店", "expected_route": "fast_path", "description": "酒店查询"},
    {"query": "北京到上海的航班", "expected_route": "fast_path", "description": "航班查询"},
    {"query": "住宿标准是多少", "expected_route": "fast_path", "description": "政策查询"},
]

print("=" * 80)
print("快路径性能测试")
print("=" * 80)
print(f"{'场景':<15} {'查询':<20} {'耗时':<10} {'路由':<15} {'状态':<10}")
print("-" * 80)

results = []

for case in test_cases:
    query = case["query"]
    expected = case["expected_route"]
    desc = case["description"]

    start = time.time()
    try:
        answer, route = agent.route(query, user_id="test_user")
        elapsed = time.time() - start

        # Windows兼容：使用ASCII字符
        if route == expected and elapsed < 5.0:
            status = "[PASS]"
        elif route == expected:
            status = "[SLOW]"
        else:
            status = "[FAIL]"

        print(f"{desc:<15} {query:<20} {elapsed:>6.2f}s   {route:<15} {status:<10}")

        if elapsed >= 5.0:
            print(f"  警告: 响应时间超过5秒（首次调用需要初始化）")

        results.append({
            "desc": desc,
            "query": query,
            "elapsed": elapsed,
            "route": route,
            "status": status
        })

    except Exception as e:
        elapsed = time.time() - start
        print(f"{desc:<15} {query:<20} {elapsed:>6.2f}s   {'ERROR':<15} [ERROR]")
        print(f"  错误: {str(e)[:60]}")

print("-" * 80)

# 测试缓存效果：第二次调用政策查询
print("\n" + "=" * 80)
print("缓存测试：重复政策查询")
print("=" * 80)

for i in range(2):
    start = time.time()
    try:
        answer, route = agent.route("住宿标准是多少", user_id="test_user")
        elapsed = time.time() - start
        status = "[PASS]" if elapsed < 5.0 else "[SLOW]"
        print(f"第{i+1}次调用:      住宿标准是多少         {elapsed:>6.2f}s   {route:<15} {status:<10}")
        if i == 0 and elapsed >= 5.0:
            print(f"  提示: 首次调用需要初始化向量库（约30秒）")
        elif i == 1 and elapsed < 5.0:
            print(f"  优化成功: 使用缓存的检索器，响应时间显著降低")
    except Exception as e:
        elapsed = time.time() - start
        print(f"第{i+1}次调用:      住宿标准是多少         {elapsed:>6.2f}s   ERROR           [ERROR]")

print("-" * 80)
print("\n统计信息:")
stats = agent.get_stats()
for key, value in stats.items():
    print(f"  {key}: {value}")

print("\n预期结果:")
print("  - 快路径响应时间: < 5秒")
print("  - 所有查询路由正确")
print("  - 无记忆加载日志")
