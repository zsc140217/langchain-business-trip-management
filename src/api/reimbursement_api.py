# -*- coding: utf-8 -*-
"""
报销管理REST API

提供报销申请、审批、查询的HTTP接口
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Header
from pydantic import BaseModel, Field
from typing import List

from src.reimbursement.reimbursement_service import ReimbursementService
from src.reimbursement.form_generator import ReimbursementFormGenerator
from src.reimbursement.feishu_approval_client import FeishuApprovalClient
from src.reimbursement.invoice_verification_service import get_verification_service

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/api/reimbursement", tags=["报销管理"])

# 初始化服务
reimbursement_service = ReimbursementService()
form_generator = ReimbursementFormGenerator()
feishu_approval = FeishuApprovalClient()


# ========== Pydantic模型定义 ==========

class InvoiceRecognitionResponse(BaseModel):
    """发票识别响应"""
    success: bool
    invoice_id: Optional[str] = None
    invoice_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CreateApplicationRequest(BaseModel):
    """创建报销申请请求"""
    user_id: str = Field(..., description="申请人ID")
    title: str = Field(..., min_length=5, max_length=100, description="报销标题")
    trip_destination: Optional[str] = Field(default=None, description="出差目的地")
    trip_days: Optional[int] = Field(default=None, ge=1, le=365, description="出差天数")
    trip_purpose: Optional[str] = Field(default="", description="出差事由")
    invoice_ids: List[str] = Field(..., min_items=1, description="发票ID列表")
    remarks: Optional[str] = Field(default="", description="备注")


class CreateApplicationResponse(BaseModel):
    """创建报销申请响应"""
    success: bool
    application_id: Optional[str] = None
    status: str = "draft"
    total_amount: float = 0.0
    invoice_count: int = 0


class SubmitApplicationResponse(BaseModel):
    """提交报销申请响应"""
    success: bool
    application_id: str
    status: str
    chain_config: Dict[str, Any]
    current_approver: Optional[Dict[str, Any]] = None


class ApprovalRequest(BaseModel):
    """审批请求"""
    approver_id: str = Field(..., description="审批人ID")
    decision: str = Field(..., description="审批决策: approve/reject")
    comment: Optional[str] = Field(default="", description="审批意见")


class ApprovalResponse(BaseModel):
    """审批响应"""
    success: bool
    application_id: str
    is_completed: bool
    final_status: Optional[str] = None
    next_approver: Optional[Dict[str, Any]] = None


class ApplicationDetailResponse(BaseModel):
    """报销申请详情响应"""
    application_id: str
    user_id: str
    title: str
    status: str
    total_amount: float
    invoice_count: int
    created_at: str
    submitted_at: Optional[str] = None
    approved_at: Optional[str] = None
    trip_info: Optional[Dict[str, Any]] = None
    invoices: List[Dict[str, Any]] = []
    approvals: List[Dict[str, Any]] = []


# ========== API路由 ==========

@router.post("/upload-invoice", response_model=InvoiceRecognitionResponse)
async def upload_invoice(
    file: UploadFile = File(..., description="发票图片文件")
):
    """
    上传发票并进行OCR识别

    - 支持格式：JPG, PNG, PDF
    - 文件大小：< 10MB
    - 返回：发票识别结果
    """
    try:
        # 验证文件类型
        allowed_types = ["image/jpeg", "image/png", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}"
            )

        # 保存临时文件
        import tempfile
        import os

        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"invoice_{datetime.now().timestamp()}_{file.filename}")

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 调用识别服务
        result = reimbursement_service.upload_and_recognize_invoice(temp_path)

        # 清理临时文件
        try:
            os.remove(temp_path)
        except Exception:
            pass

        if result.get('success'):
            # OCR识别成功后，自动调用发票验真
            invoice_data = result.get('invoice_data', {})
            verification_result = None

            # 提取必要的验证参数
            invoice_number = invoice_data.get('invoice_number') or invoice_data.get('InvoiceNum')
            invoice_date = invoice_data.get('invoice_date') or invoice_data.get('InvoiceDate')
            invoice_code = invoice_data.get('invoice_code') or invoice_data.get('InvoiceCode')
            invoice_sum = invoice_data.get('total') or invoice_data.get('TotalAmount')
            verify_code = invoice_data.get('check_code') or invoice_data.get('CheckCode')

            # 如果有必填字段，则调用验证服务
            if invoice_number and invoice_date:
                try:
                    verification_service = get_verification_service()
                    verification_result = verification_service.verify_invoice(
                        invoice_number=invoice_number,
                        invoice_date=invoice_date,
                        invoice_code=invoice_code,
                        invoice_sum=float(invoice_sum) if invoice_sum else None,
                        verify_code=verify_code
                    )

                    logger.info(
                        f"[API] 发票验真完成: "
                        f"号码={invoice_number}, "
                        f"状态={verification_result.get('status')}"
                    )
                except Exception as e:
                    logger.error(f"[API] 发票验真失败: {e}", exc_info=True)
                    verification_result = {
                        "success": False,
                        "status": "error",
                        "message": f"验真服务异常: {str(e)}"
                    }
            else:
                logger.warning(
                    f"[API] OCR未识别到必要字段，跳过验真: "
                    f"invoice_number={invoice_number}, invoice_date={invoice_date}"
                )
                verification_result = {
                    "success": False,
                    "status": "skipped",
                    "message": "OCR未识别到发票号码或日期，无法验真"
                }

            # 将验真结果添加到响应中
            result['verification'] = verification_result

            return InvoiceRecognitionResponse(
                success=True,
                invoice_id=result.get('invoice_id'),
                invoice_data=result
            )
        else:
            return InvoiceRecognitionResponse(
                success=False,
                error=result.get('error', '识别失败')
            )

    except Exception as e:
        logger.error(f"[API] 上传发票失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/applications", response_model=CreateApplicationResponse)
async def create_application(request: CreateApplicationRequest):
    """
    创建报销申请（草稿状态）

    - 需要先上传发票并获取invoice_ids
    - 创建后状态为draft，需要调用submit接口提交审批
    """
    try:
        # 构建发票列表（这里简化，实际应从数据库查询）
        invoices = []
        for invoice_id in request.invoice_ids:
            # TODO: 从数据库或缓存查询发票数据
            invoices.append({"invoice_id": invoice_id})

        # 构建出差信息
        trip_info = {
            "trip_destination": request.trip_destination,
            "trip_days": request.trip_days,
            "trip_purpose": request.trip_purpose,
            "remarks": request.remarks
        }

        # 调用服务创建申请
        application_id = reimbursement_service.create_application(
            user_id=request.user_id,
            title=request.title,
            invoices=invoices,
            trip_info=trip_info
        )

        return CreateApplicationResponse(
            success=True,
            application_id=application_id,
            status="draft",
            invoice_count=len(invoices)
        )

    except Exception as e:
        logger.error(f"[API] 创建报销申请失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/applications/{application_id}/submit", response_model=SubmitApplicationResponse)
async def submit_application(
    application_id: str,
    user_id: str,
    department: Optional[str] = None
):
    """
    提交报销申请（进入审批流程）

    - 将报销申请从draft状态变为submitted
    - 自动匹配审批链并初始化审批节点
    - 发送通知给第一审批人
    """
    try:
        result = reimbursement_service.submit_application(
            application_id=application_id,
            user_id=user_id,
            department=department
        )

        return SubmitApplicationResponse(
            success=result['success'],
            application_id=application_id,
            status=result['status'],
            chain_config=result['chain_config'],
            current_approver=result.get('current_approver')
        )

    except Exception as e:
        logger.error(f"[API] 提交报销申请失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/applications/{application_id}/approve", response_model=ApprovalResponse)
async def approve_application(
    application_id: str,
    request: ApprovalRequest,
    req: Request
):
    """
    审批操作（通过/拒绝）

    - decision: approve（通过）/ reject（拒绝）
    - 自动流转到下一审批人
    - 全部通过后自动生成PDF
    """
    try:
        # 获取客户端信息
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get('user-agent')

        result = reimbursement_service.approve(
            application_id=application_id,
            approver_id=request.approver_id,
            decision=request.decision,
            comment=request.comment,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return ApprovalResponse(
            success=result['success'],
            application_id=application_id,
            is_completed=result['is_completed'],
            final_status=result.get('final_status'),
            next_approver=result.get('next_approver')
        )

    except Exception as e:
        logger.error(f"[API] 审批操作失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications")
async def list_applications(user_id: str):
    """查询用户的报销记录列表 - Mock实现"""
    try:
        mock_applications = [
            {"application_id": "app_001", "title": "北京出差报销", "total_amount": 1580.00,
             "status": "approved", "created_at": "2026-07-20T10:30:00", "current_approver": None},
            {"application_id": "app_002", "title": "上海出差报销", "total_amount": 2350.00,
             "status": "pending", "created_at": "2026-07-22T14:15:00",
             "current_approver": {"approver_name": "张经理"}},
            {"application_id": "app_003", "title": "深圳出差报销", "total_amount": 3200.00,
             "status": "rejected", "created_at": "2026-07-18T09:00:00", "current_approver": None}
        ]
        return {"applications": mock_applications}
    except Exception as e:
        logger.error(f"[API] 查询报销记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/{application_id}", response_model=ApplicationDetailResponse)
async def get_application(application_id: str):
    """查询报销申请详情 - Mock实现"""
    try:
        mock_details = {
            "app_001": {
                "application_id": "app_001", "user_id": "user_001", "title": "北京出差报销",
                "status": "approved", "total_amount": 1580.00, "invoice_count": 2,
                "created_at": "2026-07-20T10:30:00", "submitted_at": "2026-07-20T10:35:00",
                "approved_at": "2026-07-21T09:15:00",
                "trip_info": {"destination": "北京", "days": 2, "reason": "客户拜访"},
                "invoices": [
                    {"invoice_id": "inv_001", "invoice_number": "00123456", "amount": 800.00,
                     "date": "2026-07-20", "vendor": "北京XX酒店"},
                    {"invoice_id": "inv_002", "invoice_number": "00123457", "amount": 780.00,
                     "date": "2026-07-21", "vendor": "北京YY餐厅"}
                ],
                "approvals": [
                    {"approver_name": "张经理", "approver_id": "user_002", "role": "直属经理",
                     "status": "approved", "approved_at": "2026-07-20T15:30:00"},
                    {"approver_name": "李总监", "approver_id": "user_003", "role": "部门总监",
                     "status": "approved", "approved_at": "2026-07-21T09:15:00"}
                ]
            },
            "app_002": {
                "application_id": "app_002", "user_id": "user_001", "title": "上海出差报销",
                "status": "pending", "total_amount": 2350.00, "invoice_count": 2,
                "created_at": "2026-07-22T14:15:00", "submitted_at": "2026-07-22T14:20:00",
                "approved_at": None,
                "trip_info": {"destination": "上海", "days": 3, "reason": "项目实施"},
                "invoices": [
                    {"invoice_id": "inv_003", "invoice_number": "00234567", "amount": 1200.00,
                     "date": "2026-07-22", "vendor": "上海XX酒店"},
                    {"invoice_id": "inv_004", "invoice_number": "00234568", "amount": 1150.00,
                     "date": "2026-07-23", "vendor": "上海YY交通"}
                ],
                "approvals": [
                    {"approver_name": "张经理", "approver_id": "user_002", "role": "直属经理",
                     "status": "pending", "approved_at": None}
                ]
            }
        }

        if application_id not in mock_details:
            raise HTTPException(status_code=404, detail="报销记录不存在")

        return ApplicationDetailResponse(**mock_details[application_id])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 查询报销申请失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/{application_id}/pdf")
async def download_pdf(application_id: str):
    """
    下载PDF报销单

    - 实时生成PDF
    - 返回PDF文件流
    """
    try:
        from fastapi.responses import StreamingResponse
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_CENTER
        import os
        from datetime import datetime

        # 获取Mock数据
        mock_details = {
            "app_001": {
                "application_id": "app_001", "user_id": "user_001", "title": "北京出差报销",
                "user_name": "王小明", "department": "销售部", "position": "销售经理",
                "status": "approved", "total_amount": 1580.00, "invoice_count": 2,
                "created_at": "2026-07-20T10:30:00", "submitted_at": "2026-07-20T10:35:00",
                "approved_at": "2026-07-21T09:15:00",
                "trip_info": {"destination": "北京", "days": 2, "reason": "客户拜访"},
                "invoices": [
                    {"invoice_id": "inv_001", "invoice_number": "00123456", "amount": 800.00, "tax": 80.00, "total": 880.00,
                     "date": "2026-07-20", "vendor": "北京XX酒店"},
                    {"invoice_id": "inv_002", "invoice_number": "00123457", "amount": 700.00, "tax": 0.00, "total": 700.00,
                     "date": "2026-07-21", "vendor": "北京YY餐厅"}
                ],
                "approvals": [
                    {"approver_name": "张经理", "approver_id": "user_002", "role": "直属经理",
                     "status": "approved", "approved_at": "2026-07-20T15:30:00", "comment": "同意"},
                    {"approver_name": "李总监", "approver_id": "user_003", "role": "部门总监",
                     "status": "approved", "approved_at": "2026-07-21T09:15:00", "comment": "通过"}
                ]
            },
            "app_002": {
                "application_id": "app_002", "user_id": "user_001", "title": "上海出差报销",
                "user_name": "王小明", "department": "销售部", "position": "销售经理",
                "status": "pending", "total_amount": 2350.00, "invoice_count": 2,
                "created_at": "2026-07-22T14:15:00", "submitted_at": "2026-07-22T14:20:00",
                "approved_at": None,
                "trip_info": {"destination": "上海", "days": 3, "reason": "项目实施"},
                "invoices": [
                    {"invoice_id": "inv_003", "invoice_number": "00234567", "amount": 1200.00, "tax": 120.00, "total": 1320.00,
                     "date": "2026-07-22", "vendor": "上海XX酒店"},
                    {"invoice_id": "inv_004", "invoice_number": "00234568", "amount": 1000.00, "tax": 30.00, "total": 1030.00,
                     "date": "2026-07-23", "vendor": "上海YY交通"}
                ],
                "approvals": [
                    {"approver_name": "张经理", "approver_id": "user_002", "role": "直属经理",
                     "status": "pending", "approved_at": None, "comment": ""}
                ]
            },
            "app_003": {
                "application_id": "app_003", "user_id": "user_001", "title": "深圳出差报销",
                "user_name": "王小明", "department": "销售部", "position": "销售经理",
                "status": "rejected", "total_amount": 3200.00, "invoice_count": 3,
                "created_at": "2026-07-18T09:00:00", "submitted_at": "2026-07-18T09:30:00",
                "approved_at": None,
                "trip_info": {"destination": "深圳", "days": 4, "reason": "技术交流"},
                "invoices": [
                    {"invoice_id": "inv_005", "invoice_number": "00345678", "amount": 1500.00, "tax": 150.00, "total": 1650.00,
                     "date": "2026-07-18", "vendor": "深圳XX酒店"},
                    {"invoice_id": "inv_006", "invoice_number": "00345679", "amount": 800.00, "tax": 80.00, "total": 880.00,
                     "date": "2026-07-19", "vendor": "深圳YY餐厅"},
                    {"invoice_id": "inv_007", "invoice_number": "00345680", "amount": 600.00, "tax": 70.00, "total": 670.00,
                     "date": "2026-07-20", "vendor": "深圳ZZ交通"}
                ],
                "approvals": [
                    {"approver_name": "张经理", "approver_id": "user_002", "role": "直属经理",
                     "status": "rejected", "approved_at": "2026-07-18T16:00:00", "comment": "发票不完整"}
                ]
            }
        }

        if application_id not in mock_details:
            raise HTTPException(status_code=404, detail="报销记录不存在")

        data = mock_details[application_id]

        # 注册中文字体
        font_paths = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/msyh.ttc",
        ]
        font_registered = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('SimHei', font_path))
                    font_registered = True
                    break
                except:
                    continue

        # 创建PDF到内存
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )

        story = []

        # 样式
        title_style = ParagraphStyle(
            'CustomTitle',
            fontName='SimHei' if font_registered else 'Helvetica-Bold',
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=5*mm
        )

        # 标题
        story.append(Paragraph("差旅费报销申请单", title_style))
        story.append(Spacer(1, 10*mm))

        # 基本信息表
        basic_data = [
            ['报销单号', data['application_id'], '申请人', data['user_name']],
            ['所属部门', data['department'], '职位', data['position']],
            ['提交日期', data['submitted_at'][:10], '报销总额', f"¥{data['total_amount']:.2f}"],
            ['申请状态', {'approved': '已通过', 'pending': '审批中', 'rejected': '已驳回'}[data['status']], '', '']
        ]

        basic_table = Table(basic_data, colWidths=[30*mm, 60*mm, 30*mm, 50*mm])
        basic_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'SimHei' if font_registered else 'Helvetica'),
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
        story.append(basic_table)
        story.append(Spacer(1, 5*mm))

        # 出差信息表
        trip_data = [
            ['出差目的地', data['trip_info']['destination']],
            ['出差天数', f"{data['trip_info']['days']}天"],
            ['出差事由', data['trip_info']['reason']]
        ]

        trip_table = Table(trip_data, colWidths=[30*mm, 140*mm])
        trip_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'SimHei' if font_registered else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(trip_table)
        story.append(Spacer(1, 5*mm))

        # 发票明细表
        invoice_data = [['序号', '发票号码', '开票日期', '销售方', '金额', '税额', '合计']]
        for idx, inv in enumerate(data['invoices']):
            invoice_data.append([
                str(idx + 1),
                inv['invoice_number'],
                inv['date'],
                inv['vendor'][:15],
                f"{inv['amount']:.2f}",
                f"{inv['tax']:.2f}",
                f"{inv['total']:.2f}"
            ])

        # 合计行
        total_amount = sum(inv['amount'] for inv in data['invoices'])
        total_tax = sum(inv['tax'] for inv in data['invoices'])
        total_sum = sum(inv['total'] for inv in data['invoices'])
        invoice_data.append(['合计', '', '', '', f"{total_amount:.2f}", f"{total_tax:.2f}", f"{total_sum:.2f}"])

        invoice_table = Table(invoice_data, colWidths=[12*mm, 25*mm, 25*mm, 45*mm, 20*mm, 20*mm, 23*mm])
        invoice_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'SimHei' if font_registered else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(invoice_table)
        story.append(Spacer(1, 5*mm))

        # 审批记录表
        approval_data = [['审批人', '职责', '决策', '审批时间', '意见']]
        for approval in data['approvals']:
            approval_data.append([
                approval['approver_name'],
                approval['role'],
                {'approved': '通过', 'pending': '待审批', 'rejected': '拒绝'}[approval['status']],
                approval['approved_at'][:16] if approval['approved_at'] else '待审批',
                approval['comment'] or '无'
            ])

        approval_table = Table(approval_data, colWidths=[30*mm, 30*mm, 20*mm, 40*mm, 50*mm])
        approval_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'SimHei' if font_registered else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(approval_table)
        story.append(Spacer(1, 10*mm))

        # 页脚
        footer_style = ParagraphStyle(
            'Footer',
            fontName='SimHei' if font_registered else 'Helvetica',
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER
        )
        story.append(Paragraph(
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 系统生成，仅供参考",
            footer_style
        ))

        # 生成PDF
        doc.build(story)
        buffer.seek(0)

        from urllib.parse import quote

        # 使用URL编码处理中文文件名
        filename_encoded = quote(f"报销单-{application_id}.pdf")

        return StreamingResponse(
            buffer,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f"attachment; filename*=UTF-8''{filename_encoded}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 下载PDF失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-approvals")
async def get_my_approvals(
    user_id: str,
    status: Optional[str] = "pending"
):
    """
    我的待审批列表

    - status: pending（待审批）/ approved（已通过）/ rejected（已拒绝）
    - 返回当前用户的审批任务列表
    """
    try:
        # TODO: 实现查询逻辑
        # 查询 reimbursement_approvals WHERE approver_id=user_id AND status=status

        raise HTTPException(
            status_code=501,
            detail="查询功能待实现"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 查询待审批列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feishu/card/callback")
async def handle_feishu_card_callback(request: Request):
    """
    飞书卡片交互回调接口（单级审批）

    - 接收审批人点击卡片按钮的回调
    - 解析操作类型（通过/拒绝）
    - 调用报销服务更新状态
    - 返回Toast提示和更新后的卡片
    """
    try:
        # 读取请求体
        body = await request.body()
        body_str = body.decode('utf-8')

        import json
        callback_data = json.loads(body_str)

        logger.info(f"[API] 收到飞书卡片回调: {json.dumps(callback_data, ensure_ascii=False)}")

        # 提取回调数据
        action = callback_data.get('action', {})
        action_value = action.get('value', {})

        operation = action_value.get('operation')  # "approve" or "reject"
        application_id = action_value.get('approval_id')
        user_id = action_value.get('user_id')

        # 从token中获取审批人ID（飞书用户的open_id）
        open_id = callback_data.get('open_id', 'feishu_approver')

        if not operation or not application_id:
            return {
                "toast": {
                    "type": "error",
                    "content": "缺少必要参数"
                }
            }

        # 调用报销服务处理审批
        decision = "approved" if operation == "approve" else "rejected"

        result = reimbursement_service.approve(
            application_id=application_id,
            approver_id=open_id,
            decision=decision,
            comment="",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )

        if result['success']:
            # 构建更新后的卡片
            status_emoji = "✅" if decision == "approved" else "❌"
            status_text = "已通过" if decision == "approved" else "已拒绝"
            card_color = "green" if decision == "approved" else "red"

            updated_card = {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{status_emoji} 审批{status_text}"
                    },
                    "template": card_color
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": (
                            f"**报销单号**: {application_id}\n"
                            f"**状态**: {status_text}\n"
                            f"**处理时间**: {result.get('approved_at', 'N/A')}"
                        )
                    }
                ]
            }

            return {
                "toast": {
                    "type": "success",
                    "content": f"审批{status_text}"
                },
                "card": updated_card
            }
        else:
            return {
                "toast": {
                    "type": "error",
                    "content": result.get('message', '审批失败')
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 处理飞书卡片回调失败: {e}", exc_info=True)
        return {
            "toast": {
                "type": "error",
                "content": f"处理失败: {str(e)}"
            }
        }


@router.post("/feishu/approval/callback")
async def handle_feishu_callback(
    request: Request,
    x_lark_signature: Optional[str] = Header(None),
    x_lark_request_timestamp: Optional[str] = Header(None),
    x_lark_request_nonce: Optional[str] = Header(None)
):
    """
    飞书审批回调接口

    - 接收飞书审批事件
    - 验证签名
    - 同步审批状态到本地数据库
    """
    try:
        # 读取请求体
        body = await request.body()
        body_str = body.decode('utf-8')

        # 验证签名
        if x_lark_signature and x_lark_request_timestamp and x_lark_request_nonce:
            is_valid = feishu_approval.verify_signature(
                timestamp=x_lark_request_timestamp,
                nonce=x_lark_request_nonce,
                signature=x_lark_signature,
                body=body_str
            )

            if not is_valid:
                raise HTTPException(status_code=401, detail="签名验证失败")

        # 解析事件数据
        import json
        event_data = json.loads(body_str)

        # 处理回调
        event = feishu_approval.handle_callback(event_data)

        if event:
            instance_code = event.get('instance_code')
            status = event.get('status')
            operator_id = event.get('operator_id')
            comment = event.get('comment', '')

            logger.info(
                f"[API] 收到飞书审批回调: "
                f"instance_code={instance_code}, status={status}"
            )

            # TODO: 根据instance_code查询对应的application_id
            # TODO: 调用reimbursement_service.approve()同步状态

            return {"success": True, "message": "回调处理成功"}
        else:
            return {"success": False, "message": "未知事件类型"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 处理飞书回调失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/form-schema")
async def get_form_schema(invoice_ids: str):
    """
    获取报销表单Schema

    - 根据发票ID生成动态表单配置
    - 返回JSON Schema格式
    - 前端使用react-jsonschema-form渲染
    """
    try:
        # 解析发票ID列表
        invoice_id_list = invoice_ids.split(',')

        # TODO: 从数据库查询发票数据
        invoices = []

        # 生成表单Schema
        form_schema = form_generator.generate_form_schema(invoices)

        return form_schema

    except Exception as e:
        logger.error(f"[API] 生成表单Schema失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
