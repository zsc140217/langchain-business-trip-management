"""
LangChain企业差旅项目评测指标实现

实现四大LLM-as-Judge评测指标：
1. Correctness Evaluator - 答案正确性评估
2. Relevance Evaluator - 答案相关性评估
3. Groundedness Evaluator - 基础性/忠实度评估（是否基于检索内容）
4. Retrieval Relevance Evaluator - 检索相关性评估

设计原则：
- 使用LLM作为评判者（LLM-as-Judge）
- 结构化评分标准（1-5分制）
- 详细的评估理由
- 支持LangSmith跟踪
- 类型安全的输入输出
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from langsmith import traceable
import logging
import json

logger = logging.getLogger(__name__)


# ============================================================================
# 数据模型定义
# ============================================================================

class EvaluationResult(BaseModel):
    """评估结果数据模型"""
    score: int = Field(..., ge=1, le=5, description="评分（1-5分）")
    reasoning: str = Field(..., description="评分理由")
    metric_name: str = Field(..., description="评测指标名称")
    passed: bool = Field(..., description="是否通过（score >= 3）")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外元数据")


class CorrectnessInput(BaseModel):
    """正确性评估输入"""
    question: str = Field(..., description="用户问题")
    answer: str = Field(..., description="系统生成的答案")
    reference: Optional[str] = Field(None, description="参考答案（可选）")
    context: Optional[str] = Field(None, description="额外上下文（可选）")


class RelevanceInput(BaseModel):
    """相关性评估输入"""
    question: str = Field(..., description="用户问题")
    answer: str = Field(..., description="系统生成的答案")


class GroundednessInput(BaseModel):
    """基础性评估输入"""
    answer: str = Field(..., description="系统生成的答案")
    retrieved_contexts: List[str] = Field(..., description="检索到的上下文列表")


class RetrievalRelevanceInput(BaseModel):
    """检索相关性评估输入"""
    question: str = Field(..., description="用户问题")
    retrieved_contexts: List[str] = Field(..., description="检索到的上下文列表")


# ============================================================================
# Prompt模板定义
# ============================================================================

CORRECTNESS_PROMPT = """你是一个专业的答案质量评估专家。请评估给定答案的正确性。

用户问题：
{question}

系统答案：
{answer}

{reference_section}

评估标准：
- 5分：答案完全正确，信息准确无误，逻辑清晰
- 4分：答案基本正确，有少量无关紧要的小错误
- 3分：答案部分正确，有一些错误但核心信息准确
- 2分：答案大部分错误，仅有少量正确信息
- 1分：答案完全错误或不相关

请以JSON格式返回评估结果：
{{
    "score": <1-5的整数>,
    "reasoning": "<详细的评分理由，说明答案的正确性、错误之处、改进建议>"
}}

评估结果："""

RELEVANCE_PROMPT = """你是一个专业的答案相关性评估专家。请评估给定答案与用户问题的相关性。

用户问题：
{question}

系统答案：
{answer}

评估标准：
- 5分：答案完全切题，直接回答用户问题，没有无关内容
- 4分：答案基本切题，有少量偏离但不影响理解
- 3分：答案部分切题，包含一些无关信息
- 2分：答案大部分偏离主题，仅有少量相关内容
- 1分：答案完全偏题或答非所问

请以JSON格式返回评估结果：
{{
    "score": <1-5的整数>,
    "reasoning": "<详细的评分理由，说明答案的相关性、偏离之处、改进建议>"
}}

评估结果："""

GROUNDEDNESS_PROMPT = """你是一个专业的答案忠实度评估专家。请评估给定答案是否基于检索到的上下文，是否存在幻觉（hallucination）。

系统答案：
{answer}

检索到的上下文：
{contexts}

评估标准：
- 5分：答案完全基于检索上下文，所有陈述都有明确来源，无任何幻觉
- 4分：答案基本基于检索上下文，有少量合理推理，无明显幻觉
- 3分：答案部分基于检索上下文，有一些无法验证的陈述
- 2分：答案大部分内容无法从检索上下文中验证，存在较多幻觉
- 1分：答案完全脱离检索上下文，严重幻觉

请以JSON格式返回评估结果：
{{
    "score": <1-5的整数>,
    "reasoning": "<详细的评分理由，说明哪些内容有依据、哪些是幻觉、改进建议>"
}}

