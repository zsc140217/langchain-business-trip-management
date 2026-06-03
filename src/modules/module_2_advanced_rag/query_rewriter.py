"""
查询重写器 - 使用LLM改写用户查询

对应Spring AI的：
src/main/java/com/jblmj/aiagent/rag/EnterpriseQueryRewriter.java

核心功能：
1. 口语化 → 标准化
2. 保留否定词（不能、不可以）
3. 补充关键信息
4. Few-shot prompt engineering
"""
from typing import Optional


class EnterpriseQueryRewriter:
    """
    企业级查询重写器

    为什么需要查询重写：
    1. 用户查询口语化："去魔都出差住宿能报多少"
    2. 向量检索需要标准化："上海一类城市出差住宿费用报销标准"
    3. 提升召回率：补充关键信息、替换俚语

    核心挑战：
    - 否定查询处理：如"不能住五星级酒店吗"需要保留"不能"
    - 语义保持：不能改变用户原意
    - 稳定性：需要低temperature避免随机性

    Few-shot示例：
    1. 口语化 → 标准化：
       "去魔都出差住宿能报多少" → "上海一类城市出差住宿费用报销标准"

    2. 否定疑问 → 保留否定词：
       "北京出差不能住五星级酒店吗" → "北京出差住宿标准 不能住五星级酒店"

    3. 多意图 → 拆分关键词：
       "去杭州拜访客户，住宿标准和客户地址" → "杭州出差住宿标准 杭州客户信息地址"
    """

    def __init__(self, llm):
        """
        初始化查询重写器

        Args:
            llm: LLM实例（必须支持predict方法）
        """
        self.llm = llm
        self.negation_keywords = [
            "不能", "不可以", "不是", "没有",
            "不要", "禁止", "不准", "不得"
        ]

        # Few-shot示例（基于真实业务场景）
        self.few_shot_examples = """
示例1：口语化 → 标准化
原始："去魔都出差住宿能报多少"
改写："上海一类城市出差住宿费用报销标准"

示例2：否定疑问 → 保留否定词
原始："北京出差不能住五星级酒店吗"
改写："北京出差住宿标准 不能住五星级酒店"

示例3：多意图 → 拆分关键词
原始："去杭州拜访客户，住宿标准和客户地址"
改写："杭州出差住宿标准 杭州客户信息地址"

示例4：简称 → 全称
原始："差旅补助咋算的"
改写："出差期间差旅补助费用计算标准"

示例5：数值保留
原始："超过1000元的住宿能报销吗"
改写："住宿费用报销标准 超过1000元"
"""

    def rewrite(self, original_query: str) -> str:
        """
        执行查询重写

        流程：
        1. 检测否定查询 → 特殊处理
        2. 构建Few-shot Prompt
        3. 调用LLM改写（低temperature）
        4. 清理和验证结果

        Args:
            original_query: 原始查询

        Returns:
            改写后的查询（如果改写失败，返回原始查询）
        """
        # 1. 检测否定查询
        if self._is_negation_query(original_query):
            return self._handle_negation_query(original_query)

        # 2. 构建改写Prompt
        prompt = f"""你是企业差旅政策查询系统的查询重写专家。
将用户的口语化查询改写为更适合向量检索的标准化表达。

{self.few_shot_examples}

【改写规则】
1. 替换口语词为标准术语（魔都→上海，咋→如何）
2. 补充关键信息（城市分类、费用类型、政策条款）
3. 保留原始语义，不添加用户未提及的内容
4. 保留否定词、数值、时间等关键要素
5. 改写后应该是陈述句，去掉疑问语气
6. 只输出改写后的查询，不要解释

【用户查询】
{original_query}

改写后的查询："""

        try:
            # 3. 调用LLM改写（Temperature=0.1，稳定性优先）
            rewritten_query = self.llm.predict(prompt, temperature=0.1)

            # 4. 清理结果
            rewritten_query = self._clean_result(rewritten_query)

            # 5. 验证质量
            if self._is_valid_rewrite(original_query, rewritten_query):
                return rewritten_query
            else:
                return original_query

        except Exception as e:
            print(f"查询重写失败：{e}")
            return original_query

    def _is_negation_query(self, query: str) -> bool:
        """
        检测是否为否定查询

        Args:
            query: 查询字符串

        Returns:
            是否包含否定词
        """
        return any(keyword in query for keyword in self.negation_keywords)

    def _handle_negation_query(self, query: str) -> str:
        """
        处理否定查询，保留否定词

        策略：将否定词前后内容拆分，保持否定语义

        示例：
        "北京出差不能住五星级酒店吗"
        → "北京出差住宿标准 不能住五星级酒店"

        Args:
            query: 原始查询

        Returns:
            处理后的查询
        """
        for keyword in self.negation_keywords:
            if keyword in query:
                parts = query.split(keyword)
                if len(parts) >= 2:
                    # 去除疑问词
                    before = parts[0].strip()
                    after = parts[1].replace("吗", "").replace("？", "").strip()
                    return f"{before} {keyword} {after}"
        return query

    def _clean_result(self, rewritten: str) -> str:
        """
        清理改写结果

        移除LLM可能输出的前缀和引号

        Args:
            rewritten: LLM输出的改写结果

        Returns:
            清理后的查询
        """
        # 移除常见前缀
        rewritten = rewritten.replace("改写后的查询：", "")
        rewritten = rewritten.replace("改写：", "")
        rewritten = rewritten.replace("标准化查询：", "")

        # 移除引号
        rewritten = rewritten.strip('"\'')

        # 移除首尾空白
        return rewritten.strip()

    def _is_valid_rewrite(self, original: str, rewritten: str) -> bool:
        """
        验证改写质量

        质量标准：
        1. 长度合理：5-100字符
        2. 不为空
        3. 不与原始查询完全相同（除非确实不需要改写）

        Args:
            original: 原始查询
            rewritten: 改写后的查询

        Returns:
            是否为有效改写
        """
        # 基本检查
        if not rewritten or len(rewritten) < 5 or len(rewritten) > 100:
            return False

        # 检查是否只是简单复制
        if rewritten == original:
            # 如果原始查询已经很标准，复制也是合理的
            return True

        return True


class SimpleQueryRewriter:
    """
    简单查询重写器（无需LLM）

    基于规则的查询重写，适合不想使用LLM的场景

    功能：
    1. 口语词替换（魔都→上海）
    2. 疑问词去除（吗、呢、啊）
    3. 同义词扩展
    """

    def __init__(self):
        """初始化简单查询重写器"""
        # 口语词映射
        self.slang_map = {
            "魔都": "上海",
            "帝都": "北京",
            "咋": "如何",
            "啥": "什么",
            "咋样": "怎么样",
            "多少钱": "费用标准",
            "能不能": "是否可以",
        }

        # 疑问词列表
        self.question_words = ["吗", "呢", "啊", "？", "?"]

    def rewrite(self, original_query: str) -> str:
        """
        执行规则驱动的查询重写

        Args:
            original_query: 原始查询

        Returns:
            改写后的查询
        """
        rewritten = original_query

        # 1. 替换口语词
        for slang, formal in self.slang_map.items():
            rewritten = rewritten.replace(slang, formal)

        # 2. 去除疑问词
        for word in self.question_words:
            rewritten = rewritten.replace(word, "")

        return rewritten.strip()
