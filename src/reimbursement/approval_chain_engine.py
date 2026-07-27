# -*- coding: utf-8 -*-
"""
审批链引擎 - 基于内江嘉宏城建集团差旅管理办法

根据报销金额自动匹配审批流程，支持多级审批
符合真实企业审批制度
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import os

logger = logging.getLogger(__name__)


class ApprovalChainEngine:
    """
    审批链引擎

    基于内江嘉宏城建集团差旅管理办法第十七条：
    "员工报销差旅费时，须附：经部室、公司分管领导及总经理批准的出差审批表"

    审批流程：
    - 小额(<1000): 部门经理 → 完成
    - 中额(1000-5000): 部门经理 → 分管副总 → 完成
    - 大额(5000-20000): 部门经理 → 分管副总 → 财务总监 → 完成
    - 特大额(>20000): 部门经理 → 分管副总 → 财务总监 → 总经理
    """

    def __init__(self, db_connection_string: Optional[str] = None):
        self.conn_str = db_connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://localhost:5432/business_trip"
        )
        self._conn = None

    def _get_connection(self):
        """获取数据库连接"""
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(self.conn_str)
                logger.info("[ApprovalChain] 数据库连接已建立")
            except Exception as e:
                logger.error(f"[ApprovalChain] 数据库连接失败: {e}")
                raise
        return self._conn

    def match_approval_chain(
        self,
        amount: float,
        department: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        匹配审批链配置

        Args:
            amount: 报销金额
            department: 部门名称

        Returns:
            审批链配置字典
        """
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 优先匹配部门特定规则，然后全局规则
                query = """
                    SELECT id, rule_name, approval_chain, approval_mode,
                           min_amount, max_amount, priority
                    FROM approval_chain_config
                    WHERE is_active = TRUE
                      AND min_amount <= %s
                      AND (max_amount IS NULL OR max_amount >= %s)
                      AND (department = %s OR department IS NULL)
                    ORDER BY
                        CASE WHEN department IS NOT NULL THEN 1 ELSE 2 END,
                        priority DESC
                    LIMIT 1
                """

                cur.execute(query, (amount, amount, department))
                result = cur.fetchone()

                if result:
                    logger.info(
                        f"[ApprovalChain] 匹配审批链: {result['rule_name']} "
                        f"(金额: ¥{amount}, 部门: {department})"
                    )
                    return dict(result)
                else:
                    logger.warning(
                        f"[ApprovalChain] 未找到匹配的审批链 "
                        f"(金额: ¥{amount}, 部门: {department})"
                    )
                    return None

        except Exception as e:
            logger.error(f"[ApprovalChain] 匹配审批链失败: {e}", exc_info=True)
            raise

    def initialize_approval_nodes(
        self,
        application_id: str,
        approval_chain: List[Dict[str, Any]],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        初始化审批节点

        Args:
            application_id: 报销申请ID
            approval_chain: 审批链配置
            user_id: 申请人ID

        Returns:
            创建的审批节点列表
        """
        conn = self._get_connection()
        created_nodes = []

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for node_config in approval_chain:
                    level = node_config['level']
                    role = node_config['role']
                    timeout_hours = node_config.get('timeout_hours', 24)

                    # 解析审批人
                    approver_id = self._resolve_approver(user_id, role, cur)

                    if not approver_id:
                        logger.warning(
                            f"[ApprovalChain] 无法解析审批人: "
                            f"role={role}, user_id={user_id}"
                        )
                        continue

                    # 计算截止时间
                    deadline = datetime.now() + timedelta(hours=timeout_hours)

                    # 插入审批节点
                    insert_query = """
                        INSERT INTO reimbursement_approvals
                            (application_id, approval_level, approver_id,
                             approver_role, status, deadline, assigned_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, approver_id, approval_level, deadline
                    """

                    cur.execute(
                        insert_query,
                        (application_id, level, approver_id, role,
                         'pending', deadline, datetime.now())
                    )

                    node = cur.fetchone()
                    created_nodes.append(dict(node))

                    logger.info(
                        f"[ApprovalChain] 创建审批节点: "
                        f"level={level}, approver={approver_id}, "
                        f"deadline={deadline}"
                    )

                conn.commit()
                logger.info(
                    f"[ApprovalChain] 审批链初始化完成: "
                    f"application={application_id}, 节点数={len(created_nodes)}"
                )

                return created_nodes

        except Exception as e:
            conn.rollback()
            logger.error(f"[ApprovalChain] 初始化审批节点失败: {e}", exc_info=True)
            raise

    def _resolve_approver(
        self,
        user_id: str,
        role: str,
        cursor
    ) -> Optional[str]:
        """
        解析审批人ID

        基于组织架构的上下级关系（manager_id）：
        - direct_manager: 直属上级（通过manager_id查找）
        - dept_manager: 部门经理（同direct_manager）
        - vp: 分管副总（副总经理，position包含VP）
        - finance: 财务总监（CFO或财务部高管）
        - ceo: 总经理（CEO）

        Args:
            user_id: 申请人ID
            role: 审批角色
            cursor: 数据库游标

        Returns:
            审批人ID
        """
        try:
            if role in ['direct_manager', 'dept_manager']:
                # 通过manager_id查找直属上级
                query = """
                    SELECT u2.user_id, u2.full_name, u2.position
                    FROM users u1
                    JOIN users u2 ON u1.manager_id = u2.user_id
                    WHERE u1.user_id = %s
                      AND u2.is_active = TRUE
                """
                cursor.execute(query, (user_id,))
                result = cursor.fetchone()

                if result:
                    logger.info(
                        f"[ApprovalChain] 找到直属上级: "
                        f"{result['full_name']} ({result['position']})"
                    )
                    return result['user_id']
                else:
                    logger.warning(
                        f"[ApprovalChain] 用户 {user_id} 没有配置直属上级(manager_id)"
                    )
                    return None

            elif role == 'vp':
                # 查询分管副总（先尝试从申请人部门找VP，找不到则任意VP）
                # 第一步：获取申请人部门
                cursor.execute(
                    "SELECT department FROM users WHERE user_id = %s",
                    (user_id,)
                )
                user_dept = cursor.fetchone()
                dept = user_dept['department'] if user_dept else None

                # 第二步：优先查找同部门的VP
                if dept:
                    query = """
                        SELECT user_id, full_name, position
                        FROM users
                        WHERE department = %s
                          AND (position = 'VP' OR position LIKE '%%副总%%')
                          AND is_active = TRUE
                        LIMIT 1
                    """
                    cursor.execute(query, (dept,))
                    result = cursor.fetchone()

                    if result:
                        logger.info(
                            f"[ApprovalChain] 找到分管副总: "
                            f"{result['full_name']} ({result['position']})"
                        )
                        return result['user_id']

                # 第三步：降级查找任意VP
                query = """
                    SELECT user_id, full_name, position
                    FROM users
                    WHERE (position = 'VP' OR position LIKE '%%副总%%')
                      AND is_active = TRUE
                    LIMIT 1
                """
                cursor.execute(query)
                result = cursor.fetchone()

                if result:
                    logger.info(
                        f"[ApprovalChain] 找到副总: "
                        f"{result['full_name']} ({result['position']})"
                    )
                    return result['user_id']
                else:
                    logger.warning("[ApprovalChain] 未找到分管副总")
                    return None

            elif role == 'finance':
                # 查询财务总监（CFO或财务部高管）
                query = """
                    SELECT user_id, full_name, position
                    FROM users
                    WHERE (position = 'CFO'
                           OR (department = '财务部' AND position LIKE '%%总监%%')
                           OR (department = '财务部' AND position LIKE '%%经理%%'))
                      AND is_active = TRUE
                    ORDER BY
                        CASE
                            WHEN position = 'CFO' THEN 1
                            WHEN position LIKE '%%总监%%' THEN 2
                            ELSE 3
                        END
                    LIMIT 1
                """
                cursor.execute(query)
                result = cursor.fetchone()

                if result:
                    logger.info(
                        f"[ApprovalChain] 找到财务审批人: "
                        f"{result['full_name']} ({result['position']})"
                    )
                    return result['user_id']
                else:
                    logger.warning("[ApprovalChain] 未找到财务总监")
                    return None

            elif role == 'ceo':
                # 查询总经理（CEO）
                query = """
                    SELECT user_id, full_name, position
                    FROM users
                    WHERE (position = 'CEO' OR position LIKE '%%总经理%%')
                      AND position NOT LIKE '%%副%%'
                      AND is_active = TRUE
                    ORDER BY
                        CASE WHEN position = 'CEO' THEN 1 ELSE 2 END
                    LIMIT 1
                """
                cursor.execute(query)
                result = cursor.fetchone()

                if result:
                    logger.info(
                        f"[ApprovalChain] 找到总经理: "
                        f"{result['full_name']} ({result['position']})"
                    )
                    return result['user_id']
                else:
                    logger.warning("[ApprovalChain] 未找到总经理")
                    return None

            else:
                logger.warning(f"[ApprovalChain] 未知审批角色: {role}")
                return None

        except Exception as e:
            logger.error(f"[ApprovalChain] 解析审批人失败: {e}", exc_info=True)
            return None

    def get_current_approver(
        self,
        application_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取当前待审批节点

        Args:
            application_id: 报销申请ID

        Returns:
            当前审批人信息
        """
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT id, application_id, approval_level,
                           approver_id, approver_role, status, deadline
                    FROM reimbursement_approvals
                    WHERE application_id = %s
                      AND status = 'pending'
                    ORDER BY approval_level ASC
                    LIMIT 1
                """

                cur.execute(query, (application_id,))
                result = cur.fetchone()

                return dict(result) if result else None

        except Exception as e:
            logger.error(f"[ApprovalChain] 获取当前审批人失败: {e}")
            return None

    def approve_node(
        self,
        application_id: str,
        approver_id: str,
        decision: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        审批节点（通过/拒绝）

        Args:
            application_id: 报销申请ID
            approver_id: 审批人ID
            decision: 审批决策 (approve/reject)
            comment: 审批意见

        Returns:
            是否成功
        """
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                now = datetime.now()
                status = 'approved' if decision == 'approve' else 'rejected'

                update_query = """
                    UPDATE reimbursement_approvals
                    SET status = %s,
                        decision = %s,
                        comment = %s,
                        responded_at = %s,
                        duration_minutes = EXTRACT(EPOCH FROM (%s - assigned_at)) / 60
                    WHERE application_id = %s
                      AND approver_id = %s
                      AND status = 'pending'
                    RETURNING id, approval_level
                """

                cur.execute(
                    update_query,
                    (status, decision, comment, now, now,
                     application_id, approver_id)
                )

                result = cur.fetchone()

                if not result:
                    logger.warning(
                        f"[ApprovalChain] 未找到待审批节点: "
                        f"application={application_id}, approver={approver_id}"
                    )
                    return False

                conn.commit()

                logger.info(
                    f"[ApprovalChain] 审批完成: "
                    f"application={application_id}, "
                    f"level={result['approval_level']}, decision={decision}"
                )

                return True

        except Exception as e:
            conn.rollback()
            logger.error(f"[ApprovalChain] 审批失败: {e}", exc_info=True)
            return False

    def is_approval_completed(
        self,
        application_id: str
    ) -> tuple[bool, str]:
        """
        检查审批是否完成

        Args:
            application_id: 报销申请ID

        Returns:
            (是否完成, 最终状态)
            状态: 'approved'(全部通过) / 'rejected'(有拒绝) / 'approving'(审批中)
        """
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 检查是否有拒绝
                reject_query = """
                    SELECT COUNT(*) as count
                    FROM reimbursement_approvals
                    WHERE application_id = %s AND status = 'rejected'
                """
                cur.execute(reject_query, (application_id,))
                reject_count = cur.fetchone()['count']

                if reject_count > 0:
                    return (True, 'rejected')

                # 检查是否还有待审批
                pending_query = """
                    SELECT COUNT(*) as count
                    FROM reimbursement_approvals
                    WHERE application_id = %s AND status = 'pending'
                """
                cur.execute(pending_query, (application_id,))
                pending_count = cur.fetchone()['count']

                if pending_count == 0:
                    return (True, 'approved')
                else:
                    return (False, 'approving')

        except Exception as e:
            logger.error(f"[ApprovalChain] 检查审批状态失败: {e}")
            return (False, 'error')

    def get_approval_history(
        self,
        application_id: str
    ) -> List[Dict[str, Any]]:
        """
        获取审批历史记录

        Args:
            application_id: 报销申请ID

        Returns:
            审批历史列表
        """
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT
                        a.approval_level,
                        a.approver_id,
                        u.full_name as approver_name,
                        a.approver_role,
                        a.status,
                        a.decision,
                        a.comment,
                        a.assigned_at,
                        a.responded_at,
                        a.deadline,
                        a.duration_minutes,
                        a.is_timeout
                    FROM reimbursement_approvals a
                    LEFT JOIN users u ON a.approver_id = u.user_id
                    WHERE a.application_id = %s
                    ORDER BY a.approval_level ASC
                """

                cur.execute(query, (application_id,))
                results = cur.fetchall()

                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"[ApprovalChain] 获取审批历史失败: {e}")
            return []

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            try:
                self._conn.close()
                logger.info("[ApprovalChain] 数据库连接已关闭")
            except Exception:
                pass

    def __del__(self):
        self.close()
