#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试聊天 API - 诊断前端调用失败问题
"""
import requests
import json
import os
import sys
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 加载环境变量
from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

API_BASE = "http://localhost:8001"

def test_login():
    """测试登录接口"""
    print("=" * 60)
    print("🔐 测试登录接口...")
    print("=" * 60)

    response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"username": "employee", "password": "test123456"}
    )

    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"\n✅ 登录成功，获取 token: {token[:20]}...")
        return token
    else:
        print(f"\n❌ 登录失败")
        return None


def test_chat_api(token: str, query: str):
    """测试聊天接口"""
    print("\n" + "=" * 60)
    print(f"💬 测试聊天接口: {query}")
    print("=" * 60)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "query": query,
        "user_id": "employee"
    }

    print(f"\n请求 URL: {API_BASE}/api/unified/chat")
    print(f"请求头: {json.dumps(headers, indent=2)}")
    print(f"请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    try:
        response = requests.post(
            f"{API_BASE}/api/unified/chat",
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"\n状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 请求成功")
            print(f"回答: {result['answer']}")
            print(f"路由: {result.get('route', 'N/A')}")
        else:
            print(f"\n❌ 请求失败")
            print(f"响应: {response.text}")

    except requests.exceptions.Timeout:
        print(f"\n⏱️ 请求超时（30秒）")
    except requests.exceptions.ConnectionError:
        print(f"\n🔌 连接失败 - 后端服务未启动？")
    except Exception as e:
        print(f"\n❌ 错误: {e}")


def test_health():
    """测试健康检查接口"""
    print("=" * 60)
    print("🏥 测试健康检查接口...")
    print("=" * 60)

    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")


if __name__ == "__main__":
    print("\n🚀 开始 API 测试...\n")

    # 1. 健康检查
    test_health()

    # 2. 登录
    token = test_login()

    if not token:
        print("\n⚠️ 登录失败，无法继续测试")
        exit(1)

    # 3. 测试不同类型的查询
    test_queries = [
        "内江的天气",
        "北京住宿标准是多少",
        "你好",
    ]

    for query in test_queries:
        test_chat_api(token, query)
        print("\n" + "-" * 60)

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    print("\n💡 提示：")
    print("1. 如果测试成功，问题可能在前端")
    print("2. 查看后端终端日志，看看是否有错误")
    print("3. 使用浏览器 F12 Network 查看前端请求详情")
