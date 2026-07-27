#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统完整链路测试脚本
测试所有业务域和通道
"""
import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

# 测试用例定义
test_cases = [
    # 测试组 A: 快路径 - 单工具调用
    {
        "group": "A1",
        "name": "天气查询",
        "query": "北京今天天气怎么样？",
        "expected_route": "qa_domain",
        "expected_keywords": ["天气", "北京"],
        "timeout": 60
    },
    {
        "group": "A2",
        "name": "酒店查询",
        "query": "上海有什么酒店推荐？",
        "expected_route": "qa_domain",
        "expected_keywords": ["酒店", "上海"],
        "timeout": 60
    },
    {
        "group": "A3",
        "name": "航班查询",
        "query": "查一下北京到上海的航班",
        "expected_route": "qa_domain",
        "expected_keywords": ["航班", "北京"],
        "timeout": 60
    },
    {
        "group": "A4",
        "name": "政策查询",
        "query": "北京的住宿标准是多少？",
        "expected_route": "qa_domain",
        "expected_keywords": ["住宿", "标准"],
        "timeout": 60
    },
    # 测试组 B: 审批域
    {
        "group": "B1",
        "name": "自动审批",
        "query": "我要报销去北京出差的费用，住了2天，花了800元",
        "expected_route": "approval_domain",
        "expected_keywords": ["报销", "800"],
        "timeout": 60
    },
    {
        "group": "B2",
        "name": "人工审批",
        "query": "我要报销去深圳出差5天的费用，总共花了3500元",
        "expected_route": "approval_domain",
        "expected_keywords": ["申请", "3500"],
        "timeout": 60
    },
    {
        "group": "B3",
        "name": "审批状态查询",
        "query": "我的审批进度怎么样了？",
        "expected_route": "approval_domain",
        "expected_keywords": ["审批"],
        "timeout": 60
    },
    # 测试组 C: 复杂通道
    {
        "group": "C1",
        "name": "多步骤任务",
        "query": "去杭州出差3天需要多少钱？",
        "expected_route": "qa_domain",
        "expected_keywords": ["杭州", "费用"],
        "timeout": 60
    },
]

def run_test(test_case):
    """执行单个测试用例"""
    print(f"\n{'='*70}")
    print(f"🧪 测试 [{test_case['group']}]: {test_case['name']}")
    print(f"📝 输入: {test_case['query']}")
    print(f"⏱️  超时设置: {test_case['timeout']}秒")

    start_time = time.time()

    try:
        response = requests.post(
            f"{BASE_URL}/api/unified/chat",
            json={
                "query": test_case['query'],
                "user_id": "test_user_123",
                "conversation_id": f"test_conv_{test_case['group']}"
            },
            timeout=test_case['timeout']
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            answer = result.get('answer', '')
            route = result.get('route', 'N/A')

            print(f"✅ 请求成功 | 耗时: {elapsed:.2f}秒")
            print(f"📍 路由: {route}")

            # 检查路由是否正确
            route_match = route == test_case['expected_route']
            if route_match:
                print(f"✅ 路由正确: {route}")
            else:
                print(f"⚠️  路由不符: 期望 {test_case['expected_route']}, 实际 {route}")

            # 检查关键词
            keyword_matches = []
            for keyword in test_case['expected_keywords']:
                if keyword in answer:
                    keyword_matches.append(f"✅ '{keyword}'")
                else:
                    keyword_matches.append(f"❌ '{keyword}'")

            print(f"🔍 关键词检查: {' | '.join(keyword_matches)}")

            # 显示响应内容（截取前200字符）
            print(f"💬 响应内容:")
            print(f"   {answer[:200]}{'...' if len(answer) > 200 else ''}")

            # 判断测试是否通过
            all_keywords_match = all(kw in answer for kw in test_case['expected_keywords'])
            test_passed = route_match and all_keywords_match

            return {
                "group": test_case['group'],
                "name": test_case['name'],
                "status": "PASS" if test_passed else "PARTIAL",
                "elapsed": elapsed,
                "route": route,
                "route_match": route_match,
                "keyword_match": all_keywords_match,
                "answer_preview": answer[:100]
            }

        else:
            print(f"❌ 请求失败 | 状态码: {response.status_code}")
            print(f"错误响应: {response.text[:200]}")

            return {
                "group": test_case['group'],
                "name": test_case['name'],
                "status": "FAIL",
                "elapsed": elapsed,
                "error": f"HTTP {response.status_code}"
            }

    except requests.Timeout:
        print(f"❌ 请求超时 (>{test_case['timeout']}秒)")
        return {
            "group": test_case['group'],
            "name": test_case['name'],
            "status": "TIMEOUT",
            "error": "请求超时"
        }
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return {
            "group": test_case['group'],
            "name": test_case['name'],
            "status": "ERROR",
            "error": str(e)
        }

def print_summary(results):
    """打印测试总结"""
    print(f"\n{'='*70}")
    print(f"📊 测试总结报告")
    print(f"{'='*70}")

    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'PASS')
    partial = sum(1 for r in results if r['status'] == 'PARTIAL')
    failed = sum(1 for r in results if r['status'] in ['FAIL', 'TIMEOUT', 'ERROR'])

    print(f"\n总测试数: {total}")
    print(f"✅ 通过: {passed}")
    print(f"⚠️  部分通过: {partial}")
    print(f"❌ 失败: {failed}")
    print(f"成功率: {(passed/total*100):.1f}%")

    print(f"\n详细结果:")
    print(f"{'组别':<6} {'测试名称':<20} {'状态':<10} {'耗时':<10} {'路由':<20}")
    print(f"{'-'*70}")

    for r in results:
        status_icon = {
            'PASS': '✅',
            'PARTIAL': '⚠️',
            'FAIL': '❌',
            'TIMEOUT': '⏱️',
            'ERROR': '💥'
        }.get(r['status'], '❓')

        elapsed_str = f"{r.get('elapsed', 0):.2f}s" if 'elapsed' in r else 'N/A'
        route_str = r.get('route', r.get('error', 'N/A'))[:18]

        print(f"{r['group']:<6} {r['name']:<20} {status_icon} {r['status']:<8} {elapsed_str:<10} {route_str:<20}")

    print(f"\n{'='*70}")

def main():
    """主测试流程"""
    import sys
    import io
    # Windows编码修复
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("="*70)
    print("🚀 系统完整链路测试")
    print("="*70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端地址: {BASE_URL}")
    print(f"测试用例数: {len(test_cases)}")

    # 健康检查
    print(f"\n{'='*70}")
    print("🏥 执行健康检查...")
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print("✅ 后端服务健康")
            print(f"   状态: {health_data.get('status')}")
            print(f"   组件: {health_data.get('components')}")
        else:
            print(f"❌ 健康检查失败: HTTP {health_response.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接后端服务: {e}")
        print(f"请确保后端服务在 {BASE_URL} 上运行")
        return

    # 运行测试
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n进度: {i}/{len(test_cases)}")
        result = run_test(test_case)
        results.append(result)

        # 测试间隔，避免请求过快
        if i < len(test_cases):
            time.sleep(2)

    # 打印总结
    print_summary(results)

    # 保存结果到文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"test_results_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total": len(results),
            "passed": sum(1 for r in results if r['status'] == 'PASS'),
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n📁 测试结果已保存到: {output_file}")

if __name__ == "__main__":
    main()
