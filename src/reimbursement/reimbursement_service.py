# -*- coding: utf-8 -*-
"""
报销服务 - 核心协调层

职责：
1. 协调发票识别（QianfanInvoiceRecognizer）
2. 审批链引擎（ApprovalChainEngine）
3. 表单生成（FormGenerator）
4. PDF生成（PDFGenerator）
5. 飞书通知（FeishuClient）
"""
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os

from src.multimodal.qianfan_invoice_recognizer import QianfanInvoiceRecognizer
from src.reimbursement.approval_chain_engine import ApprovalChainEngine
from src.reimbursement.pdf_generator import ReimbursementPDFGenerator
from src.harness.feishu_client import FeishuClient

logger = logging.getLogger(__name__)


class ReimbursementService:
    """
    报销服务 - 整合发票识别、审批流程、通知的核心服务
    """

    def __init__(
        self,
        db_connection_string: Optional[str] = None,
        invoice_recognizer: Optional[QianfanInvoiceRecognizer] = None,
        approval_engine: Optional[ApprovalChainEngine] = None,
        feishu_client: Optional[FeishuClient] = None,
        pdf_generator: Optional[ReimbursementPDFGenerator] = None
    ):
        self.conn_str = db_connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://localhost:5432/business_trip"
        )
        self._conn = None

        # 依赖注入
        qianfan_api_key = os.getenv(
            "QIANFAN_API_KEY",
            "bce-v3/ALTAK-bb5n0uwwEtylRfFVWBnrz/ac8b75364bcb7016af82a0789335a0c8d4ce594e"
        )
        feishu_webhook_key = os.getenv("FEISHU_WEBHOOK_KEY")
        feishu_app_id = os.getenv("FEISHU_APP_ID")
        feishu_app_secret = os.getenv("FEISHU_APP_SECRET")
        feishu_chat_id = os.getenv("FEISHU_CHAT_ID", "oc_f4b85703576e1fcd986ac22399cb65eb")

        self.invoice_recognizer = invoice_recognizer or QianfanInvoiceRecognizer(api_key=qianfan_api_key)
        self.approval_engine = approval_engine or ApprovalChainEngine(db_connection_string)
        # 优先使用消息API（支持回调），降级到Webhook
        if feishu_app_id and feishu_app_secret:
            self.feishu_client = feishu_client or FeishuClient(
                webhook_key=feishu_webhook_key or "dummy",
                app_id=feishu_app_id,
                app_secret=feishu_app_secret
            )
            self.feishu_chat_id = feishu_chat_id
            logger.info("[ReimbursementService] 飞书客户端初始化成功（消息API模式）")
        elif feishu_webhook_key:
            self.feishu_client = feishu_client or FeishuClient(webhook_key=feishu_webhook_key)
            self.feishu_chat_id = None
            logger.warning("[ReimbursementService] 飞书客户端使用Webhook模式（不支持回调）")
        else:
            self.feishu_client = None
            self.feishu_chat_id = None
        self.pdf_generator = pdf_generator or ReimbursementPDFGenerator(db_connection_string)

    def _get_connection(self):
        """获取数据库连接"""
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(self.conn_str)
                logger.info("[ReimbursementService] 数据库连接已建立")
            except Exception as e:
                logger.error(f"[ReimbursementService] 数据库连接失败: {e}")
                raise
        return self._conn

    def upload_and_recognize_invoice(
        self,
        image_path: str
    ) -> Dict[str, Any]:
        """
        上传发票并进行OCR识别

        Args:
            image_path: 发票图片路径

        Returns:
            识别结果字典
        """
        try:
            logger.info(f"[ReimbursementService] 开始识别发票: {image_path}")

            # 1. 调用千帆OCR识别
            result = self.invoice_recognizer.recognize(image_path)

            if not result or result.get('error'):
                logger.error(f"[ReimbursementService] 发票识别失败: {result}")
                return {
                    'success': False,
                    'error': result.get('error', '识别失败')
                }

            # 2. 计算图片哈希（防重复）
            with open(image_path, 'rb') as f:
                image_hash = hashlib.sha256(f.read()).hexdigest()

            # 3. 检查是否重复报销
            is_duplicate = self._check_duplicate_invoice(image_hash)

            # 4. 生成发票ID
            invoice_id = self._generate_invoice_id()

            # 5. 组装返回结果
            invoice_data = {
                'success': True,
                'invoice_id': invoice_id,
                'invoice_code': result.get('invoice_code', ''),
                'invoice_number': result.get('invoice_number', ''),
                'invoice_date': result.get('invoice_date', ''),
                'invoice_type': result.get('invoice_type', '增值税专用发票'),
                'seller_name': result.get('seller_name', ''),
                'seller_tax_id': result.get('seller_tax_id', ''),
                'buyer_name': result.get('buyer_name', ''),
                'buyer_tax_id': result.get('buyer_tax_id', ''),
                'amount': float(result.get('amount', 0)),
                'tax': float(result.get('tax', 0)),
                'total': float(result.get('total', 0)),
                'tax_rate': result.get('tax_rate'),
                'confidence': result.get('confidence', 0.0),
                'warnings': result.get('warnings', []),
                'need_manual_review': result.get('confidence', 1.0) < 0.8,
                'image_hash': image_hash,
                'is_duplicate': is_duplicate,
                'image_url': image_path
            }

            logger.info(
                f"[ReimbursementService] 发票识别成功: {invoice_id}, "
                f"金额: ¥{invoice_data['total']}, "
                f"置信度: {invoice_data['confidence']:.2f}"
            )

            return invoice_data

        except Exception as e:
            logger.error(f"[ReimbursementService] 发票识别异常: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def create_application(
        self,
        user_id: str,
        title: str,
        invoices: List[Dict[str, Any]],
        trip_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建报销申请（草稿状态）

        Args:
            user_id: 申请人ID
            title: 报销标题
            invoices: 发票列表
            trip_info: 出差信息（可选）

        Returns:
            报销申请ID
        """
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 1. 生成报销单号
                application_id = self._generate_application_id(cur)

                # 2. 计算总金额
                total_amount = sum(invoice.get('total', 0) for invoice in invoices)
                invoice_count = len(invoices)

                # 3. 提取出差信息
                trip_destination = trip_info.get('trip_destination') if trip_info else None
                trip_days = trip_info.get('trip_days') if trip_info else None
                trip_purpose = trip_info.get('trip_purpose') if trip_info else None
                remarks = trip_info.get('remarks') if trip_info else None

                # 4. 插入报销申请主表
                insert_app_query = """
                    INSERT INTO reimbursement_applications
                        (application_id, user_id, title, trip_destination,
                         trip_days, trip_purpose, total_amount, invoice_count,
                         status, remarks, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING application_id
                """

                cur.execute(
                    insert_app_query,
                    (application_id, user_id, title, trip_destination,
                     trip_days, trip_purpose, total_amount, invoice_count,
                     'draft', remarks, datetime.now())
                )

                # 5. 插入发票明细
                for invoice in invoices:
                    self._insert_invoice_record(cur, application_id, invoice)

                conn.commit()

                logger.info(
                    f"[ReimbursementService] 报销申请创建成功: {application_id}, "
                    f"用户: {user_id}, 金额: ¥{total_amount}, 发票数: {invoice_count}"
                )

                return application_id

        except Exception as e:
            conn.rollback()
            logger.error(f"[ReimbursementService] 创建报销申请失败: {e}", exc_info=True)
            raise

    def submit_application(
        self,
        application_id: str,
        user_id: str,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提交报销申请（进入审批流程）

        Args:
            application_id: 报销申请ID
            user_id: 申请人ID
            department: 部门名称

        Returns:
            提交结果
        """
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 1. 查询报销申请信息
                cur.execute(
                    "SELECT total_amount FROM reimbursement_applications WHERE application_id = %s",
                    (application_id,)
                )
                app = cur.fetchone()

                if not app:
                    raise ValueError(f"报销申请不存在: {application_id}")

                total_amount = float(app['total_amount'])

                # 2. 匹配审批链
                chain_config = self.approval_engine.match_approval_chain(
                    amount=total_amount,
                    department=department
                )

                if not chain_config:
                    raise ValueError(f"未找到匹配的审批链配置（金额: ¥{total_amount}, 部门: {department}）")

                approval_chain = chain_config['approval_chain']

                # 3. 初始化审批节点
                nodes = self.approval_engine.initialize_approval_nodes(
                    application_id=application_id,
                    approval_chain=approval_chain,
                    user_id=user_id
                )

                # 4. 更新申请状态为submitted
                cur.execute(
                    """
                    UPDATE reimbursement_applications
                    SET status = 'submitted',
                        submitted_at = %s,
                        approval_level = 0
                    WHERE application_id = %s
                    """,
                    (datetime.now(), application_id)
                )

                # 5. 获取第一审批人
                current_approver = self.approval_engine.get_current_approver(application_id)

                conn.commit()

                # 6. 发送飞书通知给第一审批人
                if current_approver:
                    self._send_approval_notification(
                        application_id=application_id,
                        approver_id=current_approver['approver_id'],
                        amount=total_amount,
                        title=app.get('title', '报销申请')
                    )

                logger.info(
                    f"[ReimbursementService] 报销申请已提交: {application_id}, "
                    f"审批链: {chain_config['rule_name']}, "
                    f"当前审批人: {current_approver['approver_id'] if current_approver else 'N/A'}"
                )

                return {
                    'success': True,
                    'application_id': application_id,
                    'status': 'submitted',
                    'chain_config': {
                        'rule_name': chain_config['rule_name'],
                        'approval_mode': chain_config['approval_mode'],
                        'total_nodes': len(nodes)
                    },
                    'current_approver': current_approver,
                    'total_nodes': len(nodes)
                }

        except Exception as e:
            conn.rollback()
            logger.error(f"[ReimbursementService] 提交报销申请失败: {e}", exc_info=True)
            raise

    def approve(
        self,
        application_id: str,
        approver_id: str,
        decision: str,
        comment: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        审批操作（通过/拒绝）

        Args:
            application_id: 报销申请ID
            approver_id: 审批人ID
            decision: 审批决策 (approve/reject)
            comment: 审批意见
            ip_address: 操作IP
            user_agent: 浏览器UA

        Returns:
            审批结果
        """
        conn = self._get_connection()

        try:
            # 1. 执行审批操作
            success = self.approval_engine.approve_node(
                application_id=application_id,
                approver_id=approver_id,
                decision=decision,
                comment=comment
            )

            if not success:
                return {
                    'success': False,
                    'error': '审批失败：未找到待审批节点或权限不足'
                }

            # 2. 检查审批是否完成
            is_completed, final_status = self.approval_engine.is_approval_completed(application_id)

            # 3. 更新报销申请状态
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if is_completed:
                    # 审批完成
                    if final_status == 'approved':
                        # 生成PDF报销单
                        pdf_url = self._generate_pdf_reimbursement(application_id)

                        cur.execute(
                            """
                            UPDATE reimbursement_applications
                            SET status = 'approved',
                                approved_at = %s,
                                pdf_url = %s
                            WHERE application_id = %s
                            """,
                            (datetime.now(), pdf_url, application_id)
                        )

                        logger.info(f"[ReimbursementService] 报销申请已通过: {application_id}, PDF: {pdf_url}")

                    elif final_status == 'rejected':
                        cur.execute(
                            """
                            UPDATE reimbursement_applications
                            SET status = 'rejected',
                                rejection_reason = %s
                            WHERE application_id = %s
                            """,
                            (comment, application_id)
                        )

                        logger.info(f"[ReimbursementService] 报销申请已拒绝: {application_id}")

                else:
                    # 审批未完成，获取下一审批人
                    next_approver = self.approval_engine.get_current_approver(application_id)

                    if next_approver:
                        cur.execute(
                            """
                            UPDATE reimbursement_applications
                            SET current_approver = %s,
                                approval_level = %s,
                                status = 'approving'
                            WHERE application_id = %s
                            """,
                            (next_approver['approver_id'], next_approver['approval_level'], application_id)
                        )

                        # 发送通知给下一审批人
                        self._send_approval_notification(
                            application_id=application_id,
                            approver_id=next_approver['approver_id'],
                            amount=0,  # 这里需要查询金额
                            title=f"报销申请审批通知"
                        )

                # 4. 记录审计日志
                self._insert_audit_log(
                    cur=cur,
                    application_id=application_id,
                    operation='approve' if decision == 'approve' else 'reject',
                    operator_id=approver_id,
                    details={
                        'decision': decision,
                        'comment': comment,
                        'is_completed': is_completed,
                        'final_status': final_status
                    },
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                conn.commit()

            return {
                'success': True,
                'application_id': application_id,
                'is_completed': is_completed,
                'final_status': final_status,
                'next_approver': self.approval_engine.get_current_approver(application_id) if not is_completed else None
            }

        except Exception as e:
            conn.rollback()
            logger.error(f"[ReimbursementService] 审批操作失败: {e}", exc_info=True)
            raise

    # ========== 私有辅助方法 ==========

    def _generate_application_id(self, cursor) -> str:
        """生成报销单号（格式：REI+YYYYMMDD+3位序号）"""
        today = datetime.now().strftime('%Y%m%d')
        prefix = f"REI{today}"

        # 查询今天已有的最大序号
        cursor.execute(
            """
            SELECT application_id FROM reimbursement_applications
            WHERE application_id LIKE %s
            ORDER BY application_id DESC
            LIMIT 1
            """,
            (f"{prefix}%",)
        )

        result = cursor.fetchone()

        if result:
            last_id = result['application_id']
            seq = int(last_id[-3:]) + 1
        else:
            seq = 1

        return f"{prefix}{seq:03d}"

    def _generate_invoice_id(self) -> str:
        """生成发票ID（格式：INV+YYYYMMDD+HHmmss+3位随机数）"""
        import random
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        rand_num = random.randint(100, 999)
        return f"INV{timestamp}{rand_num}"

    def _check_duplicate_invoice(self, image_hash: str) -> bool:
        """检查发票是否重复报销"""
        conn = self._get_connection()

        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM reimbursement_invoices WHERE image_hash = %s",
                    (image_hash,)
                )
                count = cur.fetchone()[0]
                return count > 0
        except Exception as e:
            logger.error(f"[ReimbursementService] 检查重复发票失败: {e}")
            return False

    def _insert_invoice_record(
        self,
        cursor,
        application_id: str,
        invoice: Dict[str, Any]
    ):
        """插入发票记录到数据库"""
        insert_query = """
            INSERT INTO reimbursement_invoices
                (application_id, invoice_id, invoice_code, invoice_number,
                 invoice_date, invoice_type, amount, tax, total, tax_rate,
                 seller_name, seller_tax_id, buyer_name, buyer_tax_id,
                 confidence, ocr_warnings, need_manual_review,
                 image_url, image_hash, is_duplicate, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            insert_query,
            (
                application_id,
                invoice.get('invoice_id'),
                invoice.get('invoice_code'),
                invoice.get('invoice_number'),
                invoice.get('invoice_date'),
                invoice.get('invoice_type', '增值税专用发票'),
                invoice.get('amount', 0),
                invoice.get('tax', 0),
                invoice.get('total', 0),
                invoice.get('tax_rate'),
                invoice.get('seller_name'),
                invoice.get('seller_tax_id'),
                invoice.get('buyer_name'),
                invoice.get('buyer_tax_id'),
                invoice.get('confidence', 0.0),
                invoice.get('warnings', []),
                invoice.get('need_manual_review', False),
                invoice.get('image_url'),
                invoice.get('image_hash'),
                invoice.get('is_duplicate', False),
                datetime.now()
            )
        )

    def _send_approval_notification(
        self,
        application_id: str,
        approver_id: str,
        amount: float,
        title: str
    ):
        """发送飞书审批通知"""
        try:
            if not self.feishu_client:
                logger.warning(f"[ReimbursementService] 飞书客户端未配置，跳过通知")
                return

            # 获取申请详情（用于卡片展示）
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT ra.*, u.full_name as user_name
                    FROM reimbursement_applications ra
                    LEFT JOIN users u ON ra.user_id = u.user_id
                    WHERE ra.application_id = %s
                """, (application_id,))
                application = cur.fetchone()

            if not application:
                logger.error(f"[ReimbursementService] 找不到报销申请: {application_id}")
                return

            # 优先使用消息API（支持回调）
            if self.feishu_chat_id:
                result = self.feishu_client.send_approval_card_to_chat(
                    chat_id=self.feishu_chat_id,
                    approval_id=application_id,
                    user_id=application['user_id'],
                    applicant=application.get('user_name', '申请人'),
                    destination=application.get('trip_destination', '未知'),
                    days=application.get('trip_days', 0),
                    amount=amount
                )

                if result.get('code') == 0:
                    logger.info(f"[ReimbursementService] 飞书审批卡片已发送（消息API）: {application_id}")
                else:
                    logger.error(f"[ReimbursementService] 飞书卡片发送失败: {result}")
            else:
                # 降级使用Webhook（不支持回调）
                result = self.feishu_client.send_approval_card(
                    approval_id=application_id,
                    user_id=application['user_id'],
                    applicant=application.get('user_name', '申请人'),
                    destination=application.get('trip_destination', '未知'),
                    days=application.get('trip_days', 0),
                    amount=amount
                )

                if result.get('StatusCode') == 0:
                    logger.info(f"[ReimbursementService] 飞书审批卡片已发送（Webhook）: {application_id}")
                    logger.warning("[ReimbursementService] 使用Webhook模式，不支持按钮回调")
                else:
                    logger.error(f"[ReimbursementService] 飞书卡片发送失败: {result}")

        except Exception as e:
            logger.error(f"[ReimbursementService] 发送审批通知失败: {e}", exc_info=True)

    def _generate_pdf_reimbursement(self, application_id: str) -> str:
        """生成PDF报销单"""
        try:
            pdf_path = self.pdf_generator.generate(application_id)
            logger.info(f"[ReimbursementService] PDF生成成功: {pdf_path}")
            return pdf_path
        except Exception as e:
            logger.error(f"[ReimbursementService] PDF生成失败: {e}")
            # PDF生成失败不影响审批流程，返回空路径
            return ""

    def _insert_audit_log(
        self,
        cur,
        application_id: str,
        operation: str,
        operator_id: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """插入审计日志"""
        import json

        insert_query = """
            INSERT INTO approval_audit_logs
                (application_id, operation, operator_id, details,
                 ip_address, user_agent, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        cur.execute(
            insert_query,
            (application_id, operation, operator_id,
             json.dumps(details, ensure_ascii=False),
             ip_address, user_agent, datetime.now())
        )

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            try:
                self._conn.close()
                logger.info("[ReimbursementService] 数据库连接已关闭")
            except Exception:
                pass

    def __del__(self):
        self.close()
