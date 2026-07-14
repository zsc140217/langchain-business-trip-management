import sys
sys.path.insert(0, '.')
from src.harness.feishu_client import FeishuClient

client = FeishuClient(webhook_key='557e5b9b-e431-486f-a26c-2b0509b73437')

print("发送审批卡片...")
result = client.send_approval_card(
    approval_id='APV202607130999',
    user_id='test_user_final',
    applicant='Test User',
    destination='Beijing',
    days=3,
    amount=2500
)

if result.get('StatusCode') == 0:
    print("[SUCCESS] 卡片已发送到飞书群！")
    print("请在飞书中查看并点击按钮测试")
else:
    print(f"[FAILED] 发送失败: {result}")
