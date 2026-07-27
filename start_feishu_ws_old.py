import os
import sys
import io
import logging

# 修复 Windows 控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s'
)

# 设置环境变量
os.environ['FEISHU_APP_ID'] = 'cli_aa8759bff078dcbd'
os.environ['FEISHU_APP_SECRET'] = 'ralUiiVIL2ryfvDxeR9Bhd67DEiGPyGC'
os.environ['FEISHU_VERIFICATION_TOKEN'] = 'c5KhjV6iJAI7RdPceU8eefyVq1wGTJhh'

# 导入模块
from src.harness.feishu_ws_client import FeishuWSClient
from src.harness.feishu_callback_handler import FeishuCallbackHandler

# 简单的Mock审批引擎（用于测试）
class MockApprovalEngine:
    def process_approval_result(self, approval_id, operation, approver_id):
        print(f"[Mock] 处理审批: {approval_id} - {operation} by {approver_id}")
        return {
            "status": "approved" if operation == "approve" else "rejected",
            "message": f"审批{operation}成功",
            "applicant": "test_user",
            "amount": 2500,
            "approval_id": approval_id
        }

# 创建回调处理器
handler = FeishuCallbackHandler(approval_engine=MockApprovalEngine())

# 创建长连接客户端
ws_client = FeishuWSClient(callback_handler=handler)

print("=" * 80)
print("飞书长连接客户端启动中...")
print("=" * 80)
print("修复说明：")
print("  ✅ 使用空字符串作为 EventDispatcherHandler 参数（符合飞书官方文档）")
print("  ✅ 增强了调试日志")
print("  ✅ 添加了实时 print 输出")
print("=" * 80)
print("保持此窗口运行，不要关闭！")
print("\n等待回调中...")
print("请在另一个终端运行: python send_card_to_chat.py")
print("然后在飞书中点击卡片按钮")
print("=" * 80)

# 启动（会阻塞主线程）
ws_client.start()
