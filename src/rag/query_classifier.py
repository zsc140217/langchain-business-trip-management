"""
查询分类器模块

使用LLM判断用户查询类型，决定是否需要检索知识库

分类类型：
- FACTUAL: 需要检索知识库的事实性查询（政策、数值、流程等）
- CHITCHAT: 不需要检索的闲聊查询（问候、通用知识、系统功能等）
"""
from langchain_core.messages import HumanMessage, SystemMessage
from src.models.llm import get_llm
import json
import re


class QueryClassifier:
    """
    查询分类器

    使用LLM判断查询类型，支持：
    - FACTUAL: 事实性查询，需要检索（政策、数值、流程、地点相关）
    - CHITCHAT: 闲聊查询，直接回答（问候、通用知识、功能说明）
    """

    def __init__(self, llm=None, temperature=0.1):
        """
        初始化分类器

        Args:
            llm: 语言模型实例，如果为None则自动创建
            temperature: 温度参数，默认0.1（更确定性的输出）
        """
        self.llm = llm if llm else get_llm(temperature=temperature)

        # 系统提示词
        self.system_prompt = """你是一个查询分类器，负责判断用户查询是否需要检索企业差旅知识库。

分类标准：

【FACTUAL - 需要检索知识库】：
- 询问企业差旅政策、规章制度
- 询问具体数值（住宿标准、报销额度、补贴金额等）
- 询问流程（如何申请、如何报销等）
- 询问具体地点的政策（北京、上海、杭州等城市的差旅标准）
- 询问时间、日期相关的差旅规定

【CHITCHAT - 直接回答，不需要检索】：
- 问候语（你好、早上好、谢谢等）
- 通用常识问题（天气、日期、一般性知识等）
- 系统功能询问（你能做什么、你是谁等）
- 与差旅政策无关的闲聊

请分析用户查询，返回JSON格式：
{
    "type": "FACTUAL" 或 "CHITCHAT",
    "confidence": 0.0到1.0之间的置信度,
    "reason": "分类原因的简短说明"
}

只返回JSON，不要其他内容。"""

    def classify(self, query: str) -> dict:
        """
        分类用户查询

        Args:
            query: 用户查询字符串

        Returns:
            dict: 包含type、confidence、reason的字典

        Raises:
            ValueError: 如果查询为空或None
        """
        # 输入验证
        if not query or (isinstance(query, str) and not query.strip()):
            raise ValueError("查询不能为空")

        query = query.strip()

        # 构建消息
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"用户查询：{query}")
        ]

        # 调用LLM（添加错误处理）
        try:
            response = self.llm.invoke(messages)
            result_text = response.content.strip()
        except Exception as e:
            # LLM调用失败，使用启发式规则作为后备
            result = self._fallback_classify(query)
            result["reason"] = f"LLM调用失败，使用启发式规则: {str(e)}"
            return result

        # 解析JSON响应
        try:
            # 尝试直接解析JSON
            result = json.loads(result_text)
        except json.JSONDecodeError:
            # 如果解析失败，尝试提取JSON部分
            json_match = re.search(r'\{[^}]+\}', result_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # 如果仍然失败，使用启发式规则作为后备
                result = self._fallback_classify(query)

        # 验证返回结构
        if "type" not in result:
            result["type"] = "CHITCHAT"
        if "confidence" not in result:
            result["confidence"] = 0.5
        if "reason" not in result:
            result["reason"] = "基于启发式规则的分类"

        # 确保type是有效值
        if result["type"] not in ["FACTUAL", "CHITCHAT"]:
            result["type"] = "CHITCHAT"

        # 确保confidence在有效范围
        result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))

        return result

    def _fallback_classify(self, query: str) -> dict:
        """
        启发式规则作为LLM失败时的后备方案

        Args:
            query: 用户查询

        Returns:
            dict: 分类结果
        """
        query_lower = query.lower()

        # CHITCHAT关键词
        chitchat_keywords = [
            "你好", "您好", "hi", "hello", "谢谢", "再见",
            "天气", "今天", "怎么样", "什么意思",
            "你是谁", "你能做什么", "功能"
        ]

        # FACTUAL关键词
        factual_keywords = [
            "标准", "多少", "报销", "差旅", "住宿", "交通",
            "补贴", "费用", "政策", "规定", "申请", "流程",
            "北京", "上海", "广州", "深圳", "杭州", "成都"
        ]

        # 检查关键词
        for keyword in chitchat_keywords:
            if keyword in query_lower:
                return {
                    "type": "CHITCHAT",
                    "confidence": 0.7,
                    "reason": f"包含闲聊关键词：{keyword}"
                }

        for keyword in factual_keywords:
            if keyword in query_lower:
                return {
                    "type": "FACTUAL",
                    "confidence": 0.7,
                    "reason": f"包含政策查询关键词：{keyword}"
                }

        # 默认返回CHITCHAT（更安全）
        return {
            "type": "CHITCHAT",
            "confidence": 0.5,
            "reason": "无法明确判断，默认为闲聊"
        }


# 使用示例
if __name__ == "__main__":
    """测试查询分类器"""
    print("测试查询分类器...\n")

    classifier = QueryClassifier()

    test_queries = [
        "你好",
        "去上海出差住宿能报多少钱",
        "今天天气怎么样",
        "北京出差住宿标准",
        "出差能报销多少钱",
        "你能做什么",
        "如何申请差旅报销"
    ]

    for query in test_queries:
        result = classifier.classify(query)
        print(f"查询：{query}")
        print(f"分类：{result['type']}")
        print(f"置信度：{result['confidence']:.2f}")
        print(f"原因：{result['reason']}")
        print("-" * 50)
