#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
飞书卡片集成测试脚本

测试流程：
1. 提交一个报销申请
2. 触发飞书卡片推送
3. 模拟审批回调
4. 验证状态更新
"""

import sys
import os
sys.path.insert(0, '.')

from src.reimbursement.reimbursement_service import ReimbursementService
from src.harness.feishu_client import FeishuClient

def test_submit_and_send_card():
    """测试提交报销并发送飞书卡片"""
    print("\n" + "="*60)
    print("测试：提交报销申请并推送飞书卡片")
    print("="*60)

    # 初始化服务
    webhook_key = os.getenv("FEISHU_WEBHOOK_KEY")
    if not webhook_key:
        print("❌ 错误：未配置 FEISHU_WEBHOOK_KEY")
        print("   请在 .env 文件中配置飞书 Webhook Key")
        return False

    print(f"✅ 飞书 Webhook Key: {webhook_key[:20]}...")

    # 创建服务实例
    reimbursement_service = ReimbursementService()

    # 准备测试数据
    test_invoices = [
        {
            "invoice_number": "TEST00001",
            "invoice_code": "TEST001",
            "invoice_date": "2026-07-25",
            "buyer_name": "测试公司",
            "seller_name": "北京XX酒店",
            "total_amount": 800.00,
            "tax_amount": 80.00,
            "amount_in_words": "捌佰元整",
            "verification_status": "verified"
        }
    ]

    trip_info = {
        "trip_destination": "北京",
        "trip_days": 2,
        "trip_purpose": "客户拜访",
        "remarks": "飞书卡片集成测试"
    }

    try:
        # 1. 创建报销申请
        print("\n[步骤1] 创建报销申请...")
        result = reimbursement_service.create_application(
            user_id="test_user_001",
            title="飞书卡片测试 - 北京出差报销",
            invoices=test_invoices,
            trip_info=trip_info
        )

        if not result['success']:
            print(f"❌ 创建失败: {result.get('message')}")
            return False

        application_id = result['application_id']
        print(f"✅ 报销申请创建成功: {application_id}")

        # 2. 提交申请（触发审批流程和飞书推送）
        print("\n[步骤2] 提交报销申请，触发飞书推送...")
        submit_result = reimbursement_service.submit_application(
            application_id=application_id,
            user_id="test_user_001",
            department="销售部"
        )

        if not submit_result['success']:
            print(f"❌ 提交失败: {submit_result.get('message')}")
            return False

        print(f"✅ 报销申请提交成功")
        print(f"   状态: {submit_result['status']}")
        print(f"   审批人数: {len(submit_result.get('approvers', []))}")

        if submit_result.get('approvers'):
            print(f"   审批人: {submit_result['approvers'][0].get('user_name', 'N/A')}")

        print("\n" + "="*60)
        print("🎉 测试完成！")
        print("="*60)
        print("\n请检查飞书群聊，应该收到一张审批卡片：")
        print("  📋 标题：待审批：出差报销申请")
        print("  🔵 颜色：橙色")
        print("  📝 内容：申请人、目的地、天数、金额")
        print("  🔘 按钮：✅ 通过 / ❌ 拒绝")
        print("\n点击按钮后，回调地址应配置为：")
        print("  http://your-server:8001/api/reimbursement/feishu/card/callback")
        print("\n⚠️  注意：如果本地测试，需要使用 ngrok 等工具将本地端口映射到公网")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        reimbursement_service.close()


def test_direct_card_send():
    """直接测试发送飞书卡片（不走完整流程）"""
    print("\n" + "="*60)
    print("测试：直接发送飞书审批卡片")
    print("="*60)

    webhook_key = os.getenv("FEISHU_WEBHOOK_KEY")
    if not webhook_key:
        print("❌ 错误：未配置 FEISHU_WEBHOOK_KEY")
        return False

    feishu_client = FeishuClient(webhook_key=webhook_key)

    try:
        result = feishu_client.send_approval_card(
            approval_id="TEST_APP_001",
            user_id="test_user_001",
            applicant="张三",
            destination="北京",
            days=2,
            amount=800.00
        )

        if result.get('StatusCode') == 0:
            print("✅ 飞书卡片发送成功！")
            print("   请在飞书群聊中查看")
            return True
        else:
            print(f"❌ 发送失败: {result}")
            return False

    except Exception as e:
        print(f"❌ 发送异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n飞书卡片集成测试")
    print("="*60)
    print("\n选择测试模式：")
    print("  1. 完整流程测试（创建报销 → 提交 → 发送卡片）")
    print("  2. 快速测试（仅发送测试卡片）")

    choice = input("\n请输入选项（1或2，默认2）: ").strip() or "2"

    if choice == "1":
        success = test_submit_and_send_card()
    else:
        success = test_direct_card_send()

    sys.exit(0 if success else 1)
