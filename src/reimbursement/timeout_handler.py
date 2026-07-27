# -*- coding: utf-8 -*-
"""
审批超时处理器

职责：
1. 定时检查超时的审批节点
2. 分级超时处理（催办/升级/自动通过）
3. 发送超时通知
4. 记录超时日志
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.reimbursement.approval_chain_engine import ApprovalChainEngine
from src.reimbursement.feishu_approval_client import FeishuApprovalClient
from src.harness.feishu_client import FeishuClient

logger = logging.getLogger(__name__)


class TimeoutHandler:
    """
    审批超时处理器

    定时检查超时审批并自动处理
    """

    def __init__(
        self,
        db_connection_string: Optional[str] = None,
        approval_engine: Optional[ApprovalChainEngine] = None,
        feishu_approval: Optional[FeishuApprovalClient] = None,
        feishu_client: Optional[FeishuClient] = None,
        check_interval_hours: int = 1
    ):
        self.conn_str = db_connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://localhost:5432/business_trip"
        )
        self._conn = None

        # 依赖注入
        self.approval_engine = approval_engine or ApprovalChainEngine(db_connection_string)
        self.feishu_approval = feishu_approval or FeishuApprovalClient()
        self.feishu_client = feishu_client or FeishuClient()

        # 创建定时调度器
        self.scheduler = BackgroundScheduler()
        self.check_interval_hours = check_interval_hours

        # 超时策略配置
        self.timeout_config = {
            'reminder_hours': 24,      # 超时24小时发送催办
            'escalation_hours': 48,    # 超时48小时升级上级
            'auto_approve_hours': 72,  # 超时72小时自动处理
        }

        logger.info(f"[TimeoutHandler] 超时处理器初始化完成，检查间隔: {check_interval_hours}小时")

    def _get_connection(self):
        """获取数据库连接"""
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(self.conn_str)
                logger.info("[TimeoutHandler] 数据库连接已建立")
            except Exception as e:
                logger.error(f"[TimeoutHandler] 数据库连接失败: {e}")
                raise
        return self._conn

    def start(self):
        """启动超时检查任务"""
        try:
            # 添加定时任务
            self.scheduler.add_job(
                func=self.check_timeout,
                trigger=IntervalTrigger(hours=self.check_interval_hours),
                id='timeout_check',
                name='审批超时检查',
                replace_existing=True
            )

            # 启动调度器
            self.scheduler.start()

            logger.info("[TimeoutHandler] 超时检查任务已启动")

        except Exception as e:
            logger.error(f"[TimeoutHandler] 启动超时检查任务失败: {e}", exc_info=True)
            raise

    def stop(self):
        """停止超时检查任务"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("[TimeoutHandler] 超时检查任务已停止")
        except Exception as e:
            logger.error(f"[TimeoutHandler] 停止超时检查任务失败: {e}")

    def check_timeout(self):
        """
        检查超时审批节点

        定时执行的主要逻辑
        """
        logger.info("[TimeoutHandler] 开始执行超时检查")

        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 查询所有超时的待审批节点
                query = """
                    SELECT
                        a.id,
                        a.application_id,
                        a.approval_level,
                        a.approver_id,
                        a.approver_role,
                        a.deadline,
                        a.assigned_at,
                        app.title,
                        app.total_amount,
                        app.user_id,
                        u.full_name as approver_name
                    FROM reimbursement_approvals a
                    JOIN reimbursement_applications app ON a.application_id = app.application_id
                    LEFT JOIN users u ON a.approver_id = u.user_id
                    WHERE a.status = 'pending'
                      AND a.deadline < NOW()
                      AND a.is_timeout = FALSE
                    ORDER BY a.deadline ASC
                """

                cur.execute(query)
                timeout_nodes = cur.fetchall()

                logger.info(f"[TimeoutHandler] 发现 {len(timeout_nodes)} 个超时节点")

                # 处理每个超时节点
                for node in timeout_nodes:
                    self._handle_timeout_node(cur, dict(node))

                conn.commit()

                logger.info("[TimeoutHandler] 超时检查完成")

        except Exception as e:
            conn.rollback()
            logger.error(f"[TimeoutHandler] 超时检查异常: {e}", exc_info=True)

    def _handle_timeout_node(
        self,
        cursor,
        node: Dict[str, Any]
    ):
        """
        处理单个超时节点

        Args:
            cursor: 数据库游标
            node: 超时节点信息
        """
        try:
            node_id = node['id']
            application_id = node['application_id']
            approver_id = node['approver_id']
            approver_name = node['approver_name']
            deadline = node['deadline']

            # 计算超时时长（小时）
            now = datetime.now()
            overtime_hours = (now - deadline).total_seconds() / 3600

            logger.info(
                f"[TimeoutHandler] 处理超时节点: "
                f"application_id={application_id}, "
                f"approver={approver_name}, "
                f"超时={overtime_hours:.1f}小时"
            )

            # 根据超时时长分级处理
            if overtime_hours < self.timeout_config['reminder_hours']:
                # 第一阶段：发送催办通知
                self._send_reminder(node)
                action = 'reminder'

            elif overtime_hours < self.timeout_config['escalation_hours']:
                # 第二阶段：升级给上级
                self._escalate(cursor, node)
                action = 'escalate'

            elif overtime_hours >= self.timeout_config['auto_approve_hours']:
                # 第三阶段：自动通过或转派
                self._auto_approve_or_transfer(cursor, node)
                action = 'auto_approve'

            else:
                # 继续发送催办
                self._send_reminder(node)
                action = 'reminder'

            # 标记为超时
            cursor.execute(
                """
                UPDATE reimbursement_approvals
                SET is_timeout = TRUE,
                    timeout_action = %s
                WHERE id = %s
                """,
                (action, node_id)
            )

            # 插入超时通知记录
            self._insert_timeout_notification(
                cursor,
                application_id=application_id,
                approver_id=approver_id,
                notification_type=action,
                overtime_hours=overtime_hours
            )

        except Exception as e:
            logger.error(f"[TimeoutHandler] 处理超时节点失败: {e}", exc_info=True)

    def _send_reminder(self, node: Dict[str, Any]):
        """
        发送催办通知

        Args:
            node: 超时节点信息
        """
        try:
            application_id = node['application_id']
            approver_id = node['approver_id']
            approver_name = node['approver_name']
            title = node['title']
            total_amount = node['total_amount']

            message = f"""
⏰ **审批超时提醒**

报销单号: {application_id}
报销标题: {title}
报销金额: ¥{total_amount:.2f}
审批人: {approver_name}

您有一笔报销申请已超时，请尽快处理。
            """.strip()

            # 发送飞书通知
            self.feishu_client.send_text_message(
                user_id=approver_id,
                content=message
            )

            logger.info(
                f"[TimeoutHandler] 催办通知已发送: "
                f"application_id={application_id}, approver={approver_name}"
            )

        except Exception as e:
            logger.error(f"[TimeoutHandler] 发送催办通知失败: {e}")

    def _escalate(self, cursor, node: Dict[str, Any]):
        """
        升级给上级

        Args:
            cursor: 数据库游标
            node: 超时节点信息
        """
        try:
            application_id = node['application_id']
            approver_id = node['approver_id']
            approver_role = node['approver_role']

            # 查找上级领导
            escalated_to = self._find_superior(cursor, approver_id, approver_role)

            if not escalated_to:
                logger.warning(
                    f"[TimeoutHandler] 未找到上级领导，无法升级: "
                    f"approver={approver_id}"
                )
                # 降级为催办
                self._send_reminder(node)
                return

            # 更新审批节点，转派给上级
            cursor.execute(
                """
                UPDATE reimbursement_approvals
                SET approver_id = %s,
                    transferred_from = %s,
                    transfer_reason = '审批超时自动升级',
                    escalated_to = %s,
                    deadline = NOW() + INTERVAL '24 hours'
                WHERE application_id = %s
                  AND status = 'pending'
                  AND approval_level = %s
                """,
                (escalated_to, approver_id, escalated_to,
                 application_id, node['approval_level'])
            )

            # 发送通知给上级和原审批人
            self._send_escalation_notification(node, escalated_to)

            logger.info(
                f"[TimeoutHandler] 审批已升级: "
                f"application_id={application_id}, "
                f"from={approver_id}, to={escalated_to}"
            )

        except Exception as e:
            logger.error(f"[TimeoutHandler] 升级审批失败: {e}", exc_info=True)

    def _auto_approve_or_transfer(self, cursor, node: Dict[str, Any]):
        """
        自动通过或转派

        Args:
            cursor: 数据库游标
            node: 超时节点信息
        """
        try:
            application_id = node['application_id']

            # 查询审批链配置中的超时策略
            cursor.execute(
                """
                SELECT approval_chain
                FROM approval_chain_config
                WHERE id = (
                    SELECT id FROM approval_chain_config
                    WHERE min_amount <= %s
                      AND (max_amount IS NULL OR max_amount >= %s)
                      AND is_active = TRUE
                    ORDER BY priority DESC
                    LIMIT 1
                )
                """,
                (node['total_amount'], node['total_amount'])
            )

            result = cursor.fetchone()
            if not result:
                logger.warning(f"[TimeoutHandler] 未找到审批链配置")
                return

            approval_chain = result['approval_chain']

            # 查找当前节点配置
            current_level = node['approval_level']
            node_config = None
            for level_config in approval_chain:
                if level_config['level'] == current_level:
                    node_config = level_config
                    break

            if not node_config:
                logger.warning(f"[TimeoutHandler] 未找到节点配置")
                return

            auto_approve_on_timeout = node_config.get('auto_approve_on_timeout', False)

            if auto_approve_on_timeout:
                # 自动通过
                self.approval_engine.approve_node(
                    application_id=application_id,
                    approver_id=node['approver_id'],
                    decision='approve',
                    comment='审批超时自动通过'
                )

                logger.info(
                    f"[TimeoutHandler] 审批已自动通过: "
                    f"application_id={application_id}"
                )
            else:
                # 转派给其他人（简化处理：升级）
                self._escalate(cursor, node)

        except Exception as e:
            logger.error(f"[TimeoutHandler] 自动处理失败: {e}", exc_info=True)

    def _find_superior(
        self,
        cursor,
        user_id: str,
        role: str
    ) -> Optional[str]:
        """
        查找上级领导

        Args:
            cursor: 数据库游标
            user_id: 当前审批人ID
            role: 当前审批人角色

        Returns:
            上级领导user_id
        """
        try:
            # 简化逻辑：根据职级向上查找
            role_hierarchy = {
                'direct_manager': 'dept_manager',
                'dept_manager': 'vp',
                'vp': 'ceo',
                'finance': 'ceo'
            }

            superior_role = role_hierarchy.get(role)
            if not superior_role:
                return None

            # 查询对应角色的用户
            if superior_role == 'vp':
                cursor.execute(
                    """
                    SELECT user_id FROM users
                    WHERE position LIKE '%%副总%%'
                      AND is_active = TRUE
                    LIMIT 1
                    """
                )
            elif superior_role == 'ceo':
                cursor.execute(
                    """
                    SELECT user_id FROM users
                    WHERE position LIKE '%%总经理%%'
                      AND position NOT LIKE '%%副%%'
                      AND is_active = TRUE
                    LIMIT 1
                    """
                )
            else:
                return None

            result = cursor.fetchone()
            return result['user_id'] if result else None

        except Exception as e:
            logger.error(f"[TimeoutHandler] 查找上级领导失败: {e}")
            return None

    def _send_escalation_notification(
        self,
        node: Dict[str, Any],
        escalated_to: str
    ):
        """
        发送升级通知

        Args:
            node: 节点信息
            escalated_to: 升级目标user_id
        """
        try:
            application_id = node['application_id']
            title = node['title']
            total_amount = node['total_amount']

            # 通知新审批人
            message_to_new = f"""
📨 **审批升级通知**

报销单号: {application_id}
报销标题: {title}
报销金额: ¥{total_amount:.2f}

原审批人超时未处理，已升级至您，请尽快审批。
            """.strip()

            self.feishu_client.send_text_message(
                user_id=escalated_to,
                content=message_to_new
            )

            # 通知原审批人
            message_to_old = f"""
⚠️ **审批超时通知**

报销单号: {application_id}

您的审批超时未处理，已自动升级给上级领导。
            """.strip()

            self.feishu_client.send_text_message(
                user_id=node['approver_id'],
                content=message_to_old
            )

        except Exception as e:
            logger.error(f"[TimeoutHandler] 发送升级通知失败: {e}")

    def _insert_timeout_notification(
        self,
        cursor,
        application_id: str,
        approver_id: str,
        notification_type: str,
        overtime_hours: float
    ):
        """
        插入超时通知记录

        Args:
            cursor: 数据库游标
            application_id: 报销申请ID
            approver_id: 审批人ID
            notification_type: 通知类型
            overtime_hours: 超时时长
        """
        try:
            cursor.execute(
                """
                INSERT INTO timeout_notifications
                    (application_id, approver_id, notification_type,
                     notification_channel, sent_at, is_success)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (application_id, approver_id, notification_type,
                 'feishu', datetime.now(), True)
            )

        except Exception as e:
            logger.error(f"[TimeoutHandler] 插入超时通知记录失败: {e}")

    def close(self):
        """关闭资源"""
        self.stop()
        if self._conn:
            try:
                self._conn.close()
                logger.info("[TimeoutHandler] 数据库连接已关闭")
            except Exception:
                pass

    def __del__(self):
        self.close()
