"""
Qianfan-based Invoice Recognition Module
使用百度千帆视觉理解 API 进行发票识别
"""

import os
import base64
import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path


class QianfanInvoiceRecognizer:
    """
    基于百度千帆 API 的发票识别器

    特点：
    1. 端到端识别，无需独立 OCR 步骤
    2. 支持 Layout-as-Thought 机制
    3. 零样本能力强，可能无需微调
    """

    # 标准增值税税率（中国）
    VALID_TAX_RATES = [0.03, 0.06, 0.09, 0.13, 0.17]  # 注意：17%已改为13%，但历史发票可能有17%

    def __init__(
        self,
        api_key: str,
        model: str = "qianfan-ocr",
        enable_thinking: bool = True,
        confidence_threshold: float = 0.8
    ):
        """
        初始化识别器

        Args:
            api_key: 百度千帆 API Key (bce-v3/...)
            model: 模型名称，默认使用 qianfan-ocr
            enable_thinking: 是否启用思考模式（Layout-as-Thought）
            confidence_threshold: 置信度阈值（低于此值需人工复核）
        """
        self.api_key = api_key
        self.model = model
        self.enable_thinking = enable_thinking
        self.confidence_threshold = confidence_threshold
        self.api_url = "https://qianfan.baidubce.com/v2/chat/completions"

    def _encode_image(self, image_path: str) -> str:
        """
        将图像编码为 base64 格式

        Args:
            image_path: 图像文件路径

        Returns:
            data:image/jpeg;base64,... 格式的字符串
        """
        with open(image_path, 'rb') as f:
            image_data = f.read()

        base64_data = base64.b64encode(image_data).decode('utf-8')

        # 判断文件类型
        suffix = Path(image_path).suffix.lower()
        mime_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.pdf': 'application/pdf'
        }.get(suffix, 'image/jpeg')

        return f"data:{mime_type};base64,{base64_data}"

    def _build_prompt(self) -> str:
        """
        构建发票识别的 Prompt

        Returns:
            结构化的 Prompt 字符串
        """
        return """请仔细识别图像中的增值税专用发票，提取以下字段并输出为严格的JSON格式：

【必填字段及识别要点】

1. invoice_code（发票代码）
   - 位置：发票右上角，"发票代码"标签下方
   - 格式：10-12位连续数字
   - 示例："1120020701"

2. invoice_number（发票号码）
   - 位置：发票代码下方，标记为"No"或"发票号码"
   - 格式：8位数字
   - 示例："12271524"

3. date（开票日期）
   - 位置：发票右上角区域
   - 格式：统一输出为 YYYY-MM-DD
   - 原始格式可能是："2016年06月12日"
   - 示例输出："2016-06-12"

4. amount（金额/不含税金额）
   - 位置：发票中部或底部，标签为"金额"或"合计"
   - 格式：浮点数，去掉"￥"符号和千位分隔符
   - 示例：2987.18

5. tax（税额）
   - 位置：金额旁边，标签为"税额"或"税颜"（OCR可能误识别）
   - 格式：浮点数，去掉"￥"符号
   - 示例：507.82

6. tax_rate（税率）
   - 位置：税额附近，标签为"税率"
   - 格式：转换为小数（17%写成0.17，13%写成0.13）
   - 示例：0.17

7. total（价税合计）
   - 位置：发票底部，标签为"价税合计"或"合计金额"
   - 格式：浮点数，去掉"￥"符号
   - 验证：必须等于 amount + tax（允许±0.02误差）
   - 示例：3495.00

8. seller_name（销售方名称）
   - 位置：发票左上方区域，标签为"名称"或"销售方"
   - 识别重点：完整的公司全称，通常包含"有限公司"、"股份有限公司"等
   - 常见格式："XX市XX有限公司"、"XX股份有限公司"
   - 示例："深圳市购机汇网络有限公司"
   - 注意：不要截断，必须识别完整公司名

9. seller_tax_id（销售方纳税人识别号）
   - 位置：销售方名称正下方，标签为"纳税人识别号"
   - 格式：15-18位连续数字或字母
   - 示例："440300083885931"
   - 注意：识别全部字符，不要遗漏

10. buyer_name（购买方名称）
    - 位置：发票右侧或左下方，标签为"购买方"或"名称"
    - 识别重点：完整的购买方公司名称
    - 可能为空或不清晰

【输出格式要求】
1. 直接返回JSON对象，不要添加任何解释文字
2. 不要使用markdown代码块（不要```json```）
3. 所有金额字段去掉"￥"、","等符号，只保留数字
4. 日期统一为 YYYY-MM-DD 格式
5. 税率转换为小数（如17%→0.17）
6. 如果某个字段无法识别，返回 null

【输出示例】
{
  "invoice_code": "1120020701",
  "invoice_number": "12271524",
  "date": "2016-06-12",
  "amount": 2987.18,
  "tax": 507.82,
  "tax_rate": 0.17,
  "total": 3495.00,
  "seller_name": "深圳市购机汇网络有限公司",
  "seller_tax_id": "440300083885931",
  "buyer_name": "某某公司"
}

请开始识别并输出JSON："""

    def _call_api(self, image_path: str) -> Dict:
        """
        调用千帆 API 进行识别

        Args:
            image_path: 图像文件路径

        Returns:
            API 返回的原始结果

        Raises:
            Exception: API 调用失败
        """
        image_base64 = self._encode_image(image_path)
        prompt = self._build_prompt()

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        # 百度千帆API格式：使用正确的Image对象结构
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "image": {
                        "url": image_base64
                    }
                }
            ],
            "temperature": 0.1,
            "max_tokens": 2000
        }

        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"API 调用失败: {response.status_code} - {response.text}")

        return response.json()

    def _parse_response(self, api_response: Dict) -> Dict:
        """
        解析 API 返回的结果

        Args:
            api_response: API 原始返回

        Returns:
            解析后的结构化数据
        """
        try:
            content = api_response['choices'][0]['message']['content']

            # 尝试提取 JSON（去除可能的 markdown 代码块标记）
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]

            result = json.loads(content.strip())
            return result

        except (KeyError, json.JSONDecodeError) as e:
            raise Exception(f"解析 API 响应失败: {str(e)}\n原始内容: {api_response}")

    def _cross_validate(self, result: Dict) -> Tuple[List[str], float]:
        """
        4层交叉验证（复用原有逻辑）

        验证层次：
        1. 数学一致性：amount + tax = total
        2. 日期合理性：不能晚于今天
        3. 税率合法性：必须是标准税率
        4. 字段完整性：关键字段不能为空

        Args:
            result: 识别结果

        Returns:
            (warnings, base_confidence) - 警告列表和基础置信度
        """
        warnings = []
        base_confidence = 1.0

        # 1. 数学一致性检查
        amount = result.get('amount')
        tax = result.get('tax')
        total = result.get('total')

        if amount is not None and tax is not None and total is not None:
            calculated_total = amount + tax
            if abs(calculated_total - total) > 0.02:
                warnings.append(
                    f"金额不一致: {amount} + {tax} = {calculated_total:.2f} != {total}"
                )
                base_confidence *= 0.8

        # 2. 日期合理性检查
        date_str = result.get('date')
        if date_str:
            try:
                invoice_date = datetime.strptime(date_str, '%Y-%m-%d')
                if invoice_date > datetime.now():
                    warnings.append(f"开票日期晚于今天: {date_str}")
                    base_confidence *= 0.7
            except ValueError:
                warnings.append(f"日期格式错误: {date_str}")
                base_confidence *= 0.6

        # 3. 税率合法性检查
        tax_rate = result.get('tax_rate')
        if tax_rate is not None:
            if not any(abs(tax_rate - valid_rate) < 0.001 for valid_rate in self.VALID_TAX_RATES):
                warnings.append(
                    f"非标准税率: {tax_rate*100:.1f}% (标准税率: 3%, 6%, 9%, 13%, 17%)"
                )
                base_confidence *= 0.9

        # 4. 字段完整性检查
        required_fields = ['invoice_code', 'invoice_number', 'date', 'amount', 'tax', 'total']
        missing_fields = [f for f in required_fields if not result.get(f)]
        if missing_fields:
            warnings.append(f"缺失字段: {', '.join(missing_fields)}")
            base_confidence *= (1 - 0.1 * len(missing_fields))

        return warnings, base_confidence

    def _calculate_confidence(self, result: Dict, base_confidence: float, warnings: List[str]) -> float:
        """
        计算综合置信度

        置信度 = 基础置信度 * 50% + 完整性得分 * 30% + 异常惩罚 * 20%

        Args:
            result: 识别结果
            base_confidence: 基础置信度（来自交叉验证）
            warnings: 警告列表

        Returns:
            综合置信度（0-1之间）
        """
        # 字段完整性得分
        all_fields = [
            'invoice_code', 'invoice_number', 'date',
            'amount', 'tax', 'tax_rate', 'total',
            'seller_name', 'seller_tax_id', 'buyer_name'
        ]
        completeness = sum(1 for f in all_fields if result.get(f) is not None) / len(all_fields)

        # 异常惩罚
        warnings_penalty = max(0, 1 - 0.1 * len(warnings))

        # 加权综合
        confidence = (
            base_confidence * 0.5 +
            completeness * 0.3 +
            warnings_penalty * 0.2
        )

        return min(1.0, max(0.0, confidence))

    def recognize(self, invoice_path: str, return_raw: bool = False) -> Dict:
        """
        识别发票

        Args:
            invoice_path: 发票图像路径
            return_raw: 是否返回原始 API 响应

        Returns:
            识别结果字典，包含：
            - 所有发票字段
            - confidence: 置信度（0-1）
            - warnings: 警告列表
            - need_review: 是否需要人工复核
            - raw_response: 原始 API 响应（如果 return_raw=True）
        """
        # 调用 API
        api_response = self._call_api(invoice_path)

        # 解析结果
        result = self._parse_response(api_response)

        # 交叉验证
        warnings, base_confidence = self._cross_validate(result)

        # 计算综合置信度
        confidence = self._calculate_confidence(result, base_confidence, warnings)

        # 构建返回结果
        output = {
            **result,
            'confidence': round(confidence, 3),
            'warnings': warnings,
            'need_review': confidence < self.confidence_threshold,
            'model': self.model,
            'enable_thinking': self.enable_thinking
        }

        if return_raw:
            output['raw_response'] = api_response

        return output

    def batch_recognize(
        self,
        invoice_paths: List[str],
        save_results: bool = True,
        output_dir: str = "results"
    ) -> List[Dict]:
        """
        批量识别发票

        Args:
            invoice_paths: 发票图像路径列表
            save_results: 是否保存结果到文件
            output_dir: 结果保存目录

        Returns:
            识别结果列表
        """
        results = []

        for i, invoice_path in enumerate(invoice_paths, 1):
            print(f"\n[{i}/{len(invoice_paths)}] 识别: {invoice_path}")

            try:
                result = self.recognize(invoice_path)
                result['file_path'] = invoice_path
                results.append(result)

                # 打印摘要
                status = "需复核" if result['need_review'] else "通过"
                print(f"  状态: {status} (置信度: {result['confidence']:.3f})")
                if result['warnings']:
                    print(f"  警告: {len(result['warnings'])} 个")
                    for warning in result['warnings']:
                        print(f"    - {warning}")

            except Exception as e:
                print(f"  错误: {str(e)}")
                results.append({
                    'file_path': invoice_path,
                    'error': str(e),
                    'confidence': 0.0,
                    'need_review': True
                })

        # 保存结果
        if save_results:
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = os.path.join(output_dir, f"recognition_results_{timestamp}.json")

            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"\n结果已保存到: {result_file}")

        return results

    def calculate_accuracy(
        self,
        results: List[Dict],
        ground_truth: Dict[str, Dict]
    ) -> Dict:
        """
        计算识别准确率

        Args:
            results: 识别结果列表
            ground_truth: 真实标注 {filename: {field: value}}

        Returns:
            准确率统计
        """
        field_names = [
            'invoice_code', 'invoice_number', 'date',
            'amount', 'tax', 'total', 'tax_rate',
            'seller_name', 'seller_tax_id', 'buyer_name'
        ]

        field_correct = {f: 0 for f in field_names}
        field_total = {f: 0 for f in field_names}
        total_exact_match = 0

        for result in results:
            if 'error' in result:
                continue

            filename = Path(result['file_path']).name
            if filename not in ground_truth:
                continue

            gt = ground_truth[filename]
            all_match = True

            for field in field_names:
                if field in gt:
                    field_total[field] += 1
                    pred_value = result.get(field)
                    true_value = gt[field]

                    # 数值比较（允许小误差）
                    if isinstance(true_value, (int, float)) and isinstance(pred_value, (int, float)):
                        if abs(pred_value - true_value) < 0.02:
                            field_correct[field] += 1
                        else:
                            all_match = False
                    # 字符串比较
                    elif str(pred_value).strip() == str(true_value).strip():
                        field_correct[field] += 1
                    else:
                        all_match = False

            if all_match:
                total_exact_match += 1

        # 计算准确率
        field_accuracy = {}
        for field in field_names:
            if field_total[field] > 0:
                field_accuracy[field] = field_correct[field] / field_total[field]

        total_samples = len([r for r in results if 'error' not in r and Path(r['file_path']).name in ground_truth])
        exact_match_rate = total_exact_match / total_samples if total_samples > 0 else 0

        return {
            'field_accuracy': field_accuracy,
            'average_accuracy': sum(field_accuracy.values()) / len(field_accuracy) if field_accuracy else 0,
            'exact_match_rate': exact_match_rate,
            'total_samples': total_samples
        }
