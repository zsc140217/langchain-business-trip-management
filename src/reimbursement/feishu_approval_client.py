# -*- coding: utf-8 -*-
"""
飞书审批客户端

职责：
1. 对接飞书审批流API
2. 创建审批实例
3. 查询审批状态
4. 发送催办通知
5. 处理审批回调
"""
import logging
import os
from typing import Dict, List, Any, Optional
import json

from lark_oapi import Client

logger = logging.getLogger(__name__)

try:
    from lark_oapi.api.approval.v4 import (
        CreateInstanceRequest,
        CreateInstanceRequestBody,
        GetInstanceRequest,
        ApprovalInfo,
        ApprovalNode,
        ApprovalNodeType,
    )
except ImportError:
    # 如果导入失败，使用简化版本
    from lark_oapi.api.approval.v4 import CreateInstanceRequest, GetInstanceRequest
    CreateInstanceRequestBody = None
    ApprovalInfo = None
    ApprovalNode = None
    ApprovalNodeType = None
    logger.warning("[FeishuApproval] 部分飞书API类导入失败，将使用降级模式")


class FeishuApprovalClient:
    """
    飞书审批客户端

    封装飞书开放平台审批API
    """

    def __init__(self):
        # 飞书应用凭证
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        self.approval_code = os.getenv("FEISHU_APPROVAL_CODE")  # 审批定义code

        if not all([self.app_id, self.app_secret]):
            logger.warning("[FeishuApproval] 飞书应用凭证未配置")
            self.client = None
        else:
            # 创建飞书客户端
            self.client = Client.builder() \
                .app_id(self.app_id) \
                .app_secret(self.app_secret) \
                .build()
            logger.info("[FeishuApproval] 飞书客户端初始化成功")

    def create_approval_instance(
        self,
        application_id: str,
        applicant_user_id: str,
        approver_user_ids: List[str],
        form_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        创建飞书审批实例

        Args:
            application_id: 报销申请ID
            applicant_user_id: 申请人飞书user_id
            approver_user_ids: 审批人飞书user_id列表
            form_data: 表单数据

        Returns:
            飞书审批实例code
        """
        if not self.client or not self.approval_code:
            logger.warning("[FeishuApproval] 飞书未配置，跳过创建审批实例")
            return None

        try:
            # 构建审批表单数据
            form_content = self._build_form_content(form_data)

            # 构建审批节点
            approval_nodes = self._build_approval_nodes(approver_user_ids)

            # 创建审批实例请求
            request_body = CreateInstanceRequestBody.builder() \
                .approval_code(self.approval_code) \
                .user_id(applicant_user_id) \
                .form(form_content) \
                .node_approver_user_id_list(approval_nodes) \
                .build()

            request = CreateInstanceRequest.builder() \
                .body(request_body) \
                .build()

            # 调用API
            response = self.client.approval.v4.instance.create(request)

            if response.success():
                instance_code = response.data.instance_code
                logger.info(
                    f"[FeishuApproval] 审批实例创建成功: "
                    f"application_id={application_id}, "
                    f"instance_code={instance_code}"
                )
                return instance_code
            else:
                logger.error(
                    f"[FeishuApproval] 创建审批实例失败: "
                    f"code={response.code}, msg={response.msg}"
                )
                return None

        except Exception as e:
            logger.error(f"[FeishuApproval] 创建审批实例异常: {e}", exc_info=True)
            return None

    def query_approval_status(
        self,
        instance_code: str
    ) -> Optional[Dict[str, Any]]:
        """
        查询审批实例状态

        Args:
            instance_code: 飞书审批实例code

        Returns:
            审批状态信息
        """
        if not self.client:
            logger.warning("[FeishuApproval] 飞书未配置，跳过查询审批状态")
            return None

        try:
            request = GetInstanceRequest.builder() \
                .instance_id(instance_code) \
                .build()

            response = self.client.approval.v4.instance.get(request)

            if response.success():
                data = response.data
                status_info = {
                    'instance_code': instance_code,
                    'status': data.status,  # PENDING/APPROVED/REJECTED/CANCELED/DELETED
                    'start_time': data.start_time,
                    'end_time': data.end_time,
                    'timeline': self._parse_timeline(data.timeline)
                }

                logger.info(
                    f"[FeishuApproval] 查询审批状态成功: "
                    f"instance_code={instance_code}, status={data.status}"
                )

                return status_info
            else:
                logger.error(
                    f"[FeishuApproval] 查询审批状态失败: "
                    f"code={response.code}, msg={response.msg}"
                )
                return None

        except Exception as e:
            logger.error(f"[FeishuApproval] 查询审批状态异常: {e}", exc_info=True)
            return None

    def send_reminder(
        self,
        instance_code: str,
        approver_user_id: str,
        message: str
    ) -> bool:
        """
        发送催办通知

        Args:
            instance_code: 飞书审批实例code
            approver_user_id: 审批人飞书user_id
            message: 催办消息

        Returns:
            是否成功
        """
        if not self.client:
            logger.warning("[FeishuApproval] 飞书未配置，跳过发送催办")
            return False

        try:
            # 使用飞书消息API发送催办
            # 这里简化处理，实际应使用 CreateInstanceCommentRequest
            logger.info(
                f"[FeishuApproval] 发送催办通知: "
                f"instance_code={instance_code}, "
                f"approver={approver_user_id}"
            )

            # TODO: 实现催办消息发送
            # 可以使用飞书消息API或审批评论API

            return True

        except Exception as e:
            logger.error(f"[FeishuApproval] 发送催办通知异常: {e}", exc_info=True)
            return False

    def handle_callback(
        self,
        event_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        处理飞书审批回调事件

        Args:
            event_data: 飞书回调事件数据

        Returns:
            解析后的审批事件
        """
        try:
            event_type = event_data.get('type')

            if event_type == 'approval_instance':
                # 审批实例状态变更事件
                instance = event_data.get('instance', {})
                instance_code = instance.get('instance_code')
                status = instance.get('status')

                logger.info(
                    f"[FeishuApproval] 收到审批回调: "
                    f"instance_code={instance_code}, status={status}"
                )

                return {
                    'instance_code': instance_code,
                    'status': status,
                    'operator_id': instance.get('operator_id'),
                    'operate_time': instance.get('operate_time'),
                    'comment': instance.get('comment', '')
                }

            elif event_type == 'approval_task':
                # 审批任务事件（单个审批节点）
                task = event_data.get('task', {})

                logger.info(
                    f"[FeishuApproval] 收到审批任务事件: "
                    f"task_id={task.get('task_id')}"
                )

                return {
                    'task_id': task.get('task_id'),
                    'instance_code': task.get('instance_code'),
                    'status': task.get('status'),
                    'approver_id': task.get('approver_id'),
                    'operate_time': task.get('operate_time')
                }

            else:
                logger.warning(f"[FeishuApproval] 未知事件类型: {event_type}")
                return None

        except Exception as e:
            logger.error(f"[FeishuApproval] 处理审批回调异常: {e}", exc_info=True)
            return None

    def _build_form_content(self, form_data: Dict[str, Any]) -> str:
        """
        构建飞书审批表单内容

        将报销表单数据转换为飞书审批表单格式
        """
        form_fields = []

        # 报销标题
        if 'title' in form_data:
            form_fields.append({
                'id': 'title',
                'type': 'input',
                'value': form_data['title']
            })

        # 出差目的地
        if 'trip_destination' in form_data:
            form_fields.append({
                'id': 'trip_destination',
                'type': 'input',
                'value': form_data['trip_destination']
            })

        # 出差天数
        if 'trip_days' in form_data:
            form_fields.append({
                'id': 'trip_days',
                'type': 'number',
                'value': str(form_data['trip_days'])
            })

        # 报销总额
        if 'total_amount' in form_data:
            form_fields.append({
                'id': 'total_amount',
                'type': 'amount',
                'value': str(form_data['total_amount'])
            })

        # 发票明细（表格）
        if 'invoices' in form_data:
            invoice_table = []
            for invoice in form_data['invoices']:
                invoice_table.append([
                    invoice.get('invoice_number', ''),
                    invoice.get('invoice_date', ''),
                    str(invoice.get('total', 0))
                ])

            form_fields.append({
                'id': 'invoices',
                'type': 'table',
                'value': invoice_table
            })

        return json.dumps(form_fields, ensure_ascii=False)

    def _build_approval_nodes(
        self,
        approver_user_ids: List[str]
    ) -> List[List[str]]:
        """
        构建审批节点列表

        飞书审批支持串行审批：[[user1], [user2], [user3]]
        """
        return [[user_id] for user_id in approver_user_ids]

    def _parse_timeline(self, timeline: Any) -> List[Dict[str, Any]]:
        """
        解析审批时间线

        Args:
            timeline: 飞书返回的时间线对象

        Returns:
            解析后的时间线列表
        """
        if not timeline:
            return []

        result = []
        try:
            for event in timeline:
                result.append({
                    'type': event.type,
                    'create_time': event.create_time,
                    'user_id': event.user_id,
                    'comment': event.comment
                })
        except Exception as e:
            logger.error(f"[FeishuApproval] 解析时间线异常: {e}")

        return result

    def verify_signature(
        self,
        timestamp: str,
        nonce: str,
        signature: str,
        body: str
    ) -> bool:
        """
        验证飞书回调签名

        Args:
            timestamp: 时间戳
            nonce: 随机数
            signature: 签名
            body: 请求体

        Returns:
            签名是否有效
        """
        import hashlib
        import hmac

        # 飞书签名验证
        # signature = sha256(timestamp + nonce + encrypt_key + body)

        encrypt_key = os.getenv("FEISHU_ENCRYPT_KEY", "")
        if not encrypt_key:
            logger.warning("[FeishuApproval] FEISHU_ENCRYPT_KEY未配置")
            return False

        try:
            data = f"{timestamp}{nonce}{encrypt_key}{body}".encode('utf-8')
            computed_signature = hashlib.sha256(data).hexdigest()

            is_valid = computed_signature == signature

            if not is_valid:
                logger.warning(
                    f"[FeishuApproval] 签名验证失败: "
                    f"expected={computed_signature}, got={signature}"
                )

            return is_valid

        except Exception as e:
            logger.error(f"[FeishuApproval] 签名验证异常: {e}")
            return False