评估结果："""

RETRIEVAL_RELEVANCE_PROMPT = """你是一个专业的检索质量评估专家。请评估检索到的上下文与用户问题的相关性。

用户问题：
{question}

检索到的上下文：
{contexts}

评估标准：
- 5分：所有检索结果都高度相关，能够充分回答问题
- 4分：大部分检索结果相关，少量结果相关性较弱
- 3分：约一半检索结果相关，能够部分回答问题
- 2分：大部分检索结果不相关，仅少量有用信息
- 1分：所有检索结果都不相关，无法回答问题

请以JSON格式返回评估结果：
{{
    "score": <1-5的整数>,
    "reasoning": "<详细的评分理由，说明哪些上下文相关、哪些不相关、改进建议>"
}}

评估结果："""


# ============================================================================
# 评估器基类
# ============================================================================

class BaseEvaluator:
    """
    评估器基类

    提供：
    - LLM集成
    - Prompt模板管理
    - JSON解析和错误处理
    - LangSmith跟踪
    - 统一的评估接口
    """

    def __init__(
        self,
        llm: BaseChatModel,
        metric_name: str,
        prompt_template: str,
        temperature: float = 0.0  # 使用低温度保证评估一致性
    ):
        """
        初始化评估器

        Args:
            llm: 语言模型实例
            metric_name: 评测指标名称
            prompt_template: Prompt模板
            temperature: 采样温度（评估任务建议使用0.0）
        """
        self.llm = llm
        self.metric_name = metric_name
        self.prompt_template = PromptTemplate.from_template(prompt_template)
        self.temperature = temperature

        logger.info(f"Initialized {metric_name} evaluator")

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        解析LLM返回的JSON响应

        Args:
            response: LLM响应字符串

        Returns:
            解析后的字典

        Raises:
            ValueError: JSON解析失败
        """
        try:
            # 尝试提取JSON部分
            response = response.strip()

            # 如果响应包含代码块标记，提取其中的JSON
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            # 解析JSON
            parsed = json.loads(response)

            # 验证必需字段
            if "score" not in parsed or "reasoning" not in parsed:
                raise ValueError("Missing required fields: score or reasoning")

            # 验证score范围
            score = int(parsed["score"])
            if not (1 <= score <= 5):
                raise ValueError(f"Score must be between 1 and 5, got {score}")

            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}\nResponse: {response}")
            raise ValueError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            logger.error(f"Response parsing failed: {e}")
            raise ValueError(f"Failed to parse response: {e}")

    def _call_llm(self, prompt: str) -> str:
        """
        调用LLM并处理错误

        Args:
            prompt: 输入提示

        Returns:
            LLM响应

        Raises:
            RuntimeError: LLM调用失败
        """
        try:
            logger.debug(f"Calling LLM for {self.metric_name} evaluation")

            # 调用LLM - 兼容不同的LangChain版本
            if hasattr(self.llm, 'invoke'):
                # ChatModel调用方式
                from langchain_core.messages import HumanMessage
                message = HumanMessage(content=prompt)
                result = self.llm.invoke([message])
                response = result.content if hasattr(result, 'content') else str(result)
            elif hasattr(self.llm, 'predict'):
                # 旧版LLM调用方式
                response = self.llm.predict(prompt)
            else:
                # 直接调用
                result = self.llm(prompt)
                response = result.content if hasattr(result, 'content') else str(result)

            logger.debug(f"LLM response: {response[:200]}...")
            return response

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise RuntimeError(f"LLM call failed: {e}") from e

    def _create_result(
        self,
        score: int,
        reasoning: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        创建评估结果对象

        Args:
            score: 评分（1-5）
            reasoning: 评分理由
            metadata: 额外元数据

        Returns:
            评估结果对象
        """
        return EvaluationResult(
            score=score,
            reasoning=reasoning,
            metric_name=self.metric_name,
            passed=(score >= 3),  # 3分及以上视为通过
            metadata=metadata or {}
        )


# ============================================================================
# 具体评估器实现
# ============================================================================

class CorrectnessEvaluator(BaseEvaluator):
    """
    答案正确性评估器

    评估系统生成答案的准确性和正确性
    支持可选的参考答案进行对比
    """

    def __init__(self, llm: BaseChatModel, temperature: float = 0.0):
        super().__init__(
            llm=llm,
            metric_name="correctness",
            prompt_template=CORRECTNESS_PROMPT,
            temperature=temperature
        )

    @traceable(name="correctness_evaluation")
    def evaluate(self, input_data: CorrectnessInput) -> EvaluationResult:
        """
        评估答案正确性

        Args:
            input_data: 包含问题、答案和可选参考答案的输入

        Returns:
            评估结果

        Raises:
            ValueError: 输入无效
            RuntimeError: 评估失败
        """
        try:
            logger.info(f"Evaluating correctness for question: {input_data.question[:50]}...")

            # 构建参考答案部分
            reference_section = ""
            if input_data.reference:
                reference_section = f"参考答案（用于对比）：\n{input_data.reference}\n"

            # 生成Prompt
            prompt = self.prompt_template.format(
                question=input_data.question,
                answer=input_data.answer,
                reference_section=reference_section
            )

            # 调用LLM
            response = self._call_llm(prompt)

            # 解析响应
            parsed = self._parse_llm_response(response)

            # 创建结果
            result = self._create_result(
                score=parsed["score"],
                reasoning=parsed["reasoning"],
                metadata={
                    "has_reference": input_data.reference is not None,
                    "question_length": len(input_data.question),
                    "answer_length": len(input_data.answer)
                }
            )

            logger.info(f"Correctness evaluation completed: score={result.score}, passed={result.passed}")
            return result

        except Exception as e:
            logger.error(f"Correctness evaluation failed: {e}")
            raise RuntimeError(f"Correctness evaluation failed: {e}") from e


class RelevanceEvaluator(BaseEvaluator):
    """
    答案相关性评估器

    评估系统生成答案与用户问题的相关程度
    检测答非所问或偏离主题的情况
    """

    def __init__(self, llm: BaseChatModel, temperature: float = 0.0):
        super().__init__(
            llm=llm,
            metric_name="relevance",
            prompt_template=RELEVANCE_PROMPT,
            temperature=temperature
        )

    @traceable(name="relevance_evaluation")
    def evaluate(self, input_data: RelevanceInput) -> EvaluationResult:
        """
        评估答案相关性

        Args:
            input_data: 包含问题和答案的输入

        Returns:
            评估结果

        Raises:
            ValueError: 输入无效
            RuntimeError: 评估失败
        """
        try:
            logger.info(f"Evaluating relevance for question: {input_data.question[:50]}...")

            # 生成Prompt
            prompt = self.prompt_template.format(
                question=input_data.question,
                answer=input_data.answer
            )

            # 调用LLM
            response = self._call_llm(prompt)

            # 解析响应
            parsed = self._parse_llm_response(response)

            # 创建结果
            result = self._create_result(
                score=parsed["score"],
                reasoning=parsed["reasoning"],
                metadata={
                    "question_length": len(input_data.question),
                    "answer_length": len(input_data.answer)
                }
            )

            logger.info(f"Relevance evaluation completed: score={result.score}, passed={result.passed}")
            return result

        except Exception as e:
            logger.error(f"Relevance evaluation failed: {e}")
            raise RuntimeError(f"Relevance evaluation failed: {e}") from e


class GroundednessEvaluator(BaseEvaluator):
    """
    基础性/忠实度评估器

    评估答案是否基于检索到的上下文
    检测幻觉（hallucination）问题
    """

    def __init__(self, llm: BaseChatModel, temperature: float = 0.0):
        super().__init__(
            llm=llm,
            metric_name="groundedness",
            prompt_template=GROUNDEDNESS_PROMPT,
            temperature=temperature
        )

    @traceable(name="groundedness_evaluation")
    def evaluate(self, input_data: GroundednessInput) -> EvaluationResult:
        """
        评估答案基础性

        Args:
            input_data: 包含答案和检索上下文的输入

        Returns:
            评估结果

        Raises:
            ValueError: 输入无效
            RuntimeError: 评估失败
        """
        try:
            logger.info(f"Evaluating groundedness with {len(input_data.retrieved_contexts)} contexts")

            # 格式化检索上下文
            contexts_formatted = "\n\n".join([
                f"[上下文 {i+1}]\n{ctx}"
                for i, ctx in enumerate(input_data.retrieved_contexts)
            ])

            # 生成Prompt
            prompt = self.prompt_template.format(
                answer=input_data.answer,
                contexts=contexts_formatted
            )

            # 调用LLM
            response = self._call_llm(prompt)

            # 解析响应
            parsed = self._parse_llm_response(response)

            # 创建结果
            result = self._create_result(
                score=parsed["score"],
                reasoning=parsed["reasoning"],
                metadata={
                    "num_contexts": len(input_data.retrieved_contexts),
                    "answer_length": len(input_data.answer),
                    "total_context_length": sum(len(ctx) for ctx in input_data.retrieved_contexts)
                }
            )

            logger.info(f"Groundedness evaluation completed: score={result.score}, passed={result.passed}")
            return result

        except Exception as e:
            logger.error(f"Groundedness evaluation failed: {e}")
            raise RuntimeError(f"Groundedness evaluation failed: {e}") from e


class RetrievalRelevanceEvaluator(BaseEvaluator):
    """
    检索相关性评估器

    评估检索系统返回的上下文与用户问题的相关程度
    衡量检索质量
    """

    def __init__(self, llm: BaseChatModel, temperature: float = 0.0):
        super().__init__(
            llm=llm,
            metric_name="retrieval_relevance",
            prompt_template=RETRIEVAL_RELEVANCE_PROMPT,
            temperature=temperature
        )

    @traceable(name="retrieval_relevance_evaluation")
    def evaluate(self, input_data: RetrievalRelevanceInput) -> EvaluationResult:
        """
        评估检索相关性

        Args:
            input_data: 包含问题和检索上下文的输入

        Returns:
            评估结果

        Raises:
            ValueError: 输入无效
            RuntimeError: 评估失败
        """
        try:
            logger.info(f"Evaluating retrieval relevance for question: {input_data.question[:50]}...")

            # 格式化检索上下文
            contexts_formatted = "\n\n".join([
                f"[检索结果 {i+1}]\n{ctx}"
                for i, ctx in enumerate(input_data.retrieved_contexts)
            ])

            # 生成Prompt
            prompt = self.prompt_template.format(
                question=input_data.question,
                contexts=contexts_formatted
            )

            # 调用LLM
            response = self._call_llm(prompt)

            # 解析响应
            parsed = self._parse_llm_response(response)

            # 创建结果
            result = self._create_result(
                score=parsed["score"],
                reasoning=parsed["reasoning"],
                metadata={
                    "num_contexts": len(input_data.retrieved_contexts),
                    "question_length": len(input_data.question),
                    "total_context_length": sum(len(ctx) for ctx in input_data.retrieved_contexts)
                }
            )

            logger.info(f"Retrieval relevance evaluation completed: score={result.score}, passed={result.passed}")
            return result

        except Exception as e:
            logger.error(f"Retrieval relevance evaluation failed: {e}")
            raise RuntimeError(f"Retrieval relevance evaluation failed: {e}") from e


# ============================================================================
# 批量评估器
# ============================================================================

class ComprehensiveEvaluator:
    """
    综合评估器

    组合所有评估指标，提供一站式评估功能
    支持批量评估和结果汇总
    """

    def __init__(self, llm: BaseChatModel, temperature: float = 0.0):
        """
        初始化综合评估器

        Args:
            llm: 语言模型实例
            temperature: 采样温度
        """
        self.correctness = CorrectnessEvaluator(llm, temperature)
        self.relevance = RelevanceEvaluator(llm, temperature)
        self.groundedness = GroundednessEvaluator(llm, temperature)
        self.retrieval_relevance = RetrievalRelevanceEvaluator(llm, temperature)

        logger.info("Initialized comprehensive evaluator with all metrics")

    @traceable(name="comprehensive_evaluation")
    def evaluate_rag_pipeline(
        self,
        question: str,
        answer: str,
        retrieved_contexts: List[str],
        reference: Optional[str] = None
    ) -> Dict[str, EvaluationResult]:
        """
        评估完整的RAG流水线

        Args:
            question: 用户问题
            answer: 系统生成的答案
            retrieved_contexts: 检索到的上下文列表
            reference: 参考答案（可选）

        Returns:
            包含所有评估结果的字典

        Raises:
            RuntimeError: 评估失败
        """
        try:
            logger.info(f"Starting comprehensive RAG evaluation for question: {question[:50]}...")

            results = {}

            # 1. 检索相关性评估
            logger.info("Step 1/4: Evaluating retrieval relevance...")
            results["retrieval_relevance"] = self.retrieval_relevance.evaluate(
                RetrievalRelevanceInput(
                    question=question,
                    retrieved_contexts=retrieved_contexts
                )
            )

            # 2. 基础性评估
            logger.info("Step 2/4: Evaluating groundedness...")
            results["groundedness"] = self.groundedness.evaluate(
                GroundednessInput(
                    answer=answer,
                    retrieved_contexts=retrieved_contexts
                )
            )

            # 3. 相关性评估
            logger.info("Step 3/4: Evaluating relevance...")
            results["relevance"] = self.relevance.evaluate(
                RelevanceInput(
                    question=question,
                    answer=answer
                )
            )

            # 4. 正确性评估
            logger.info("Step 4/4: Evaluating correctness...")
            results["correctness"] = self.correctness.evaluate(
                CorrectnessInput(
                    question=question,
                    answer=answer,
                    reference=reference
                )
            )

            logger.info("Comprehensive evaluation completed successfully")
            return results

        except Exception as e:
            logger.error(f"Comprehensive evaluation failed: {e}")
            raise RuntimeError(f"Comprehensive evaluation failed: {e}") from e

    def summarize_results(self, results: Dict[str, EvaluationResult]) -> Dict[str, Any]:
        """
        汇总评估结果

        Args:
            results: 评估结果字典

        Returns:
            汇总统计信息
        """
        total_score = sum(r.score for r in results.values())
        avg_score = total_score / len(results)
        all_passed = all(r.passed for r in results.values())

        summary = {
            "average_score": round(avg_score, 2),
            "total_score": total_score,
            "max_possible_score": len(results) * 5,
            "all_passed": all_passed,
            "passed_count": sum(1 for r in results.values() if r.passed),
            "failed_count": sum(1 for r in results.values() if not r.passed),
            "individual_scores": {
                metric: result.score
                for metric, result in results.items()
            },
            "individual_passed": {
                metric: result.passed
                for metric, result in results.items()
            }
        }

        return summary


# ============================================================================
# 辅助函数
# ============================================================================

def create_evaluators(llm: BaseChatModel) -> Dict[str, BaseEvaluator]:
    """
    创建所有评估器实例

    Args:
        llm: 语言模型实例

    Returns:
        评估器字典
    """
    return {
        "correctness": CorrectnessEvaluator(llm),
        "relevance": RelevanceEvaluator(llm),
        "groundedness": GroundednessEvaluator(llm),
        "retrieval_relevance": RetrievalRelevanceEvaluator(llm),
        "comprehensive": ComprehensiveEvaluator(llm)
    }


def print_evaluation_result(result: EvaluationResult) -> None:
    """
    打印评估结果（格式化输出）

    Args:
        result: 评估结果对象
    """
    status = "通过" if result.passed else "未通过"
    print(f"\n{'='*60}")
    print(f"评估指标: {result.metric_name}")
    print(f"评分: {result.score}/5")
    print(f"状态: {status}")
    print(f"评估理由:")
    print(f"{result.reasoning}")
    if result.metadata:
        print(f"元数据: {result.metadata}")
    print(f"{'='*60}\n")


def print_comprehensive_summary(
    results: Dict[str, EvaluationResult],
    summary: Dict[str, Any]
) -> None:
    """
    打印综合评估汇总

    Args:
        results: 评估结果字典
        summary: 汇总统计信息
    """
    print("\n" + "="*60)
    print("综合评估汇总")
    print("="*60)
    print(f"平均分: {summary['average_score']}/5")
    print(f"总分: {summary['total_score']}/{summary['max_possible_score']}")
    print(f"通过数: {summary['passed_count']}/{len(results)}")
    print(f"整体状态: {'全部通过' if summary['all_passed'] else '部分未通过'}")
    print("\n各项指标得分:")
    for metric, score in summary['individual_scores'].items():
        status = "✓" if summary['individual_passed'][metric] else "✗"
        print(f"  {status} {metric}: {score}/5")
    print("="*60 + "\n")
