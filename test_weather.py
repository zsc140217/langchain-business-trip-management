#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试天气查询工具"""
import requests
import json

url = "http://localhost:8001/api/unified/chat"
data = {
    "query": "北京天气",
    "user_id": "test_user"
}

print("发送请求:")
print(json.dumps(data, ensure_ascii=False, indent=2))

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"\n状态码: {response.status_code}")
    print(f"\n响应内容:")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
except Exception as e:
    print(f"\n错误: {e}")
    if hasattr(e, 'response'):
        print(f"响应文本: {e.response.text}")
