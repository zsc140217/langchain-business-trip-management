# -*- coding: utf-8 -*-
"""测试智能提醒功能"""
import requests
import json

API_BASE = "http://localhost:8001"

print("="*60)
print("测试智能提醒功能")
print("="*60)

# 测试场景1：缺少金额
print("\n[场景1] 缺少金额")
response = requests.post(
    f"{API_BASE}/api/unified/chat",
    json={
        "query": "我要报销去北京出差3天",
        "user_id": "user_03d1a143-7ae3-4233-a1cf-d5fb56141e17"
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

# 测试场景2：完整信息
print("\n" + "="*60)
print("[场景2] 完整信息")
response = requests.post(
    f"{API_BASE}/api/unified/chat",
    json={
        "query": "我要报销去北京出差3天的费用800元",
        "user_id": "user_03d1a143-7ae3-4233-a1cf-d5fb56141e17"
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
