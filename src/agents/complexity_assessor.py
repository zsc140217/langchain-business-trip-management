"""
复杂度评估器
实现混合判断策略：80%规则 + 20%LLM

对应Spring AI的：
src/main/java/com/jblmj/aiagent/service/ComplexityAssessor.java
"""
from enum import Enum
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import Optional


class QueryComplexity(Enum):
    """查询复杂度枚举"""
    SIMPLE = "SIMPLE"    # 单一意图，单次工具调用
    MEDIUM = "MEDIUM"    # 单一意图，多次工具调用
    COMPLEX = "COMPLEX"  # 多意图，需要任务分解


class ComplexityAssessor:
    """
    复杂度评估器

    核心创新：混合判断策略
    - 80%场景用规则判断（<1ms，快速）
    - 20%场景用LLM判断（1-2s，准确）

    设计思路：
    1. 快速筛选：长度<10字 → SIMPLE
    2. 规则判断：基于关键词统计
    3. LLM确认：只对COMPLEX查询二次确认
    """

    def __init__(self, llm):
        self.llm = llm
        self.llm_chain = self._create_llm_chain()

        # 意图关键词组
        self.intent_groups = [
            ["天气", "温度", "下雨", "带伞", "气温"],
            ["客户", "公司", "地址", "联系", "电话"],
            ["路线", "怎么去", "交通", "地铁", "距离"],
            ["酒店", "住宿", "推荐", "协议酒店", "宾馆"],
            ["补贴", "报销", "标准", "伙食", "费用"]
        ]

        # 规划关键词
        self.planning_keywords = ["规划", "安排", "计划", "准备", "行程", "方案", "攻略"]

        # 连接词
        self.conjunctions = ["并", "和", "还有", "以及", "同时", "另外"]

    def assess(self, query: str) -> QueryComplexity:
        """
        评估查询复杂度

        流程：
        1. 快速筛选（长度判断）
        2. 规则判断（关键词统计）
        3. LLM二次确认（仅COMPLEX）

        Args:
            query: 用户查询

        Returns:
            QueryComplexity枚举值
        """
        print(f"\n========== 复杂度评估开始 ==========")
        print(f"查询：{query}")

        # 1. 快速筛选：长度 < 10 字 → SIMPLE
        if len(query) < 10:
            print(f"快速筛选：长度{len(query)}<10 → SIMPLE")
            print(f"========== 复杂度评估完成 ==========\n")
            return QueryComplexity.SIMPLE

        # 2. 规则判断
        rule_result = self._assess_by_rule(query)
        print(f"规则判断结果：{rule_result.value}")

        # 3. 如果规则判断为 COMPLEX，用 LLM 二次确认
        if rule_result == QueryComplexity.COMPLEX:
            print("触发LLM二次确认...")
            llm_result = self._assess_by_llm(query)
            print(f"LLM判断结果：{llm_result.value}")
            print(f"========== 复杂度评估完成 ==========\n")
            return llm_result

        print(f"========== 复杂度评估完成 ==========\n")
        return rule_result

    def _assess_by_rule(self, query: str) -> QueryComplexity:
        """
        基于规则的复杂度判断

        判断逻辑：
        1. 包含规划关键词 → COMPLEX
        2. 多意图（连接词分隔） → COMPLEX
        3. 意图数>=2 → COMPLEX
        4. 意图数=1 且 实体数>=2 → MEDIUM
        5. 其他 → SIMPLE

        Args:
            query: 用户查询

        Returns:
            QueryComplexity枚举值
        """
        # 统计意图、实体
        intent_count = self._count_intents(query)
        entity_count = self._count_entities(query)

        print(f"  意图数：{intent_count}")
        print(f"  实体数：{entity_count}")

        # 判断规划场景
        if self._is_complex_planning(query):
            print(f"  检测到规划关键词 → COMPLEX")
            return QueryComplexity.COMPLEX

        # 判断多意图
        if self._has_multiple_intents(query):
            print(f"  检测到多意图 → COMPLEX")
            return QueryComplexity.COMPLEX

        # 根据意图数和实体数判断
        if intent_count >= 2:
            print(f"  意图数>=2 → COMPLEX")
            return QueryComplexity.COMPLEX

        if intent_count == 1 and entity_count >= 2:
            print(f"  单意图+多实体 → MEDIUM")
            return QueryComplexity.MEDIUM

        print(f"  单意图+单实体 → SIMPLE")
        return QueryComplexity.SIMPLE

    def _assess_by_llm(self, query: str) -> QueryComplexity:
        """
        基于LLM的复杂度判断

        只在规则判断为COMPLEX时调用，减少LLM调用次数

        Args:
            query: 用户查询

        Returns:
            QueryComplexity枚举值
        """
        prompt = f"""判断以下查询的复杂度，只回答 SIMPLE / MEDIUM / COMPLEX。

规则：
- SIMPLE: 单一意图，单次工具调用（如"北京天气"）
- MEDIUM: 单一意图，多次工具调用（如"上海和广州天气对比"）
- COMPLEX: 多意图，需要任务分解（如"去杭州出差，查天气并推荐酒店"）

查询：{query}

复杂度："""

        try:
            response = self.llm_chain.run(query=query, prompt=prompt)
            response = response.strip().upper()

            if "SIMPLE" in response:
                return QueryComplexity.SIMPLE
            elif "MEDIUM" in response:
                return QueryComplexity.MEDIUM
            elif "COMPLEX" in response:
                return QueryComplexity.COMPLEX
            else:
                # 默认返回SIMPLE
                return QueryComplexity.SIMPLE

        except Exception as e:
            print(f"LLM判断失败：{e}，降级为SIMPLE")
            return QueryComplexity.SIMPLE

    def _count_intents(self, query: str) -> int:
        """
        统计意图数量（混合策略）

        策略：
        1. 先用关键词匹配（快速）
        2. 如果匹配不到，用LLM兜底（准确）

        Args:
            query: 用户查询

        Returns:
            意图数量
        """
        # 先用关键词匹配
        keyword_count = self._count_intents_by_keyword(query)

        # 如果关键词匹配不到，用LLM兜底
        if keyword_count == 0:
            return self._count_intents_by_llm(query)

        return keyword_count

    def _count_intents_by_keyword(self, query: str) -> int:
        """
        通过关键词统计意图

        Args:
            query: 用户查询

        Returns:
            意图数量
        """
        count = 0
        for group in self.intent_groups:
            if any(keyword in query for keyword in group):
                count += 1

        return count

    def _count_intents_by_llm(self, query: str) -> int:
        """
        通过LLM统计意图（兜底）

        Args:
            query: 用户查询

        Returns:
            意图数量
        """
        prompt = f"""统计以下查询包含几个意图，只回答数字。

示例：
- "北京天气" → 1
- "上海和广州天气对比" → 1
- "去杭州出差，查天气并推荐酒店" → 2

查询：{query}

意图数量："""

        try:
            response = self.llm_chain.run(query=query, prompt=prompt)
            # 提取数字
            import re
            numbers = re.findall(r'\d+', response)
            if numbers:
                return int(numbers[0])
            return 1
        except:
            return 1

    def _count_entities(self, query: str) -> int:
        """
        统计实体数量（简单实现：统计城市）

        Args:
            query: 用户查询

        Returns:
            实体数量
        """
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安", "南京", "苏州"]
        count = sum(1 for city in cities if city in query)
        return count

    def _is_complex_planning(self, query: str) -> bool:
        """
        判断是否为复杂规划场景

        Args:
            query: 用户查询

        Returns:
            是否为规划场景
        """
        return any(keyword in query for keyword in self.planning_keywords)

    def _has_multiple_intents(self, query: str) -> bool:
        """
        判断是否包含多个意图

        通过连接词判断：
        - "去杭州出差，查天气并推荐酒店" → True
        - "上海和广州天气对比" → False（同一意图）

        Args:
            query: 用户查询

        Returns:
            是否包含多意图
        """
        for conj in self.conjunctions:
            if conj in query:
                parts = query.split(conj)
                if len(parts) >= 2:
                    # 检查两部分是否都包含意图关键词
                    part1_has_intent = self._has_intent_keyword(parts[0])
                    part2_has_intent = self._has_intent_keyword(parts[1])
                    if part1_has_intent and part2_has_intent:
                        return True

        return False

    def _has_intent_keyword(self, text: str) -> bool:
        """
        判断文本中是否包含意图关键词

        Args:
            text: 文本

        Returns:
            是否包含意图关键词
        """
        intent_keywords = ["天气", "温度", "客户", "公司", "路线", "交通", "酒店", "住宿", "补贴", "报销"]
        return any(keyword in text for keyword in intent_keywords)

    def _create_llm_chain(self):
        """创建LLM链"""
        prompt = PromptTemplate(
            input_variables=["query"],
            template="{prompt}"
        )
        return LLMChain(llm=self.llm, prompt=prompt)


# 测试代码
if __name__ == "__main__":
    """
    测试复杂度评估器
    """
    print("测试复杂度评估器...\n")

    from src.models.llm import get_llm

    try:
        llm = get_llm(temperature=0.0)
        assessor = ComplexityAssessor(llm)

        # 测试用例
        test_cases = [
            ("北京天气", QueryComplexity.SIMPLE),
            ("上海和广州天气对比", QueryComplexity.MEDIUM),
            ("去杭州出差，查天气并推荐酒店", QueryComplexity.COMPLEX),
            ("帮我规划明天去深圳的行程", QueryComplexity.COMPLEX),
            ("深圳适合出差吗", QueryComplexity.SIMPLE),
        ]

        passed = 0
        for query, expected in test_cases:
            result = assessor.assess(query)
            status = "✅" if result == expected else "❌"
            print(f"{status} 查询：{query}")
            print(f"   期望：{expected.value}，实际：{result.value}\n")
            if result == expected:
                passed += 1

        print(f"\n测试结果：{passed}/{len(test_cases)} 通过")

    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
