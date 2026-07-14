"""
测试审批流程
"""
import requests
import json

# 测试1: 自动审批（金额 < 1000元）
print("=" * 80)
print("测试1: 自动审批（金额800元）")
print("=" * 80)

response1 = requests.post(
    "http://localhost:8001/api/unified/chat",
    json={
        "query": "我要报销去北京出差2天的费用800元",
        "user_id": "zhang_san"
    }
)

print(f"Status: {response1.status_code}")
print(f"Response: {json.dumps(response1.json(), ensure_ascii=False, indent=2)}")

print("\n" + "=" * 80)
print("测试2: 人工审批（金额2500元）")
print("=" * 80)

# 测试2: 人工审批（金额 >= 1000元）
response2 = requests.post(
    "http://localhost:8001/api/unified/chat",
    json={
        "query": "我要报销去上海出差5天的费用2500元",
        "user_id": "li_si"
    }
)

print(f"Status: {response2.status_code}")
print(f"Response: {json.dumps(response2.json(), ensure_ascii=False, indent=2)}")
