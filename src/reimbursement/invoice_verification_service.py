# -*- coding: utf-8 -*-
"""
发票验真服务

职责：
1. 对接阿里云OCR发票核验API
2. 验证发票真伪
3. 返回统一格式的验证结果

使用阿里云官方SDK：alibabacloud_ocr_api20210707
"""
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class InvoiceVerificationService:
    """
    发票验真服务

    使用阿里云OCR VerifyVATInvoice API
    文档：https://help.aliyun.com/zh/ocr/developer-reference/api-ocr-api-2021-07-07-verifyvatinvoice
    """

    def __init__(self):
        # 阿里云AccessKey配置（用于发票验真）
        self.access_key_id = os.getenv("ALIYUN_ACCESS_KEY_ID")
        self.access_key_secret = os.getenv("ALIYUN_ACCESS_KEY_SECRET")

        if not self.access_key_id or not self.access_key_secret:
            logger.warning(
                "[InvoiceVerification] 阿里云AccessKey未配置 "
                "(需要 ALIYUN_ACCESS_KEY_ID 和 ALIYUN_ACCESS_KEY_SECRET)"
            )

        self._client = None

    def _get_client(self):
        """延迟初始化阿里云SDK客户端"""
        if self._client is None:
            try:
                from alibabacloud_ocr_api20210707.client import Client
                from alibabacloud_tea_openapi import models as open_api_models

                config = open_api_models.Config(
                    access_key_id=self.access_key_id,
                    access_key_secret=self.access_key_secret,
                    endpoint='ocr-api.cn-hangzhou.aliyuncs.com'
                )
                self._client = Client(config)
            except ImportError:
                logger.error("[InvoiceVerification] 请安装阿里云SDK: pip install alibabacloud_ocr_api20210707")
                raise

        return self._client

    def verify_invoice(
        self,
        invoice_number: str,
        invoice_date: str,
        invoice_code: Optional[str] = None,
        invoice_sum: Optional[float] = None,
        verify_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        验证发票真伪

        Args:
            invoice_number: 发票号码（必填）
            invoice_date: 开票日期 YYYY-MM-DD 或 YYYYMMDD（必填）
            invoice_code: 发票代码（数电发票可为空）
            invoice_sum: 发票金额（部分类型必填）
            verify_code: 校验码后6位（部分类型必填）

        Returns:
            {
                "success": bool,
                "status": "verified" | "failed" | "error" | "skipped",
                "message": str,
                "data": {...}  # 验证成功时返回票面信息
            }
        """
        try:
            if not self.access_key_id or not self.access_key_secret:
                return self._error_response(
                    "阿里云AccessKey未配置，请设置 ALIYUN_ACCESS_KEY_ID 和 ALIYUN_ACCESS_KEY_SECRET"
                )

            # 格式化日期为YYYYMMDD
            formatted_date = self._format_date(invoice_date)
            if not formatted_date:
                return self._error_response("日期格式错误，应为YYYY-MM-DD或YYYYMMDD")

            logger.info(
                f"[InvoiceVerification] 开始验证发票: "
                f"号码={invoice_number}, 日期={formatted_date}"
            )

            # 调用阿里云API
            result = self._call_aliyun_api(
                invoice_number=invoice_number,
                invoice_date=formatted_date,
                invoice_code=invoice_code,
                invoice_sum=invoice_sum,
                verify_code=verify_code
            )

            logger.info(
                f"[InvoiceVerification] 验证完成: "
                f"号码={invoice_number}, 状态={result['status']}"
            )

            return result

        except Exception as e:
            logger.error(f"[InvoiceVerification] 验证异常: {e}", exc_info=True)
            return self._error_response(f"验证异常: {str(e)}")

    def _format_date(self, date_str: str) -> Optional[str]:
        """
        格式化日期为YYYYMMDD

        支持输入格式：
        - YYYY-MM-DD
        - YYYYMMDD
        """
        try:
            # 移除所有分隔符
            clean_date = date_str.replace("-", "").replace("/", "").replace(".", "")

            # 验证格式
            if len(clean_date) == 8 and clean_date.isdigit():
                # 验证日期有效性
                datetime.strptime(clean_date, "%Y%m%d")
                return clean_date

            return None

        except Exception:
            return None

    def _call_aliyun_api(
        self,
        invoice_number: str,
        invoice_date: str,
        invoice_code: Optional[str],
        invoice_sum: Optional[float],
        verify_code: Optional[str]
    ) -> Dict[str, Any]:
        """
        调用阿里云OCR API

        使用官方SDK
        """
        try:
            from alibabacloud_ocr_api20210707 import models as ocr_models

            # 获取客户端
            client = self._get_client()

            # 构建请求
            request = ocr_models.VerifyVATInvoiceRequest(
                invoice_no=invoice_number,
                invoice_date=invoice_date
            )

            # 可选参数
            if invoice_code:
                request.invoice_code = invoice_code

            if invoice_sum is not None:
                # 格式化金额为字符串（保留2位小数）
                request.invoice_sum = f"{invoice_sum:.2f}"

            if verify_code:
                # 确保是后6位
                request.verify_code = verify_code[-6:] if len(verify_code) > 6 else verify_code

            # 发送请求
            response = client.verify_vatinvoice(request)

            # 解析响应
            return self._parse_response(response)

        except Exception as e:
            logger.error(f"[InvoiceVerification] API调用失败: {e}", exc_info=True)
            return self._error_response(f"API调用失败: {str(e)}")

    def _parse_response(self, response) -> Dict[str, Any]:
        """
        解析API响应

        响应结构：
        {
            "Data": "{\"code\":\"001\",\"msg\":\"成功\",\"data\":{...}}",
            "RequestId": "xxx"
        }
        """
        try:
            import json

            # 获取响应体的字典表示
            body_dict = response.body.to_map()

            # 解析Data字段
            data_str = body_dict.get("Data", "")
            if not data_str:
                return self._error_response("响应数据为空")

            data_obj = json.loads(data_str)

            # 检查业务状态码
            biz_code = data_obj.get("code")
            biz_msg = data_obj.get("msg", "")
            invoice_data = data_obj.get("data")

            # 成功状态码: 001, 000000
            if biz_code in ["001", "000000"]:
                return {
                    "success": True,
                    "status": "verified",
                    "message": "发票验证通过",
                    "data": invoice_data,
                    "biz_code": biz_code
                }

            # 失败状态码（发票不存在或不一致）
            elif biz_code in ["006", "009", "1005"]:
                return {
                    "success": False,
                    "status": "failed",
                    "message": f"发票验证失败: {biz_msg}",
                    "biz_code": biz_code
                }

            # 其他错误
            else:
                return {
                    "success": False,
                    "status": "error",
                    "message": f"验证异常: {biz_msg} (code={biz_code})",
                    "biz_code": biz_code
                }

        except Exception as e:
            logger.error(f"[InvoiceVerification] 解析响应失败: {e}", exc_info=True)
            return self._error_response(f"解析响应失败: {str(e)}")

    def _error_response(self, message: str) -> Dict[str, Any]:
        """构造错误响应"""
        return {
            "success": False,
            "status": "error",
            "message": message
        }


# 单例实例
_service_instance = None


def get_verification_service() -> InvoiceVerificationService:
    """获取验证服务单例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = InvoiceVerificationService()
    return _service_instance
