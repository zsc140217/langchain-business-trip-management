# src/multimodal/invoice_recognizer.py
import os
# 禁用OneDNN以避免PaddlePaddle兼容性问题
os.environ['PADDLE_DISABLE_ONEDNN'] = '1'

from paddleocr import PaddleOCR
from transformers import LayoutLMv3ForTokenClassification, LayoutLMv3Processor
import torch
from typing import Dict, List, Tuple
from PIL import Image
import datetime


class AdvancedInvoiceRecognizer:
    """
    进阶发票识别器 - 两阶段架构

    特点:
    1. OCR前置 (快速文本提取)
    2. LayoutLMv3 (多模态理解)
    3. 交叉验证 (置信度评分)
    """

    def __init__(self, model_path: str = "microsoft/layoutlmv3-base-chinese"):
        # Stage 1: OCR引擎 (新版PaddleOCR移除了use_gpu参数)
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')

        # Stage 2: LayoutLM模型
        self.processor = LayoutLMv3Processor.from_pretrained(model_path)
        self.model = LayoutLMv3ForTokenClassification.from_pretrained(model_path)
        self.model.eval()

        # BIO标签映射
        self.id2label = {
            0: "O",           # Other
            1: "B-CODE",      # 发票代码开始
            2: "I-CODE",      # 发票代码中间
            3: "B-NUMBER",    # 发票号码
            4: "I-NUMBER",
            5: "B-DATE",      # 开票日期
            6: "I-DATE",
            7: "B-AMOUNT",    # 金额
            8: "I-AMOUNT",
            9: "B-TAX",       # 税额
            10: "I-TAX",
            11: "B-TOTAL",    # 价税合计
            12: "I-TOTAL",
            13: "B-SELLER",   # 销售方
            14: "I-SELLER",
            15: "B-BUYER",    # 购买方
            16: "I-BUYER"
        }

    def recognize(self, invoice_path: str) -> Dict:
        """
        识别发票并返回结构化数据

        Returns:
            {
                "type": "增值税专用发票",
                "code": "112002070106",
                "number": "12921503",
                "date": "2026-07-15",
                "amount": 1234.56,
                "tax": 123.45,
                "total": 1358.01,
                "seller": "XX公司",
                "buyer": "内江嘉宏城建集团",
                "confidence": 0.92,
                "warnings": []
            }
        """
        # Stage 1: OCR提取 (新版PaddleOCR移除了cls参数)
        ocr_result = self.ocr.ocr(invoice_path)
        text, bboxes = self._parse_ocr_result(ocr_result)

        # Stage 2: LayoutLM结构化提取
        structured_data = self._extract_with_layoutlm(
            image_path=invoice_path,
            text=text,
            bboxes=bboxes
        )

        # Stage 3: 交叉验证
        validated = self._cross_validate(text, structured_data)

        # Stage 4: 置信度评分
        validated['confidence'] = self._calculate_confidence(validated)

        return validated

    def _parse_ocr_result(self, ocr_result: List) -> Tuple[str, List]:
        """
        解析OCR结果，提取文本和边界框

        Returns:
            text: 拼接的全文
            bboxes: 归一化的边界框坐标 [[x1,y1,x2,y2], ...]
        """
        text_list = []
        bboxes = []

        if not ocr_result or not ocr_result[0]:
            return "", []

        for line in ocr_result[0]:
            bbox = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            text = line[1][0]  # 文本内容
            conf = line[1][1]  # OCR置信度

            if conf > 0.5:  # 过滤低置信度结果
                text_list.append(text)
                # 转换为 [x1, y1, x2, y2] 格式
                x1 = min(p[0] for p in bbox)
                y1 = min(p[1] for p in bbox)
                x2 = max(p[0] for p in bbox)
                y2 = max(p[1] for p in bbox)
                bboxes.append([x1, y1, x2, y2])

        full_text = ' '.join(text_list)
        return full_text, bboxes

    def _extract_with_layoutlm(self, image_path: str, text: str, bboxes: List) -> Dict:
        """
        使用LayoutLM提取结构化字段

        Args:
            image_path: 图片路径
            text: OCR文本
            bboxes: 边界框列表

        Returns:
            结构化字段字典
        """
        # 加载图像
        image = Image.open(image_path).convert("RGB")

        # 分词并对齐边界框
        words = text.split()
        if len(words) > len(bboxes):
            words = words[:len(bboxes)]
        elif len(words) < len(bboxes):
            bboxes = bboxes[:len(words)]

        if not words:
            return {}

        # 归一化边界框到0-1000范围（LayoutLM要求）
        width, height = image.size
        normalized_boxes = []
        for box in bboxes:
            normalized_boxes.append([
                int(box[0] / width * 1000),
                int(box[1] / height * 1000),
                int(box[2] / width * 1000),
                int(box[3] / height * 1000)
            ])

        # 准备输入
        encoding = self.processor(
            image,
            words,
            boxes=normalized_boxes,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=512
        )

        # 推理
        with torch.no_grad():
            outputs = self.model(**encoding)
            predictions = outputs.logits.argmax(-1).squeeze().tolist()

        # 处理单个预测的情况
        if isinstance(predictions, int):
            predictions = [predictions]

        # 解析BIO标签
        result = self._parse_bio_labels(words, predictions)

        return result

    def _parse_bio_labels(self, words: List[str], predictions: List[int]) -> Dict:
        """
        将BIO标签序列转换为结构化字段

        Args:
            words: 词列表
            predictions: 预测的标签ID列表

        Returns:
            结构化字段 {"code": "...", "number": "...", ...}
        """
        result = {}
        current_field = None
        current_value = []

        for word, pred_id in zip(words, predictions):
            label = self.id2label.get(pred_id, "O")

            if label.startswith("B-"):
                # 开始新字段
                if current_field and current_value:
                    result[current_field] = ''.join(current_value)

                current_field = label[2:].lower()
                current_value = [word]

            elif label.startswith("I-"):
                # 继续当前字段
                if current_field:
                    current_value.append(word)

            else:
                # O标签，结束当前字段
                if current_field and current_value:
                    result[current_field] = ''.join(current_value)
                    current_field = None
                    current_value = []

        # 处理最后一个字段
        if current_field and current_value:
            result[current_field] = ''.join(current_value)

        # 类型转换
        for field in ['amount', 'tax', 'total']:
            if field in result:
                try:
                    # 清理金额字符串
                    value_str = result[field].replace(',', '').replace('￥', '').replace('¥', '').strip()
                    result[field] = float(value_str)
                except:
                    pass

        return result

    def _cross_validate(self, ocr_text: str, llm_result: Dict) -> Dict:
        """
        交叉验证（面试亮点）

        4层校验:
        1. 价税合计一致性
        2. OCR文本包含性
        3. 日期合理性
        4. 税率合理性
        """
        warnings = []
        confidence = 1.0

        # 1. 价税合计一致性
        if all(k in llm_result for k in ['amount', 'tax', 'total']):
            calculated = llm_result['amount'] + llm_result['tax']
            actual = llm_result['total']
            if abs(calculated - actual) > 0.02:
                warnings.append(f'价税合计不符: 计算{calculated:.2f}, 实际{actual:.2f}')
                confidence *= 0.7

        # 2. OCR文本包含性
        key_fields = ['code', 'number']
        for field in key_fields:
            if field in llm_result and str(llm_result[field]) not in ocr_text:
                warnings.append(f'{field}未在OCR结果中找到')
                confidence *= 0.85

        # 3. 日期合理性
        if 'date' in llm_result:
            try:
                invoice_date = datetime.datetime.strptime(llm_result['date'], '%Y-%m-%d')
                if invoice_date > datetime.datetime.now():
                    warnings.append('开票日期晚于当前日期')
                    confidence *= 0.6
            except:
                warnings.append('日期格式错误')
                confidence *= 0.8

        # 4. 税率合理性
        if 'amount' in llm_result and 'tax' in llm_result and llm_result['amount'] > 0:
            tax_rate = llm_result['tax'] / llm_result['amount']
            valid_rates = [0.03, 0.06, 0.09, 0.13]
            if not any(abs(tax_rate - rate) < 0.005 for rate in valid_rates):
                warnings.append(f'税率异常: {tax_rate:.2%}')
                confidence *= 0.8

        llm_result['warnings'] = warnings
        llm_result['base_confidence'] = confidence
        return llm_result

    def _calculate_confidence(self, result: Dict) -> float:
        """
        置信度评分机制（面试亮点）

        综合考虑:
        - 基础置信度 (交叉验证得分)
        - 字段完整性
        - 异常数量
        """
        base_conf = result.get('base_confidence', 1.0)

        # 字段完整性
        required_fields = ['code', 'number', 'date', 'amount']
        filled = sum(1 for f in required_fields if result.get(f))
        completeness = filled / len(required_fields)

        # 异常惩罚
        warnings_penalty = max(0, 1 - len(result.get('warnings', [])) * 0.1)

        # 加权平均
        final_score = (
            base_conf * 0.5 +
            completeness * 0.3 +
            warnings_penalty * 0.2
        )

        return round(final_score, 3)
