"""
审批状态查询工具

查询用户的报销审批进度和状态
"""
from src.tools.base_tool import BaseTool
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CheckApprovalStatusTool(BaseTool):
    """
    审批状态查询工具

    查询用户提交的报销申请当前的审批状态和进度
    """

    name: str = "check_approval_status"
    description: str = """查询报销审批的当前状态和进度。

适用场景：
- 用户询问"我的审批进度怎么样了"
- 查询某个报销申请的审批结果
- 了解审批单据的当前处理人
- 查看审批历史记录

输入参数：
- user_id: 用户ID（字符串）
- approval_id: 审批单号（可选，不填则返回所有待审批单据）

返回信息：
- 审批状态（pending/approved/rejected）
- 申请时间和审批时间
- 当前处理人
- 审批意见
- 申请详情（目的地、金额、天数等）

示例：
- check_approval_status("user123") -> 返回该用户所有待审批单据
- check_approval_status("user123", "APV20240711001") -> 返回指定单据状态
"""

    cache_enabled: bool = False  # 审批状态实时变化，不缓存

    def __init__(self, memory_service=None, **kwargs):
        """
        初始化审批状态查询工具

        Args:
            memory_service: MemoryService 实例（用于查询工作记忆）
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self._memory_service = memory_service
        self._initialized = False

    def _lazy_init(self):
        """延迟初始化记忆服务"""
        if self._initialized:
            return

        if self._memory_service is None:
            logger.info("[CheckApprovalStatusTool] 延迟初始化记忆服务")
            try:
                from src.memory.memory_service import MemoryService

                self._memory_service = MemoryService()
                logger.info("[CheckApprovalStatusTool] 记忆服务初始化完成")

            except Exception as e:
                logger.error(f"[CheckApprovalStatusTool] 记忆服务初始化失败: {e}")
                raise RuntimeError(f"记忆服务初始化失败: {e}")

        self._initialized = True

    def _run(self, user_id: str, approval_id: Optional[str] = None, **kwargs) -> str:
        """
        查询审批状态

        Args:
            user_id: 用户ID
            approval_id: 审批单号（可选）
            **kwargs: 其他参数

        Returns:
            审批状态信息文本
        """
        # 延迟初始化
        self._lazy_init()

        if not user_id or not user_id.strip():
            raise ValueError("用户ID不能为空")

        logger.info(f"[CheckApprovalStatusTool] 查询用户 {user_id} 的审批状态")

        try:
            # 从工作记忆中查询审批状态
            if approval_id:
                # 查询指定审批单
                status = self._get_approval_by_id(user_id, approval_id)
            else:
                # 查询所有待审批单据
                status = self._get_all_approvals(user_id)

            if not status:
                return f"未找到用户 {user_id} 的审批记录。"

            return self._format_status(status)

        except Exception as e:
            logger.error(f"[CheckApprovalStatusTool] 查询审批状态失败: {e}")
            raise RuntimeError(f"查询审批状态失败: {e}")

    def _get_approval_by_id(self, user_id: str, approval_id: str) -> Optional[Dict[str, Any]]:
        """
        查询指定审批单

        Args:
            user_id: 用户ID
            approval_id: 审批单号

        Returns:
            审批状态字典，如果不存在返回 None
        """
        # 从工作记忆中获取审批状态
        working_memory = self._memory_service.working_memory_manager.get_or_create(user_id)
        approval = working_memory.get_approval(approval_id)
        return approval

    def _get_all_approvals(self, user_id: str) -> Dict[str, Any]:
        """
        查询用户所有审批单

        Args:
            user_id: 用户ID

        Returns:
            审批状态字典 {approval_id: {...}}
        """
        # 从工作记忆中获取所有审批记录
        working_memory = self._memory_service.working_memory_manager.get_or_create(user_id)
        approvals = working_memory.get_all_approvals()
        return approvals

    def _format_status(self, status: Dict[str, Any]) -> str:
        """
        格式化审批状态信息

        Args:
            status: 审批状态字典或字典的字典

        Returns:
            格式化的文本
        """
        # 如果是多个审批单
        if all(isinstance(v, dict) for v in status.values()):
            result_parts = []
            for approval_id, details in status.items():
                result_parts.append(self._format_single_approval(approval_id, details))

            if not result_parts:
                return "暂无待审批的单据。"

            return "\n\n".join(result_parts)

        # 如果是单个审批单
        else:
            approval_id = status.get("approval_id", "未知")
            return self._format_single_approval(approval_id, status)

    def _format_single_approval(self, approval_id: str, details: Dict[str, Any]) -> str:
        """
        格式化单个审批单信息

        Args:
            approval_id: 审批单号
            details: 审批详情

        Returns:
            格式化的文本
        """
        status_map = {
            "pending": "⏳ 待审批",
            "approved": "[OK] 已通过",
            "rejected": "[ERROR] 已拒绝",
            "cancelled": "🚫 已取消",
        }

        status = details.get("status", "unknown")
        status_text = status_map.get(status, f"未知状态({status})")

        # 基本信息
        destination = details.get("destination", "未知")
        amount = details.get("amount", 0)
        days = details.get("days", 0)
        submit_time = details.get("submit_time", "未知")

        result = f"【审批单号】{approval_id}\n"
        result += f"【状态】{status_text}\n"
        result += f"【目的地】{destination} | 【天数】{days}天 | 【金额】¥{amount}\n"
        result += f"【提交时间】{submit_time}\n"

        # 审批信息
        if status in ["approved", "rejected"]:
            approver = details.get("approver", "未知")
            approval_time = details.get("approval_time", "未知")
            comment = details.get("comment", "")

            result += f"【审批人】{approver}\n"
            result += f"【审批时间】{approval_time}\n"
            if comment:
                result += f"【审批意见】{comment}\n"

        elif status == "pending":
            approver = details.get("approver", "待分配")
            result += f"【当前处理人】{approver}\n"
            result += "【提示】请耐心等待审批人处理\n"

        return result


# 创建全局单例（延迟初始化）
_check_approval_tool_instance: Optional[CheckApprovalStatusTool] = None


def get_check_approval_status_tool(memory_service=None) -> CheckApprovalStatusTool:
    """
    获取审批状态查询工具单例

    Args:
        memory_service: 可选的 MemoryService 实例

    Returns:
        CheckApprovalStatusTool 实例
    """
    global _check_approval_tool_instance

    if _check_approval_tool_instance is None:
        _check_approval_tool_instance = CheckApprovalStatusTool(
            memory_service=memory_service
        )

    return _check_approval_tool_instance
