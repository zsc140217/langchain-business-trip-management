import os
import sys
import io
import logging

# 修复 Windows 控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 配置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s'
)

# 设置环境变量
os.environ['FEISHU_APP_ID'] = 'cli_aa8759bff078dcbd'
os.environ['FEISHU_APP_SECRET'] = 'ralUiiVIL2ryfvDxeR9Bhd67DEiGPyGC'

# 导入模块
from src.harness.feishu_ws_client import FeishuWSClient
from src.reimbursement.reimbursement_service import ReimbursementService
from lark_oapi.event.callback.model.p2_card_action_trigger import P2CardActionTriggerResponse

# 真实报销审批处理器
class ReimbursementApprovalHandler:
    def __init__(self):
        self.service = ReimbursementService()
        print("[Handler] 报销服务初始化成功")

    def handle_card_action(self, event):
        try:
            action = event.event.action
            action_value = action.value if action else {}
            
            operation = action_value.get("operation")
            application_id = action_value.get("approval_id")
            
            operator = event.event.operator if hasattr(event.event, 'operator') else None
            approver_id = operator.operator_id.open_id if operator else "unknown"
            
            print(f"[Handler] 收到审批: {application_id} - {operation} by {approver_id}")
            
            if not operation or not application_id:
                return self._error_response("缺少必要参数")
            
            decision = "approved" if operation == "approve" else "rejected"
            result = self.service.approve(
                application_id=application_id,
                approver_id=approver_id,
                decision=decision,
                comment="",
                ip_address="127.0.0.1",
                user_agent="Feishu-Bot"
            )
            
            if result['success']:
                print(f"[Handler] 审批成功: {application_id} -> {decision}")
                return self._success_response(result, decision)
            else:
                print(f"[Handler] 审批失败: {result.get('message')}")
                return self._error_response(result.get('message', '审批失败'))
        
        except Exception as e:
            print(f"[Handler] 异常: {e}")
            import traceback
            traceback.print_exc()
            return self._error_response(f"处理失败: {str(e)}")
    
    def _success_response(self, result, decision):
        status_emoji = "✅" if decision == "approved" else "❌"
        status_text = "已通过" if decision == "approved" else "已拒绝"
        card_color = "green" if decision == "approved" else "red"
        
        updated_card = {
            "header": {
                "title": {"tag": "plain_text", "content": f"{status_emoji} 审批{status_text}"},
                "template": card_color
            },
            "elements": [{
                "tag": "markdown",
                "content": f"**报销单号**: {result.get('application_id', 'N/A')}\n**状态**: {status_text}"
            }]
        }
        
        return P2CardActionTriggerResponse({
            "toast": {"type": "success", "content": f"审批{status_text}"},
            "card": updated_card
        })
    
    def _error_response(self, error_message):
        return P2CardActionTriggerResponse({
            "toast": {"type": "error", "content": error_message}
        })

# 创建处理器
handler = ReimbursementApprovalHandler()

# 创建长连接客户端
ws_client = FeishuWSClient(callback_handler=handler)

print("=" * 80)
print("飞书WebSocket客户端（报销系统集成版）")
print("=" * 80)
print("功能:")
print("  ✅ 使用真实的 ReimbursementService")
print("  ✅ 更新数据库审批状态")
print("  ✅ 自动生成PDF（审批通过时）")
print("=" * 80)
print("保持此窗口运行，不要关闭！")
print("\n等待回调中...")
print("=" * 80)

# 启动（会阻塞主线程）
try:
    ws_client.start()
except KeyboardInterrupt:
    print("\n\n收到中断信号，退出...")
except Exception as e:
    print(f"\n\n错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    handler.service.close()
    print("已清理资源")
