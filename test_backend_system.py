#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
后端系统完整测试脚本
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8002"

def print_section(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def test_health():
    """测试健康检查"""
    print_section("1. 健康检查")

    response = requests.get(f"{BASE_URL}/health")
    data = response.json()

    print(f"状态: {data['status']}")
    print(f"组件状态:")
    for component, status in data['components'].items():
        status_icon = "[OK]" if status else "[FAIL]"
        print(f"  {status_icon} {component}")

    return response.status_code == 200

def test_login():
    """测试用户登录"""
    print_section("2. 用户登录")

    # 测试3种用户
    users = [
        ("employee", "test123456", "普通员工"),
        ("executive", "test123456", "高管"),
        ("admin", "test123456", "管理员")
    ]

    tokens = {}

    for username, password, role in users:
        print(f"\n测试登录: {username} ({role})")
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": username, "password": password}
        )

        if response.status_code == 200:
            data = response.json()
            tokens[username] = data['access_token']
            user = data['user']
            print(f"  [OK] 登录成功")
            print(f"    - 姓名: {user['full_name']}")
            print(f"    - 部门: {user['department']}")
            print(f"    - 职位: {user['position']}")
            print(f"    - 高管: {'是' if user['is_executive'] else '否'}")
        else:
            print(f"  [FAIL] 登录失败: {response.text}")

    return tokens

def test_chat_qa(token):
    """测试Q&A域查询"""
    print_section("3. Q&A域测试")

    queries = [
        "北京的住宿标准是多少？",
        "高管的交通标准是什么？",
        "报销需要哪些材料？"
    ]

    for query in queries:
        print(f"\n查询: {query}")
        response = requests.post(
            f"{BASE_URL}/api/unified/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"user_id": "employee", "query": query}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"  路由: {data['route']}")
            print(f"  回答: {data['answer'][:100]}...")
        else:
            print(f"  [FAIL] 请求失败: {response.status_code}")

def test_approval_low_amount(token):
    """测试低金额报销（自动通过）"""
    print_section("4. 低金额报销测试（应自动通过）")

    query = "我去成都出差2天，花了500元，要报销"
    print(f"查询: {query}")

    response = requests.post(
        f"{BASE_URL}/api/unified/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": "employee", "query": query}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"  路由: {data['route']}")
        print(f"  结果: {data['answer']}")

        if "自动通过" in data['answer'] or "已通过" in data['answer']:
            print("  [OK] 自动审批成功")
            return True
        else:
            print("  [NOTE] 未检测到自动通过标识")
    else:
        print(f"  [FAIL] 请求失败: {response.status_code}")

    return False

def test_approval_high_amount(token):
    """测试高金额报销（需人工审批）"""
    print_section("5. 高金额报销测试（应需要审批）")

    query = "我去北京出差5天，花了5000元，要报销"
    print(f"查询: {query}")

    response = requests.post(
        f"{BASE_URL}/api/unified/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": "employee", "query": query}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"  路由: {data['route']}")
        print(f"  结果: {data['answer']}")

        if "待审批" in data['answer'] or "已提交" in data['answer']:
            print("  [OK] 提交审批成功")
            return True
        else:
            print("  [NOTE] 未检测到待审批标识")
    else:
        print(f"  [FAIL] 请求失败: {response.status_code}")

    return False

def test_cancel_approval(token):
    """测试取消审批"""
    print_section("6. 取消审批测试")

    query = "我要取消我的报销申请"
    print(f"查询: {query}")

    response = requests.post(
        f"{BASE_URL}/api/unified/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": "employee", "query": query}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"  路由: {data['route']}")
        print(f"  结果: {data['answer']}")
    else:
        print(f"  ✗ 请求失败: {response.status_code}")

def main():
    """主测试流程"""
    print("=" * 60)
    print(" 后端系统完整测试")
    print(f" 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}

    # 1. 健康检查
    results['health'] = test_health()

    # 2. 用户登录
    tokens = test_login()
    results['login'] = len(tokens) > 0

    if not tokens:
        print("\n[FAIL] 登录失败，终止测试")
        return

    employee_token = tokens.get('employee')

    if not employee_token:
        print("\n[FAIL] 未获取到员工token，终止测试")
        return

    # 3. Q&A域测试
    test_chat_qa(employee_token)

    # 4. 低金额报销
    results['low_amount'] = test_approval_low_amount(employee_token)

    # 5. 高金额报销
    results['high_amount'] = test_approval_high_amount(employee_token)

    # 6. 取消审批
    test_cancel_approval(employee_token)

    # 测试总结
    print_section("测试总结")
    total = len(results)
    passed = sum(1 for v in results.values() if v)

    print(f"\n总测试项: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"通过率: {passed/total*100:.1f}%")

    print("\n详细结果:")
    for test_name, result in results.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {test_name}")

    print("\n" + "=" * 60)
    if passed == total:
        print(" [SUCCESS] 所有测试通过！")
    else:
        print(f" [WARNING] {total - passed} 个测试失败")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FAIL] 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
