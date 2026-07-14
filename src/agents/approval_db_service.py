# -*- coding: utf-8 -*-
"""
ApprovalDBService - 审批记录数据库持久化层

Phase 4 P1: 将审批记录写入 PostgreSQL approval_records 表

用法:
    service = ApprovalDBService()
    service.save_approval_record(approval_info, status="approved", approver="system")

数据库不可用时静默降级（log warning，不阻塞审批流）
"""
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ApprovalDBService:
    """
    审批记录数据库服务

    将审批记录持久化到 PostgreSQL approval_records 表。
    数据库不可用时自动降级（仅 log warning），不阻塞审批流程。
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        初始化数据库服务

        Args:
            connection_string: PostgreSQL 连接字符串。
                默认从环境变量 APPROVAL_DB_URL 或 DATABASE_URL 读取。
        """
        self._conn_str = connection_string or os.getenv(
            "APPROVAL_DB_URL",
            os.getenv("DATABASE_URL")
        )
        self._conn = None

    def _get_connection(self):
        """惰性获取数据库连接"""
        if self._conn is not None:
            return self._conn
        if not self._conn_str:
            logger.warning("[ApprovalDB] 未配置数据库连接，跳过持久化")
            return None
        try:
            import psycopg2
            self._conn = psycopg2.connect(self._conn_str)
            self._conn.autocommit = True
            logger.info("[ApprovalDB] PostgreSQL 连接已建立")
            return self._conn
        except Exception as e:
            logger.warning(f"[ApprovalDB] 数据库连接失败: {e}，降级为内存模式")
            return None

    def save_approval_record(
        self,
        approval_info: Dict[str, Any],
        status: str = "pending",
        approver: str = "system",
        comment: Optional[str] = None,
    ) -> bool:
        """
        保存审批记录到数据库
        """
        conn = self._get_connection()
        if conn is None:
            logger.info(f"[ApprovalDB] 内存模式: 审批 {approval_info.get('approval_id', 'N/A')} 状态={status}")
            return False

        approved_at = None
        if status in ("approved", "rejected"):
            approved_at = datetime.now()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO approval_records
                        (approval_id, user_id, destination, days, amount,
                         status, approver, comment, submitted_at, approved_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (approval_id)
                    DO UPDATE SET
                        status = EXCLUDED.status,
                        approver = EXCLUDED.approver,
                        comment = EXCLUDED.comment,
                        approved_at = EXCLUDED.approved_at,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    approval_info.get("approval_id"),
                    approval_info.get("user_id"),
                    approval_info.get("destination"),
                    approval_info.get("days"),
                    approval_info.get("estimated_amount", 0),
                    status,
                    approver,
                    comment,
                    approval_info.get("submit_time"),
                    approved_at,
                ))
            logger.info(f"[ApprovalDB] 记录已写入: {approval_info.get('approval_id')} status={status}")
            return True
        except Exception as e:
            logger.warning(f"[ApprovalDB] 写入失败: {e}，降级为内存模式")
            return False

    def update_approval_status(
        self,
        approval_id: str,
        status: str,
        approver: str = "system",
        comment: Optional[str] = None,
    ) -> bool:
        """更新审批状态"""
        conn = self._get_connection()
        if conn is None:
            return False
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE approval_records
                    SET status = %s, approver = %s, comment = %s,
                        approved_at = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE approval_id = %s
                """, (
                    status, approver, comment,
                    datetime.now() if status in ("approved", "rejected") else None,
                    approval_id,
                ))
            logger.info(f"[ApprovalDB] 状态已更新: {approval_id} -> {status}")
            return True
        except Exception as e:
            logger.warning(f"[ApprovalDB] 状态更新失败: {e}")
            return False

    def get_approval_record(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """
        获取审批记录

        Args:
            approval_id: 审批单号

        Returns:
            审批记录字典，不存在返回 None
        """
        conn = self._get_connection()
        if conn is None:
            return None

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT approval_id, user_id, destination, days, amount,
                           status, approver, comment, submitted_at, approved_at
                    FROM approval_records
                    WHERE approval_id = %s
                """, (approval_id,))

                row = cur.fetchone()
                if not row:
                    logger.info(f"[ApprovalDB] 记录不存在: {approval_id}")
                    return None

                # 构造返回字典
                record = {
                    "approval_id": row[0],
                    "user_id": row[1],
                    "destination": row[2],
                    "days": row[3],
                    "estimated_amount": row[4],
                    "status": row[5],
                    "approver": row[6],
                    "comment": row[7],
                    "submit_time": row[8].isoformat() if row[8] else None,
                    "approval_time": row[9].isoformat() if row[9] else None,
                }

                logger.info(f"[ApprovalDB] 记录已查询: {approval_id}")
                return record

        except Exception as e:
            logger.warning(f"[ApprovalDB] 查询失败: {e}")
            return None

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            finally:
                self._conn = None

    def __del__(self):
        self.close()
