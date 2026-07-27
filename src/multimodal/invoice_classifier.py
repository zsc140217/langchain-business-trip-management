"""
Invoice Version Classifier
发票版本分类器：区分电子发票和老版纸质发票
"""

import re
from pathlib import Path
from typing import Dict, Literal, Optional
from datetime import datetime

InvoiceVersion = Literal["electronic", "old", "unknown"]


class InvoiceVersionClassifier:
    """
    零成本发票版本分类器

    通过三级决策快速判断发票类型：
    - Level 1: 文件名匹配（0ms，准确率95%+）
    - Level 2: OCR预览结果判断（0ms额外开销，准确率90%+）
    - Level 3: 兜底返回unknown

    为什么需要分类？
    电子发票和老版发票的销售方/购买方位置是相反的，
    使用统一Prompt会导致其中一种识别错误。
    """

    # 特征规则
    OLD_INVOICE_PATTERNS = {
        "old_invoice_code_length": [10, 11, 12],  # 老版发票代码10-12位
        "old_date_range": (2010, 2018),           # 2018年前
        "old_keywords": ["地方税务局", "国家税务局"],  # 国地税分立时期
    }

    ELECTRONIC_PATTERNS = {
        "electronic_code_length": 20,              # 电子发票代码20位
        "electronic_keywords": ["国家税务总局", "电子发票", "增值税电子"],
        "new_date_range": (2019, 2030),            # 2019年后
    }

    def classify_by_metadata(self, filename: str) -> InvoiceVersion:
        """
        Level 1: 通过文件名推断（最快）

        Args:
            filename: 文件名

        Returns:
            发票版本类型
        """
        filename_lower = filename.lower()

        # 明确标记
        if "dzfp" in filename_lower or "电子发票" in filename_lower or "电子" in filename_lower:
            return "electronic"

        if "old" in filename_lower or "老版" in filename_lower or "纸质" in filename_lower:
            return "old"

        # 年份判断
        year_pattern = r'(20\d{2})'
        years = re.findall(year_pattern, filename)
        if years:
            year = int(years[0])
            if year <= 2018:
                return "old"
            elif year >= 2019:
                return "electronic"

        return "unknown"

    def classify_by_ocr_preview(self, ocr_result: Dict) -> InvoiceVersion:
        """
        Level 2: 通过OCR初步结果判断（较快）

        Args:
            ocr_result: OCR识别的初步结果

        Returns:
            发票版本类型
        """
        # 检查发票代码格式
        invoice_code = ocr_result.get("invoice_code", "")
        if invoice_code:
            code_len = len(str(invoice_code).replace(" ", ""))
            if code_len == 20:
                return "electronic"  # 电子发票20位
            elif code_len in [10, 11, 12]:
                return "old"         # 老版10-12位

        # 检查日期
        date_str = ocr_result.get("date", "")
        if date_str:
            try:
                # 尝试解析日期
                if len(date_str) >= 4:
                    year = int(date_str[:4])
                    if 2010 <= year <= 2018:
                        return "old"
                    elif year >= 2019:
                        return "electronic"
            except (ValueError, TypeError):
                pass

        # 检查关键词（通过原始文本或字段内容）
        raw_text = str(ocr_result).lower()

        # 电子发票关键词
        if any(keyword in raw_text for keyword in ["电子发票", "增值税电子", "国家税务总局"]):
            return "electronic"

        # 老版发票关键词（国地税分立时期）
        if any(keyword in raw_text for keyword in ["地方税务局", "国家税务局"]):
            return "old"

        return "unknown"

    def classify(self,
                 image_path: str,
                 ocr_preview: Optional[Dict] = None) -> InvoiceVersion:
        """
        综合分类（三级决策）

        Args:
            image_path: 发票图片路径
            ocr_preview: OCR初步结果（可选，如已有则复用）

        Returns:
            发票版本类型：
            - "electronic": 电子发票（2019年后，20位代码）
            - "old": 老版纸质发票（2018年前，10-12位代码）
            - "unknown": 无法判断（使用电子发票Prompt作为兜底）
        """
        # Level 1: 文件名（0ms）
        filename = Path(image_path).name
        result = self.classify_by_metadata(filename)
        if result != "unknown":
            return result

        # Level 2: OCR初步结果（如果已有）
        if ocr_preview:
            result = self.classify_by_ocr_preview(ocr_preview)
            if result != "unknown":
                return result

        # Level 3: 兜底返回unknown（由后续流程处理）
        return "unknown"

    def get_classification_confidence(self,
                                     image_path: str,
                                     ocr_preview: Optional[Dict] = None) -> Dict:
        """
        获取分类结果及置信度

        Args:
            image_path: 发票图片路径
            ocr_preview: OCR初步结果

        Returns:
            {
                "version": "electronic" | "old" | "unknown",
                "confidence": 0.0-1.0,
                "evidence": ["判断依据1", "判断依据2"]
            }
        """
        evidence = []
        confidence = 0.0

        filename = Path(image_path).name

        # 检查文件名
        filename_result = self.classify_by_metadata(filename)
        if filename_result != "unknown":
            evidence.append(f"文件名匹配: {filename}")
            confidence += 0.5

        # 检查OCR结果
        if ocr_preview:
            ocr_result = self.classify_by_ocr_preview(ocr_preview)
            if ocr_result != "unknown":
                if ocr_result == filename_result or filename_result == "unknown":
                    evidence.append(f"OCR特征匹配: 发票代码/日期/关键词")
                    confidence += 0.5
                else:
                    evidence.append(f"⚠️ OCR结果({ocr_result})与文件名({filename_result})不一致")
                    confidence = 0.3  # 降低置信度

        # 最终分类
        version = self.classify(image_path, ocr_preview)

        return {
            "version": version,
            "confidence": min(1.0, confidence),
            "evidence": evidence
        }
