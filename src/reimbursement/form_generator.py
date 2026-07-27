# -*- coding: utf-8 -*-
"""
报销表单生成器 - 基于JSON Schema标准

职责：
根据发票OCR结果生成动态表单Schema，支持前端渲染
兼容 react-jsonschema-form 和 vue-json-schema-form
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ReimbursementFormGenerator:
    """
    报销表单生成器

    生成符合JSON Schema标准的动态表单配置
    """

    def generate_form_schema(
        self,
        invoices: List[Dict[str, Any]],
        user_info: Optional[Dict[str, Any]] = None,
        pre_fill: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成报销表单Schema

        Args:
            invoices: 发票列表（来自OCR识别）
            user_info: 用户信息（可选）
            pre_fill: 预填充数据（可选）

        Returns:
            JSON Schema格式的表单配置
        """
        # 计算总金额
        total_amount = sum(invoice.get('total', 0) for invoice in invoices)

        # 生成默认标题
        default_title = self._generate_default_title(invoices)

        # 构建表单Schema
        schema = {
            "title": "差旅费报销申请表",
            "description": "内江嘉宏城建集团有限公司",
            "type": "object",
            "required": ["title", "trip_destination", "trip_days"],
            "properties": {
                "title": {
                    "type": "string",
                    "title": "报销标题",
                    "description": "简要描述本次报销事由",
                    "default": pre_fill.get('title') if pre_fill else default_title,
                    "minLength": 5,
                    "maxLength": 100
                },
                "trip_destination": {
                    "type": "string",
                    "title": "出差目的地",
                    "description": "填写具体城市或地区",
                    "default": pre_fill.get('trip_destination') if pre_fill else "",
                    "examples": ["北京市", "上海市浦东新区", "成都市高新区"]
                },
                "trip_days": {
                    "type": "integer",
                    "title": "出差天数",
                    "description": "实际出差天数（含出发和返回日期）",
                    "default": pre_fill.get('trip_days') if pre_fill else 1,
                    "minimum": 1,
                    "maximum": 365
                },
                "trip_purpose": {
                    "type": "string",
                    "title": "出差事由",
                    "description": "详细说明出差目的和任务",
                    "default": pre_fill.get('trip_purpose') if pre_fill else "",
                    "maxLength": 500
                },
                "invoices": {
                    "type": "array",
                    "title": "发票明细",
                    "description": "已识别的发票信息，请核对无误",
                    "items": {
                        "type": "object",
                        "properties": {
                            "invoice_code": {
                                "type": "string",
                                "title": "发票代码"
                            },
                            "invoice_number": {
                                "type": "string",
                                "title": "发票号码"
                            },
                            "invoice_date": {
                                "type": "string",
                                "title": "开票日期",
                                "format": "date"
                            },
                            "seller_name": {
                                "type": "string",
                                "title": "销售方名称"
                            },
                            "invoice_type": {
                                "type": "string",
                                "title": "发票类型"
                            },
                            "amount": {
                                "type": "number",
                                "title": "金额（不含税）",
                                "minimum": 0
                            },
                            "tax": {
                                "type": "number",
                                "title": "税额",
                                "minimum": 0
                            },
                            "total": {
                                "type": "number",
                                "title": "价税合计",
                                "minimum": 0
                            },
                            "confidence": {
                                "type": "number",
                                "title": "识别置信度",
                                "minimum": 0,
                                "maximum": 1
                            },
                            "need_manual_review": {
                                "type": "boolean",
                                "title": "需人工复核"
                            }
                        }
                    },
                    "default": invoices,
                    "minItems": 1
                },
                "total_amount": {
                    "type": "number",
                    "title": "报销总额（元）",
                    "description": "所有发票金额合计",
                    "default": total_amount,
                    "readOnly": True,
                    "minimum": 0
                },
                "remarks": {
                    "type": "string",
                    "title": "备注说明",
                    "description": "其他需要说明的事项（可选）",
                    "default": pre_fill.get('remarks') if pre_fill else "",
                    "maxLength": 1000
                }
            }
        }

        # 构建UI Schema（前端渲染配置）
        ui_schema = {
            "title": {
                "ui:placeholder": "例如：2026年7月北京技术交流差旅报销",
                "ui:help": "建议格式：年月+地点+事由"
            },
            "trip_destination": {
                "ui:placeholder": "例如：北京市海淀区",
                "ui:widget": "text"
            },
            "trip_days": {
                "ui:widget": "updown"
            },
            "trip_purpose": {
                "ui:widget": "textarea",
                "ui:placeholder": "例如：参加公司技术交流会，学习先进管理经验",
                "ui:options": {
                    "rows": 3
                }
            },
            "invoices": {
                "ui:options": {
                    "orderable": False,
                    "removable": True,
                    "addable": False
                },
                "items": {
                    "ui:options": {
                        "inline": True
                    },
                    "invoice_code": {
                        "ui:readonly": True
                    },
                    "invoice_number": {
                        "ui:readonly": True
                    },
                    "invoice_date": {
                        "ui:readonly": True
                    },
                    "seller_name": {
                        "ui:readonly": True
                    },
                    "invoice_type": {
                        "ui:readonly": True
                    },
                    "amount": {
                        "ui:readonly": True,
                        "ui:widget": "text"
                    },
                    "tax": {
                        "ui:readonly": True,
                        "ui:widget": "text"
                    },
                    "total": {
                        "ui:readonly": True,
                        "ui:widget": "text"
                    },
                    "confidence": {
                        "ui:readonly": True,
                        "ui:widget": "range"
                    },
                    "need_manual_review": {
                        "ui:readonly": True,
                        "ui:widget": "checkbox"
                    }
                }
            },
            "total_amount": {
                "ui:readonly": True,
                "ui:widget": "text",
                "ui:options": {
                    "style": {
                        "fontSize": "18px",
                        "fontWeight": "bold",
                        "color": "#f56c6c"
                    }
                }
            },
            "remarks": {
                "ui:widget": "textarea",
                "ui:placeholder": "如有超标费用或特殊情况，请在此说明",
                "ui:options": {
                    "rows": 4
                }
            }
        }

        # 表单数据（用于预填充）
        form_data = {
            "title": default_title if not pre_fill else pre_fill.get('title', default_title),
            "trip_destination": pre_fill.get('trip_destination', '') if pre_fill else '',
            "trip_days": pre_fill.get('trip_days', 1) if pre_fill else 1,
            "trip_purpose": pre_fill.get('trip_purpose', '') if pre_fill else '',
            "invoices": invoices,
            "total_amount": total_amount,
            "remarks": pre_fill.get('remarks', '') if pre_fill else ''
        }

        # 生成验证警告
        warnings = self._generate_validation_warnings(invoices)

        logger.info(
            f"[FormGenerator] 表单Schema生成成功: "
            f"发票数={len(invoices)}, 总额=¥{total_amount:.2f}, "
            f"警告数={len(warnings)}"
        )

        return {
            "schema": schema,
            "uiSchema": ui_schema,
            "formData": form_data,
            "warnings": warnings,
            "meta": {
                "invoice_count": len(invoices),
                "total_amount": total_amount,
                "generated_at": datetime.now().isoformat(),
                "needs_review": any(inv.get('need_manual_review', False) for inv in invoices)
            }
        }

    def _generate_default_title(self, invoices: List[Dict[str, Any]]) -> str:
        """
        生成默认报销标题

        策略：
        1. 提取发票中的销售方名称
        2. 如果是交通/住宿类，识别地点
        3. 格式：年月+地点/类型+差旅报销
        """
        current_date = datetime.now()
        year_month = current_date.strftime('%Y年%m月')

        if not invoices:
            return f"{year_month}差旅费报销"

        # 简单策略：使用第一张发票的销售方
        first_invoice = invoices[0]
        seller_name = first_invoice.get('seller_name', '')

        # 提取关键词
        keywords = []
        if '航空' in seller_name or '机票' in seller_name:
            keywords.append('机票')
        if '酒店' in seller_name or '住宿' in seller_name:
            keywords.append('住宿')
        if '铁路' in seller_name or '高铁' in seller_name:
            keywords.append('高铁')
        if '出租' in seller_name or '网约' in seller_name:
            keywords.append('交通')

        if keywords:
            category = '+'.join(keywords[:2])
            return f"{year_month}{category}差旅报销"
        else:
            return f"{year_month}差旅费报销"

    def _generate_validation_warnings(self, invoices: List[Dict[str, Any]]) -> List[str]:
        """
        生成表单验证警告

        检查项：
        1. 发票识别置信度低
        2. 发票重复
        3. 发票日期异常
        4. 金额异常
        """
        warnings = []

        for idx, invoice in enumerate(invoices):
            invoice_num = idx + 1

            # 1. 检查置信度
            confidence = invoice.get('confidence', 1.0)
            if confidence < 0.8:
                warnings.append(
                    f"发票{invoice_num}识别置信度较低（{confidence:.1%}），建议人工复核"
                )

            # 2. 检查是否重复
            if invoice.get('is_duplicate'):
                warnings.append(
                    f"发票{invoice_num}可能已报销过，请确认是否重复"
                )

            # 3. 检查发票日期
            invoice_date_str = invoice.get('invoice_date')
            if invoice_date_str:
                try:
                    invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d')
                    days_ago = (datetime.now() - invoice_date).days

                    if days_ago > 180:
                        warnings.append(
                            f"发票{invoice_num}开票日期超过6个月（{days_ago}天前），可能超过报销期限"
                        )
                    elif days_ago < 0:
                        warnings.append(
                            f"发票{invoice_num}开票日期异常（未来日期），请核对"
                        )
                except ValueError:
                    warnings.append(
                        f"发票{invoice_num}开票日期格式异常"
                    )

            # 4. 检查金额异常
            total = invoice.get('total', 0)
            if total <= 0:
                warnings.append(
                    f"发票{invoice_num}金额异常（¥{total}），请核对"
                )
            elif total > 20000:
                warnings.append(
                    f"发票{invoice_num}金额较大（¥{total:.2f}），将进入高级审批流程"
                )

        return warnings

    def validate_form_data(self, form_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        验证表单数据

        Args:
            form_data: 表单数据

        Returns:
            (是否通过, 错误列表)
        """
        errors = []

        # 1. 必填字段检查
        required_fields = ['title', 'trip_destination', 'trip_days']
        for field in required_fields:
            if not form_data.get(field):
                errors.append(f"必填字段缺失: {field}")

        # 2. 标题长度检查
        title = form_data.get('title', '')
        if len(title) < 5:
            errors.append("报销标题至少5个字符")
        elif len(title) > 100:
            errors.append("报销标题不能超过100个字符")

        # 3. 出差天数检查
        trip_days = form_data.get('trip_days', 0)
        if not isinstance(trip_days, int) or trip_days < 1:
            errors.append("出差天数必须为正整数")
        elif trip_days > 365:
            errors.append("出差天数不能超过365天")

        # 4. 发票检查
        invoices = form_data.get('invoices', [])
        if not invoices:
            errors.append("至少需要一张发票")
        elif len(invoices) > 50:
            errors.append("单次报销发票数量不能超过50张")

        # 5. 总金额检查
        total_amount = form_data.get('total_amount', 0)
        if total_amount <= 0:
            errors.append("报销总额必须大于0")

        is_valid = len(errors) == 0

        if is_valid:
            logger.info("[FormGenerator] 表单验证通过")
        else:
            logger.warning(f"[FormGenerator] 表单验证失败: {errors}")

        return is_valid, errors

    def generate_approval_preview(
        self,
        form_data: Dict[str, Any],
        chain_config: Dict[str, Any]
    ) -> str:
        """
        生成审批预览文本

        Args:
            form_data: 表单数据
            chain_config: 审批链配置

        Returns:
            Markdown格式的预览文本
        """
        preview = f"""
## 报销申请预览

**报销标题**: {form_data.get('title', 'N/A')}
**出差目的地**: {form_data.get('trip_destination', 'N/A')}
**出差天数**: {form_data.get('trip_days', 0)}天
**出差事由**: {form_data.get('trip_purpose', '无')}

---

### 发票明细

"""
        invoices = form_data.get('invoices', [])
        for idx, invoice in enumerate(invoices):
            preview += f"""
**发票 {idx + 1}**
- 发票代码: {invoice.get('invoice_code', 'N/A')}
- 发票号码: {invoice.get('invoice_number', 'N/A')}
- 开票日期: {invoice.get('invoice_date', 'N/A')}
- 销售方: {invoice.get('seller_name', 'N/A')}
- 金额: ¥{invoice.get('total', 0):.2f}
"""

        preview += f"""
---

**报销总额**: ¥{form_data.get('total_amount', 0):.2f}

---

### 审批流程

**审批规则**: {chain_config.get('rule_name', 'N/A')}
**审批模式**: {chain_config.get('approval_mode', 'sequential')}
**审批层级**: {chain_config.get('total_nodes', 0)}级

"""

        approval_chain = chain_config.get('approval_chain', [])
        for node in approval_chain:
            level = node.get('level', 0)
            role = node.get('role', 'N/A')
            timeout_hours = node.get('timeout_hours', 24)

            preview += f"- 第{level}级: {role} (超时时间: {timeout_hours}小时)\n"

        if form_data.get('remarks'):
            preview += f"""
---

### 备注说明

{form_data.get('remarks')}
"""

        return preview.strip()
