# -*- coding: utf-8 -*-
"""
PDF报销单生成器

职责：
生成标准格式的报销单据PDF文件
使用reportlab库生成企业级PDF文档
"""
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class ReimbursementPDFGenerator:
    """
    报销单PDF生成器

    生成符合企业标准的报销单据PDF
    """

    def __init__(self, db_connection_string: Optional[str] = None):
        self.conn_str = db_connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://localhost:5432/business_trip"
        )
        self._conn = None

        # PDF输出目录
        self.output_dir = Path("static/pdfs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 注册中文字体（Windows系统）
        self._register_fonts()

    def _get_connection(self):
        """获取数据库连接"""
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(self.conn_str)
                logger.info("[PDFGenerator] 数据库连接已建立")
            except Exception as e:
                logger.error(f"[PDFGenerator] 数据库连接失败: {e}")
                raise
        return self._conn

    def _register_fonts(self):
        """注册中文字体"""
        try:
            # Windows系统常见字体路径
            font_paths = [
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
                "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
            ]

            font_registered = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('SimHei', font_path))
                        font_registered = True
                        logger.info(f"[PDFGenerator] 中文字体注册成功: {font_path}")
                        break
                    except Exception as e:
                        logger.warning(f"[PDFGenerator] 字体注册失败 {font_path}: {e}")
                        continue

            if not font_registered:
                logger.warning("[PDFGenerator] 未找到中文字体，将使用默认字体（可能显示异常）")

        except Exception as e:
            logger.error(f"[PDFGenerator] 字体注册异常: {e}")

    def generate(
        self,
        application_id: str,
        output_filename: Optional[str] = None
    ) -> str:
        """
        生成PDF报销单

        Args:
            application_id: 报销申请ID
            output_filename: 输出文件名（可选，默认使用application_id）

        Returns:
            PDF文件路径
        """
        try:
            logger.info(f"[PDFGenerator] 开始生成PDF: {application_id}")

            # 1. 从数据库查询报销单数据
            application_data = self._fetch_application_data(application_id)
            if not application_data:
                raise ValueError(f"报销申请不存在: {application_id}")

            # 2. 查询发票明细
            invoices = self._fetch_invoices(application_id)

            # 3. 查询审批记录
            approvals = self._fetch_approvals(application_id)

            # 4. 生成PDF
            if not output_filename:
                output_filename = f"{application_id}.pdf"

            output_path = self.output_dir / output_filename

            self._create_pdf(
                output_path=str(output_path),
                application=application_data,
                invoices=invoices,
                approvals=approvals
            )

            logger.info(f"[PDFGenerator] PDF生成成功: {output_path}")

            return str(output_path)

        except Exception as e:
            logger.error(f"[PDFGenerator] PDF生成失败: {e}", exc_info=True)
            raise

    def _fetch_application_data(self, application_id: str) -> Optional[Dict[str, Any]]:
        """查询报销申请数据"""
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT
                        a.application_id,
                        a.user_id,
                        u.full_name as user_name,
                        u.department,
                        u.position,
                        a.title,
                        a.trip_destination,
                        a.trip_days,
                        a.trip_purpose,
                        a.total_amount,
                        a.invoice_count,
                        a.status,
                        a.submitted_at,
                        a.approved_at,
                        a.remarks
                    FROM reimbursement_applications a
                    LEFT JOIN users u ON a.user_id = u.user_id
                    WHERE a.application_id = %s
                """

                cur.execute(query, (application_id,))
                result = cur.fetchone()

                return dict(result) if result else None

        except Exception as e:
            logger.error(f"[PDFGenerator] 查询报销数据失败: {e}")
            return None

    def _fetch_invoices(self, application_id: str) -> List[Dict[str, Any]]:
        """查询发票明细"""
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT
                        invoice_code,
                        invoice_number,
                        invoice_date,
                        invoice_type,
                        seller_name,
                        amount,
                        tax,
                        total,
                        confidence
                    FROM reimbursement_invoices
                    WHERE application_id = %s
                    ORDER BY created_at ASC
                """

                cur.execute(query, (application_id,))
                results = cur.fetchall()

                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"[PDFGenerator] 查询发票明细失败: {e}")
            return []

    def _fetch_approvals(self, application_id: str) -> List[Dict[str, Any]]:
        """查询审批记录"""
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
                        a.responded_at,
                        a.duration_minutes
                    FROM reimbursement_approvals a
                    LEFT JOIN users u ON a.approver_id = u.user_id
                    WHERE a.application_id = %s
                    ORDER BY a.approval_level ASC
                """

                cur.execute(query, (application_id,))
                results = cur.fetchall()

                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"[PDFGenerator] 查询审批记录失败: {e}")
            return []

    def _create_pdf(
        self,
        output_path: str,
        application: Dict[str, Any],
        invoices: List[Dict[str, Any]],
        approvals: List[Dict[str, Any]]
    ):
        """创建PDF文档"""
        # 创建PDF文档
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )

        # 构建文档内容
        story = []
        styles = self._get_styles()

        # 1. 标题
        story.append(Paragraph("内江嘉宏城建集团有限公司", styles['Title']))
        story.append(Paragraph("差旅费报销申请单", styles['Subtitle']))
        story.append(Spacer(1, 10*mm))

        # 2. 基本信息表格
        story.extend(self._build_basic_info_table(application, styles))
        story.append(Spacer(1, 5*mm))

        # 3. 出差信息表格
        story.extend(self._build_trip_info_table(application, styles))
        story.append(Spacer(1, 5*mm))

        # 4. 发票明细表格
        story.append(Paragraph("发票明细", styles['Heading2']))
        story.append(Spacer(1, 3*mm))
        story.extend(self._build_invoice_table(invoices, styles))
        story.append(Spacer(1, 5*mm))

        # 5. 审批记录表格
        story.append(Paragraph("审批记录", styles['Heading2']))
        story.append(Spacer(1, 3*mm))
        story.extend(self._build_approval_table(approvals, styles))
        story.append(Spacer(1, 10*mm))

        # 6. 页脚信息
        story.append(Paragraph(
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 系统生成，仅供参考",
            styles['Footer']
        ))

        # 生成PDF
        doc.build(story)

    def _get_styles(self) -> Dict[str, ParagraphStyle]:
        """获取样式表"""
        styles = getSampleStyleSheet()

        # 自定义样式
        custom_styles = {
            'Title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontName='SimHei',
                fontSize=18,
                textColor=colors.HexColor('#1a1a1a'),
                alignment=TA_CENTER,
                spaceAfter=5*mm
            ),
            'Subtitle': ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading1'],
                fontName='SimHei',
                fontSize=16,
                textColor=colors.HexColor('#333333'),
                alignment=TA_CENTER,
                spaceAfter=5*mm
            ),
            'Heading2': ParagraphStyle(
                'CustomHeading2',
                parent=styles['Heading2'],
                fontName='SimHei',
                fontSize=12,
                textColor=colors.HexColor('#333333'),
                spaceBefore=3*mm,
                spaceAfter=2*mm
            ),
            'Normal': ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName='SimHei',
                fontSize=10,
                textColor=colors.HexColor('#333333')
            ),
            'Footer': ParagraphStyle(
                'CustomFooter',
                parent=styles['Normal'],
                fontName='SimHei',
                fontSize=8,
                textColor=colors.HexColor('#999999'),
                alignment=TA_CENTER
            )
        }

        return custom_styles

    def _build_basic_info_table(
        self,
        application: Dict[str, Any],
        styles: Dict[str, ParagraphStyle]
    ) -> List:
        """构建基本信息表格"""
        data = [
            ['报销单号', application.get('application_id', 'N/A'),
             '申请人', application.get('user_name', 'N/A')],
            ['所属部门', application.get('department', 'N/A'),
             '职位', application.get('position', 'N/A')],
            ['提交日期',
             application.get('submitted_at').strftime('%Y-%m-%d') if application.get('submitted_at') else 'N/A',
             '报销总额',
             f"¥{application.get('total_amount', 0):.2f}"]
        ]

        table = Table(data, colWidths=[30*mm, 60*mm, 30*mm, 50*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f0f0')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))

        return [table]

    def _build_trip_info_table(
        self,
        application: Dict[str, Any],
        styles: Dict[str, ParagraphStyle]
    ) -> List:
        """构建出差信息表格"""
        data = [
            ['出差目的地', application.get('trip_destination', 'N/A')],
            ['出差天数', f"{application.get('trip_days', 0)}天"],
            ['出差事由', application.get('trip_purpose', '无')]
        ]

        if application.get('remarks'):
            data.append(['备注说明', application.get('remarks')])

        table = Table(data, colWidths=[30*mm, 140*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))

        return [table]

    def _build_invoice_table(
        self,
        invoices: List[Dict[str, Any]],
        styles: Dict[str, ParagraphStyle]
    ) -> List:
        """构建发票明细表格"""
        # 表头
        data = [
            ['序号', '发票代码', '发票号码', '开票日期', '销售方', '金额', '税额', '合计']
        ]

        # 发票数据
        for idx, invoice in enumerate(invoices):
            invoice_code = invoice.get('invoice_code', '')
            seller_name = invoice.get('seller_name', '')

            data.append([
                str(idx + 1),
                invoice_code[:10] + '...' if len(invoice_code) > 10 else invoice_code,
                invoice.get('invoice_number', ''),
                invoice.get('invoice_date').strftime('%Y-%m-%d') if invoice.get('invoice_date') else '',
                seller_name[:15] + '...' if len(seller_name) > 15 else seller_name,
                f"{invoice.get('amount', 0):.2f}",
                f"{invoice.get('tax', 0):.2f}",
                f"{invoice.get('total', 0):.2f}"
            ])

        # 合计行
        total_amount = sum(inv.get('amount', 0) for inv in invoices)
        total_tax = sum(inv.get('tax', 0) for inv in invoices)
        total_sum = sum(inv.get('total', 0) for inv in invoices)

        data.append([
            '合计', '', '', '', '',
            f"{total_amount:.2f}",
            f"{total_tax:.2f}",
            f"{total_sum:.2f}"
        ])

        table = Table(data, colWidths=[10*mm, 25*mm, 20*mm, 20*mm, 35*mm, 20*mm, 20*mm, 20*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, -1), (-1, -1), 'SimHei'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))

        return [table]

    def _build_approval_table(
        self,
        approvals: List[Dict[str, Any]],
        styles: Dict[str, ParagraphStyle]
    ) -> List:
        """构建审批记录表格"""
        # 表头
        data = [
            ['层级', '审批人', '职责', '决策', '审批时间', '耗时', '意见']
        ]

        # 审批数据
        for approval in approvals:
            level = f"第{approval.get('approval_level', 0)}级"
            approver = approval.get('approver_name', 'N/A')
            role = self._translate_role(approval.get('approver_role', ''))

            decision_text = ''
            if approval.get('status') == 'approved':
                decision_text = '通过'
            elif approval.get('status') == 'rejected':
                decision_text = '拒绝'
            elif approval.get('status') == 'pending':
                decision_text = '待审批'

            approval_time = ''
            if approval.get('responded_at'):
                approval_time = approval.get('responded_at').strftime('%Y-%m-%d %H:%M')

            duration = ''
            if approval.get('duration_minutes'):
                hours = int(approval.get('duration_minutes') / 60)
                minutes = int(approval.get('duration_minutes') % 60)
                duration = f"{hours}h{minutes}m"

            comment = approval.get('comment', '无')
            if len(comment) > 20:
                comment = comment[:20] + '...'

            data.append([
                level,
                approver,
                role,
                decision_text,
                approval_time,
                duration,
                comment
            ])

        table = Table(data, colWidths=[15*mm, 25*mm, 25*mm, 15*mm, 35*mm, 20*mm, 35*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))

        return [table]

    def _translate_role(self, role: str) -> str:
        """翻译审批角色"""
        role_map = {
            'direct_manager': '直属经理',
            'dept_manager': '部门经理',
            'vp': '副总经理',
            'finance': '财务总监',
            'ceo': '总经理',
            'executive': '高管'
        }
        return role_map.get(role, role)

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            try:
                self._conn.close()
                logger.info("[PDFGenerator] 数据库连接已关闭")
            except Exception:
                pass

    def __del__(self):
        self.close()
