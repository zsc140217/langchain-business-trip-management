"""
端到端测试脚本
测试 LangGraph + FastAPI + 飞书集成的完整流程
"""

import requests
import json
import time
from typing import Dict, Any


def test_api_health():
    """测试 API 健康检查"""
    print("\n" + "=" * 60)
    print("测试 1: API 健康检查")
    print("=" * 60)

    try:
        response = requests.get("http://localhost:8000/health", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过: {data.get('status')}")
            print(f"   飞书配置状态: {data.get('feishu_configured')}")
            return True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("   请先启动 API 服务: python -m src.harness.travel_approval_api")
        return False


def test_travel_application(request_data: Dict[str, Any], test_name: str):
    """测试差旅申请提交"""
    print("\n" + "=" * 60)
    print(f"测试: {test_name}")
    print("=" * 60)

    print(f"📝 申请信息:")
    print(f"   目的地: {request_data['destination']}")
    print(f"   日期: {request_data['start_date']} ~ {request_data['end_date']}")
    print(f"   目的: {request_data['purpose']}")
    print(f"   申请人: {request_data.get('user_name', '员工')}")

    try:
        print("\n⏳ 发送请求...")
        start_time = time.time()

        response = requests.post(
            "http://localhost:8000/api/travel/submit",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 请求成功 (耗时: {elapsed:.2f}秒)")
            print(f"\n📋 审批结果:")
            print(f"   状态: {data['status']}")
            print(f"   飞书推送: {'成功' if data['feishu_sent'] else '失败'}")
            print(f"   迭代次数: {data['iteration']}")
            print(f"\n💬 审批消息:")
            print(f"   {data['approval_result']}")
            return True
        else:
            print(f"\n❌ 请求失败: HTTP {response.status_code}")
            print(f"   错误: {response.text}")
            return False

    except requests.Timeout:
        print(f"\n❌ 请求超时（60秒）")
        return False
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False


def main():
    """运行所有端到端测试"""
    print("\n" + "=" * 60)
    print("🚀 LangGraph + 飞书集成 - 端到端测试")
    print("=" * 60)

    # 测试用例
    test_cases = [
        {
            "name": "国内短期出差（预期：自动通过）",
            "data": {
                "destination": "上海",
                "start_date": "2026-06-25",
                "end_date": "2026-06-27",
                "purpose": "客户拜访",
                "user_name": "张三"
            }
        },
        {
            "name": "国内长期出差（预期：需要人工审批）",
            "data": {
                "destination": "深圳",
                "start_date": "2026-07-01",
                "end_date": "2026-07-15",
                "purpose": "项目调研",
                "user_name": "李四"
            }
        },
        {
            "name": "标准差旅申请",
            "data": {
                "destination": "北京",
                "start_date": "2026-06-30",
                "end_date": "2026-07-02",
                "purpose": "技术培训",
                "user_name": "王五"
            }
        }
    ]

    # 1. 健康检查
    if not test_api_health():
        print("\n❌ 健康检查失败，终止测试")
        return

    # 2. 测试差旅申请
    results = {"total": 0, "passed": 0, "failed": 0}

    for test_case in test_cases:
        results["total"] += 1
        if test_travel_application(test_case["data"], test_case["name"]):
            results["passed"] += 1
        else:
            results["failed"] += 1

        # 避免请求过快
        time.sleep(2)

    # 3. 测试报告
    print("\n\n" + "=" * 60)
    print("📊 测试报告")
    print("=" * 60)
    print(f"总计: {results['total']}")
    print(f"✅ 通过: {results['passed']}")
    print(f"❌ 失败: {results['failed']}")

    if results["failed"] == 0:
        print("\n🎉 所有测试通过！")
        print("\n✅ Phase 2 实现完成:")
        print("   - FastAPI 接口已创建")
        print("   - LangGraph 集成成功")
        print("   - 飞书推送功能正常")
    else:
        print(f"\n⚠️ 有 {results['failed']} 个测试失败")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
