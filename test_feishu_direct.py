"""
直接测试飞书客户端 - 验证真实接入
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 测试飞书客户端
from src.harness.feishu_client import FeishuClient

webhook_key = os.getenv("FEISHU_WEBHOOK_KEY")

if not webhook_key:
    print("[ERROR] FEISHU_WEBHOOK_KEY not configured in .env")
    exit(1)

print(f"[OK] FEISHU_WEBHOOK_KEY found: {webhook_key[:20]}...")

# 创建飞书客户端
client = FeishuClient(webhook_key=webhook_key)
print("[OK] FeishuClient created")

# 发送测试消息
print("\n[TEST] Sending test message to Feishu...")
result = client.send_card_message(
    title="[TEST] Feishu Integration Verification",
    content="""**This is a test message from the unified RAG-Agent architecture v2.0**

**Test Items:**
- Real FeishuClient (not mocked)
- ApprovalEngine integration
- OrchestratorAgent routing

**Status:** SUCCESS

If you see this card, Feishu integration is working correctly!""",
    card_type="success"
)

print(f"[RESULT] {result}")

if result.get("StatusCode") == 0:
    print("\n[SUCCESS] Feishu notification sent successfully!")
    print("[INFO] Check your Feishu group for the GREEN test card")
else:
    print(f"\n[FAILED] Feishu notification failed: {result}")
