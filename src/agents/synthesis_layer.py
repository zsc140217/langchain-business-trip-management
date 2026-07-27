"""
综合分析层 - Layer 2 LLM综合判断

根据累积的上下文（工具结果+RAG文档）进行智能综合：
1. 判断信息是否足以回答用户问题
2. 如果足够：生成最终答案
3. 如果不够：判断还需要哪些工具（ReAct/编排兜底）

作者：Claude
创建时间：2026-06-28
"""
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage
from src.agents.context_accumulator import ContextAccumulator
import json


class SynthesisLayer:
    """
    综合分析层（Layer 2）

    根据累积的上下文（查询+工具结果+RAG文档）进行智能综合分析。

    工作流程：
    1. 接收ContextAccumulator累积的上下文
    2. LLM分析信息是否充足
    3. 如果充足：生成最终答案
    4. 如果不足：判断需要哪些额外工具

    Attributes:
        llm: 语言模型
    """

    def __init__(self, llm: BaseLanguageModel):
        """
        初始化综合分析层

        Args:
            llm: 语言模型
        """
        self.llm = llm

    def _create_synthesis_prompt(self, context: str) -> str:
        """
        创建综合分析提示词

        Args:
            context: 格式化的上下文

        Returns:
            完整的提示词
        """
        return f"""你是企业差旅助手的综合分析模块。你的任务是根据已有信息判断能否回答用户问题。

{context}

【分析任务】
1. 判断以上信息是否足以完整回答用户问题
2. 如果足够，生成完整、准确的答案（基于已有信息，不要编造）
3. 如果不够，说明还需要什么工具或信息

【可用工具】
- weather: 查询天气（需要城市参数）
- flight: 查询航班（需要出发城市、到达城市）
- hotel: 查询酒店（需要城市、可选价格/星级）
- customer: 查询客户信息（需要公司名或联系人）
- route: 查询路线（需要起点、终点）

【输出格式】严格按照JSON格式输出：
{{
    "complete": true/false,
    "confidence": 0.0-1.0,
    "answer": "如果complete=true，在此给出完整答案；否则为null",
    "reasoning": "分析过程和理由",
    "next_action": "如果complete=false，说明需要什么工具/信息；否则为null"
}}

【注意事项】
- 只使用已有信息回答，不要编造内容
- 如果工具结果和RAG文档有冲突，优先使用工具结果（更实时）
- 如果RAG文档为空但有工具结果，可以基于工具结果回答
- 如果两者都有，综合使用，提供完整答案
- 必须严格输出JSON格式

请输出JSON："""

    def synthesize(self, context: ContextAccumulator) -> Dict[str, Any]:
        """
        综合分析上下文并决策

        Args:
            context: 累积的上下文

        Returns:
            {
                "complete": bool,        # 信息是否充足可以回答
                "confidence": float,     # 置信度 0.0-1.0
                "answer": str | None,    # 最终答案（如果complete=True）
                "reasoning": str,        # 分析推理过程
                "next_action": str | None  # 需要的下一步操作（如果complete=False）
            }
        """
        # 获取格式化的上下文
        formatted_context = context.get_synthesis_context()

        try:
            # 创建提示词
            prompt = self._create_synthesis_prompt(formatted_context)

            # 调用LLM进行综合分析
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)

            # 提取内容
            if hasattr(response, 'content'):
                result = response.content
            else:
                result = str(response)

            # 解析JSON响应
            synthesis_result = self._parse_llm_response(result)

            # 验证和规范化
            return self._validate_result(synthesis_result)

        except Exception as e:
            # 降级处理：如果LLM调用失败，使用规则兜底
            print(f"[WARNING] 综合分析失败：{e}，使用规则降级")
            return self._fallback_analysis(context)

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        解析LLM的JSON响应

        Args:
            response: LLM输出的字符串

        Returns:
            解析后的字典

        Raises:
            ValueError: 解析失败
        """
        # 提取JSON部分（可能包含markdown代码块）
        response = response.strip()

        # 去除可能的markdown代码块标记
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        # 解析JSON
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析LLM响应为JSON: {e}\n原始响应: {response[:200]}")

    def _validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和规范化综合分析结果

        Args:
            result: 原始结果字典

        Returns:
            规范化的结果字典
        """
        # 必需字段检查
        if "complete" not in result:
            raise ValueError("缺少必需字段: complete")

        # 规范化字段
        validated = {
            "complete": bool(result.get("complete", False)),
            "confidence": float(result.get("confidence", 0.5)),
            "answer": result.get("answer"),
            "reasoning": result.get("reasoning", ""),
            "next_action": result.get("next_action")
        }

        # 逻辑一致性检查
        if validated["complete"] and not validated["answer"]:
            raise ValueError("complete=True但answer为空")

        if not validated["complete"] and not validated["next_action"]:
            raise ValueError("complete=False但next_action为空")

        # 置信度范围检查
        validated["confidence"] = max(0.0, min(1.0, validated["confidence"]))

        return validated

    def _fallback_analysis(self, context: ContextAccumulator) -> Dict[str, Any]:
        """
        规则降级分析（当LLM失败时）

        Args:
            context: 上下文累积器

        Returns:
            降级的分析结果
        """
        # 规则1：有工具结果且有RAG文档 → 可以回答
        if context.has_tool_results() and context.has_rag_documents():
            tool_names = list(context.tool_results.keys())
            return {
                "complete": True,
                "confidence": 0.7,
                "answer": self._generate_simple_answer(context),
                "reasoning": f"规则降级：检测到工具结果({tool_names})和RAG文档，尝试综合回答",
                "next_action": None
            }

        # 规则2：只有工具结果 → 可以回答
        elif context.has_tool_results():
            return {
                "complete": True,
                "confidence": 0.6,
                "answer": self._generate_simple_answer(context),
                "reasoning": "规则降级：仅基于工具结果回答",
                "next_action": None
            }

        # 规则3：只有RAG文档 → 可以回答
        elif context.has_rag_documents():
            return {
                "complete": True,
                "confidence": 0.6,
                "answer": self._generate_simple_answer(context),
                "reasoning": "规则降级：仅基于RAG文档回答",
                "next_action": None
            }

        # 规则4：什么都没有 → 需要更多信息
        else:
            return {
                "complete": False,
                "confidence": 0.3,
                "answer": None,
                "reasoning": "规则降级：无工具结果也无RAG文档，需要更多信息",
                "next_action": "建议使用任务编排器分解查询并执行"
            }

    def _generate_simple_answer(self, context: ContextAccumulator) -> str:
        """
        生成简单的拼接答案（降级策略）

        Args:
            context: 上下文累积器

        Returns:
            简单拼接的答案
        """
        answer_parts = []

        # 添加工具结果
        for tool_name, data in context.tool_results.items():
            answer_parts.append(f"【{tool_name}】{data['result']}")

        # 添加RAG文档内容（前3个）
        if context.has_rag_documents():
            answer_parts.append("\n【相关政策】")
            for doc in context.rag_documents[:3]:
                answer_parts.append(f"- {doc.page_content[:100]}...")

        return "\n".join(answer_parts) if answer_parts else "抱歉，暂无相关信息。"


