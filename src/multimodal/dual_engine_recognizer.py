"""
Dual-Engine Invoice Recognizer
双引擎发票识别器：根据发票版本自动选择识别策略
"""

from typing import Dict, List
from .invoice_classifier import InvoiceVersionClassifier, InvoiceVersion
from .qianfan_invoice_recognizer import QianfanInvoiceRecognizer


class DualEngineInvoiceRecognizer(QianfanInvoiceRecognizer):
    """
    双引擎发票识别器

    解决问题：
    电子发票和老版纸质发票的销售方/购买方位置相反
    - 电子发票：销售方在上半部分，购买方在下半部分
    - 老版发票：购买方在上半部分，销售方在下半部分

    解决方案：
    1. 先用分类器判断发票版本
    2. 根据版本选择对应的Prompt
    3. 调用千帆API识别
    4. 附加版本元数据
    """

    # 电子发票专用Prompt
    ELECTRONIC_PROMPT = """请仔细识别图像中的增值税电子发票（2019年后格式），提取以下字段并输出为严格的JSON格式：

【发票版本特征】
这是**电子发票**（2019年后），标准布局规则：
- 发票代码：20位数字
- 销售方通常在上半部分或左侧
- 购买方通常在下半部分或右侧

【必填字段及识别要点】

1. invoice_code（发票代码）
   - 位置：发票右上角，"发票代码"标签下方
   - 格式：20位连续数字（电子发票特征）
   - 示例："25502000000008817662"

2. invoice_number（发票号码）
   - 位置：发票代码下方，标记为"No"或"发票号码"
   - 格式：8位数字
   - 示例："12271524"

3. date（开票日期）
   - 位置：发票右上角区域
   - 格式：统一输出为 YYYY-MM-DD
   - 原始格式可能是："2025年01月21日"
   - 示例输出："2025-01-21"

4. amount（金额/不含税金额）
   - 位置：发票中部或底部，标签为"金额"或"合计"
   - 格式：浮点数，去掉"￥"符号和千位分隔符
   - 示例：2566198.39

5. tax（税额）
   - 位置：金额旁边，标签为"税额"
   - 格式：浮点数，去掉"￥"符号
   - 示例：333605.79

6. tax_rate（税率）
   - 位置：税额附近，标签为"税率"
   - 格式：转换为小数（13%写成0.13）
   - 示例：0.13

7. total（价税合计）
   - 位置：发票底部，标签为"价税合计"或"合计金额"
   - 格式：浮点数，去掉"￥"符号
   - 验证：必须等于 amount + tax（允许±0.02误差）
   - 示例：2899804.18

8. seller_name（销售方名称）⚠️ 重点
   - 位置：**上半部分**，标签为"销售方"或"销货单位"
   - 识别重点：完整的公司全称，通常包含"有限公司"、"股份有限公司"等
   - 示例："遂宁公路工程有限公司"
   - 注意：不要截断，必须识别完整公司名

9. seller_tax_id（销售方纳税人识别号）
   - 位置：销售方名称正下方，标签为"纳税人识别号"
   - 格式：15-20位连续数字或字母
   - 示例："91510900MA62X1234X"

10. buyer_name（购买方名称）⚠️ 重点
    - 位置：**下半部分**，标签为"购买方"或"购货单位"
    - 识别重点：完整的购买方公司名称
    - 示例："四川川海工程管理咨询有限公司"

11. buyer_tax_id（购买方纳税人识别号）
    - 位置：购买方名称正下方
    - 格式：15-20位连续数字或字母

【输出格式要求】
1. 直接返回JSON对象，不要添加任何解释文字
2. 不要使用markdown代码块（不要```json```）
3. 所有金额字段去掉"￥"、","等符号，只保留数字
4. 日期统一为 YYYY-MM-DD 格式
5. 税率转换为小数（如13%→0.13）
6. 如果某个字段无法识别，返回 null

【输出示例】
{
  "invoice_code": "25502000000008817662",
  "invoice_number": "25502000000008817662",
  "date": "2025-01-21",
  "amount": 2566198.39,
  "tax": 333605.79,
  "tax_rate": 0.13,
  "total": 2899804.18,
  "seller_name": "遂宁公路工程有限公司",
  "seller_tax_id": "91510900MA62X1234X",
  "buyer_name": "四川川海工程管理咨询有限公司",
  "buyer_tax_id": "91510100MA6CXXXX8D"
}

请开始识别并输出JSON："""

    # 老版发票专用Prompt
    OLD_INVOICE_PROMPT = """请仔细识别图像中的老版增值税纸质发票（2018年前格式），提取以下字段并输出为严格的JSON格式：

【发票版本特征】⚠️ 重要
这是**老版纸质发票**（2018年前），布局规则与电子发票**相反**：
- 发票代码：10-12位数字（注意：不是20位）
- **购买方**可能在上半部分
- **销售方**可能在下半部分
- 可能有"地方税务局"或"国家税务局"字样（2018年国地税合并前）

【必填字段及识别要点】

1. invoice_code（发票代码）
   - 位置：发票右上角
   - 格式：10-12位连续数字（老版发票特征）
   - 示例："1120020701"

2. invoice_number（发票号码）
   - 位置：发票代码下方
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
   - 位置：金额旁边，标签为"税额"
   - 格式：浮点数，去掉"￥"符号
   - 示例：507.82

6. tax_rate（税率）
   - 位置：税额附近，标签为"税率"
   - 格式：转换为小数（17%写成0.17）
   - 注意：老版发票可能有17%税率（2018年前）
   - 示例：0.17

7. total（价税合计）
   - 位置：发票底部，标签为"价税合计"
   - 格式：浮点数
   - 验证：必须等于 amount + tax（允许±0.02误差）
   - 示例：3495.00

8. seller_name（销售方名称）⚠️ 特别注意
   - 关键词识别：找到"销售方"、"销货单位"、"开票方"标签
   - 语义判断：销售方 = 开票方 = 销货单位
   - 位置参考：可能在下半部分（与电子发票相反）
   - 识别重点：完整的公司全称
   - 示例："深圳市购机汇网络有限公司"
   - **如果没有明确标签**：
     * 优先根据"销货单位"/"开票方"等语义关键词判断
     * 不要仅依赖位置判断

9. seller_tax_id（销售方纳税人识别号）
   - 关键词：在销售方名称附近，标签为"纳税人识别号"
   - 格式：15-18位连续数字或字母
   - 示例："440300083885931"

10. buyer_name（购买方名称）⚠️ 特别注意
    - 关键词识别：找到"购买方"、"购货单位"、"受票方"标签
    - 语义判断：购买方 = 受票方 = 购货单位
    - 位置参考：可能在上半部分（与电子发票相反）
    - **如果没有明确标签**：
      * 优先根据"购货单位"/"受票方"等语义关键词判断

11. buyer_tax_id（购买方纳税人识别号）
    - 关键词：在购买方名称附近

【识别策略】⚠️ 关键
1. **优先查找标签**："销售方"/"销货单位" vs "购买方"/"购货单位"
2. **语义判断**：
   - 销售方 = 开票方 = 销货单位
   - 购买方 = 受票方 = 购货单位
3. **位置判断**：仅在没有明确标签时使用，且可能与电子发票相反
4. **不确定时**：如果无法区分两个公司名称，根据上下文语义判断

【输出格式要求】
1. 直接返回JSON对象，不要添加任何解释文字
2. 不要使用markdown代码块
3. 所有金额字段去掉符号，只保留数字
4. 日期统一为 YYYY-MM-DD 格式
5. 税率转换为小数
6. 如果某个字段无法识别，返回 null
7. 如果完全无法区分销售方/购买方，两个字段都返回 null

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
  "buyer_name": "某某公司",
  "buyer_tax_id": null
}

请开始识别并输出JSON："""

    def __init__(
        self,
        api_key: str,
        model: str = "qianfan-ocr",
        enable_thinking: bool = True,
        confidence_threshold: float = 0.8
    ):
        """
        初始化双引擎识别器

        Args:
            api_key: 百度千帆 API Key
            model: 模型名称
            enable_thinking: 是否启用思考模式
            confidence_threshold: 置信度阈值
        """
        # 调用父类初始化
        super().__init__(api_key, model, enable_thinking, confidence_threshold)

        # 初始化分类器
        self.classifier = InvoiceVersionClassifier()

    def _build_prompt(self, invoice_version: InvoiceVersion = "electronic") -> str:
        """
        根据发票版本构建Prompt（覆盖父类方法）

        Args:
            invoice_version: 发票版本类型

        Returns:
            对应版本的Prompt
        """
        if invoice_version == "old":
            return self.OLD_INVOICE_PROMPT
        else:
            # 电子发票或unknown时使用电子发票Prompt
            return self.ELECTRONIC_PROMPT

    def recognize(self, invoice_path: str, return_raw: bool = False) -> Dict:
        """
        双引擎识别（覆盖父类方法）

        流程：
        1. 版本分类
        2. 选择Prompt
        3. 调用API
        4. 交叉验证
        5. 附加元数据

        Args:
            invoice_path: 发票图像路径
            return_raw: 是否返回原始API响应

        Returns:
            识别结果，包含额外字段：
            - invoice_version: 发票版本（electronic/old/unknown）
            - engine_type: 使用的引擎类型
            - classification_confidence: 分类置信度
        """
        # Step 1: 版本分类
        classification = self.classifier.get_classification_confidence(invoice_path)
        invoice_version = classification["version"]

        # Step 2: 选择Prompt
        prompt = self._build_prompt(invoice_version)

        # Step 3: 调用千帆API（修改父类的调用逻辑）
        image_base64 = self._encode_image(invoice_path)

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "enable_thinking": self.enable_thinking,
            "temperature": 0.1,
            "max_tokens": 2000
        }

        import requests
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"API 调用失败: {response.status_code} - {response.text}")

        api_response = response.json()

        # Step 4: 解析结果
        result = self._parse_response(api_response)

        # Step 5: 交叉验证
        warnings, base_confidence = self._cross_validate(result)

        # Step 6: 计算综合置信度
        confidence = self._calculate_confidence(result, base_confidence, warnings)

        # Step 7: 构建返回结果（附加元数据）
        output = {
            **result,
            'confidence': round(confidence, 3),
            'warnings': warnings,
            'need_review': confidence < self.confidence_threshold,
            'model': self.model,
            'enable_thinking': self.enable_thinking,
            # 双引擎元数据
            'invoice_version': invoice_version,
            'engine_type': 'electronic' if invoice_version == "electronic" else 'old',
            'classification_confidence': classification['confidence'],
            'classification_evidence': classification['evidence']
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
        批量识别（继承父类，自动使用双引擎）

        Args:
            invoice_paths: 发票路径列表
            save_results: 是否保存结果
            output_dir: 结果保存目录

        Returns:
            识别结果列表
        """
        # 直接调用父类的batch_recognize，它会调用我们覆盖的recognize方法
        return super().batch_recognize(invoice_paths, save_results, output_dir)
