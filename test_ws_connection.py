import os
import sys
import threading
import time

# 设置环境变量
os.environ['FEISHU_APP_ID'] = 'cli_aa8759bff078dcbd'
os.environ['FEISHU_APP_SECRET'] = 'ralUiiVIL2ryfvDxeR9Bhd67DEiGPyGC'

# 导入模块
from src.harness.feishu_ws_client import FeishuWSClient
from src.harness.feishu_callback_handler import FeishuCallbackHandler

# Mock审批引擎
class MockApprovalEngine:
    def process_approval_result(self, approval_id, operation, approver_id):
        print(f"[Mock] Processing approval: {approval_id} - {operation} by {approver_id}")
        return {
            "status": "approved" if operation == "approve" else "rejected",
            "message": f"Approval {operation} successful",
            "applicant": "test_user",
            "amount": 2500,
            "approval_id": approval_id
        }

# 创建处理器和客户端
handler = FeishuCallbackHandler(approval_engine=MockApprovalEngine())
ws_client = FeishuWSClient(callback_handler=handler)

print("=" * 80)
print("Testing Feishu WebSocket Connection (10 seconds)")
print("=" * 80)

# 在单独线程中启动客户端
def start_client():
    try:
        ws_client.start()
    except Exception as e:
        print(f"[ERROR] Client failed: {e}")

client_thread = threading.Thread(target=start_client, daemon=True)
client_thread.start()

# 等待10秒
print("Waiting for connection...")
time.sleep(10)

print("\n" + "=" * 80)
if ws_client.is_running:
    print("[SUCCESS] WebSocket client is running!")
    print("Connection established successfully.")
else:
    print("[FAILED] WebSocket client failed to start.")

print("=" * 80)
print("\nTest completed. Press Ctrl+C to exit if needed.")
sys.exit(0)