# 使用示例
if __name__ == "__main__":
    """演示SynthesisLayer的使用"""
    from src.models.llm import get_llm
    from src.agents.context_accumulator import ContextAccumulator
    from langchain.schema import Document

    # 初始化
    llm = get_llm(temperature=0.3)
    synthesis_layer = SynthesisLayer(llm)

    # 场景1：工具结果 + RAG文档都有
    print("=" * 70)
    print("场景1：信息充足，应该可以回答")
    print("=" * 70)

    ctx1 = ContextAccumulator()
    ctx1.set_query("北京天气怎么样？住宿标准是多少？")
    ctx1.add_tool_result("weather", "北京今日晴，18-25℃", {"city": "北京"})
    ctx1.add_rag_documents([
        Document(page_content="一线城市（北京、上海）住宿标准：500元/晚")
    ])

    result1 = synthesis_layer.synthesize(ctx1)
    print(f"Complete: {result1['complete']}")
    print(f"Confidence: {result1['confidence']:.2f}")
    print(f"Answer: {result1['answer'][:150] if result1['answer'] else None}...")
    print(f"Reasoning: {result1['reasoning']}")

    # 场景2：信息不足
    print("\n" + "=" * 70)
    print("场景2：信息不足，需要更多工具")
    print("=" * 70)

    ctx2 = ContextAccumulator()
    ctx2.set_query("去杭州出差，推荐酒店和航班")
    # 没有工具结果，也没有RAG文档

    result2 = synthesis_layer.synthesize(ctx2)
    print(f"Complete: {result2['complete']}")
    print(f"Confidence: {result2['confidence']:.2f}")
    print(f"Next Action: {result2['next_action']}")
    print(f"Reasoning: {result2['reasoning']}")
