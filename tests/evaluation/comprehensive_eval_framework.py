"""
企业差旅助手 - 综合评估框架
整合三层评分器：Code-based + Model-based + Human

基于 Anthropic 最佳实践设计：
1. Code-based (20-30%): 快速筛查明显错误（工具调用、政策合规）
2. Model-based (50-70%): 语义质量评估（使用现有 evaluators.py）
3. Human (10-20%): 校准和边缘案例

参考文档：
- AI_Agent_Eval系统总结.md
- 企业出差助手智能体_Eval需求问卷.md
"""

import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import logging

# 导入现有的 LLM-as-Judge 评估器
try:
    from .evaluators import (
        ComprehensiveEvaluator,
        CorrectnessInput,
        RelevanceInput,
        GroundednessInput,
        EvaluationResult as LLMEvalResult
    )
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from evaluators import (
        ComprehensiveEvaluator,
        CorrectnessInput,
        RelevanceInput,
        GroundednessInput,
        EvaluationResult as LLMEvalResult
    )

logger = logging.getLogger(__name__)


# ==================== 核心数据结构 ====================

class QueryComplexity(str, Enum):
    """查询复杂度（与系统现有的复杂度评估对应）"""
    SIMPLE = "simple"      # 单工具调用
    MEDIUM = "medium"      # 多工具调用
    COMPLEX = "complex"    # 需要任务分解


class ScoreLevel(str, Enum):
    """评分等级"""
    CRITICAL = "critical"  # 阻断问题 - 必须修复
    HIGH = "high"          # 严重问题 - 应该修复
    MEDIUM = "medium"      # 中等问题 - 考虑修复
    LOW = "low"            # 轻微问题 - 可选修复
    PASS = "pass"          # 通过


@dataclass
class TestCase:
    """评估测试用例"""
    task_id: str
    complexity: QueryComplexity
    user_query: str

    # 预期行为
    expected_tools: List[str]  # 应该调用的工具
    expected_output_keywords: List[str]  # 输出应包含的关键词
    forbidden_keywords: List[str]  # 输出不应包含的词

    # 政策约束
    policy_constraints: Dict[str, Any]  # 如 {"max_budget": 3000, "allowed_flight_classes": ["economy"]}

    # 用于 LLM 评估
    reference_answer: Optional[str] = None  # 参考答案
    retrieved_contexts: Optional[List[str]] = None  # 检索上下文

    # 元数据
    category: str = "general"  # 场景分类：booking, policy, weather, complex
    metadata: Dict[str, Any] = None


@dataclass
class AgentResponse:
    """智能体响应"""
    answer: str
    tool_calls: List[Dict[str, Any]]  # [{"name": "tool_name", "params": {...}, "result": ...}]
    total_cost: float = 0.0
    flight_class: str = ""
    hotel_rating: int = 0
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None


@dataclass
class CodeBasedEvalResult:
    """确定性评估结果"""
    score: float  # 0-1
    level: ScoreLevel
    dimensions: Dict[str, float]  # {"tool_accuracy": 1.0, "policy_compliance": 0.8}
    violations: List[Dict[str, Any]]  # 违规列表
    details: str
    execution_time: float


@dataclass
class FinalEvalResult:
    """最终综合评估结果"""
    task_id: str
    final_score: float  # 0-1
    final_level: ScoreLevel

    # 各层评分
    code_based_score: float
    model_based_score: Optional[float]
    human_score: Optional[float]

    # 详细结果
    code_based_details: CodeBasedEvalResult
    model_based_details: Optional[Dict[str, Any]]
    human_comments: Optional[str]

    # 统计
    total_time: float
    timestamp: str


# ==================== Layer 1: Code-based 确定性评分器 ====================

class CodeBasedGrader:
    """
    确定性规则检查器

    优势：
    - 100% 可重现
    - 执行快速 (<10ms)
    - 零成本（不调用 LLM）

    检查项：
    1. 工具调用准确性
    2. 差旅政策合规性
    3. 输出格式正确性
    """

    def __init__(self):
        self.name = "code_based_grader"

    def check_tool_calls(
        self,
        response: AgentResponse,
        expected_tools: List[str]
    ) -> Dict[str, Any]:
        """检查工具调用准确性"""
        actual_tool_names = [t["name"] for t in response.tool_calls]

        missing_tools = set(expected_tools) - set(actual_tool_names)
        extra_tools = set(actual_tool_names) - set(expected_tools)

        # 计分逻辑
        score = 1.0
        if missing_tools:
            score -= 0.4 * len(missing_tools)  # 缺少必需工具严重扣分
        if extra_tools:
            score -= 0.1 * len(extra_tools)  # 多余工具轻微扣分

        return {
            "score": max(0, score),
            "missing_tools": list(missing_tools),
            "extra_tools": list(extra_tools),
            "actual_tools": actual_tool_names,
            "passed": score >= 0.7
        }

    def check_policy_compliance(
        self,
        response: AgentResponse,
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        检查差旅政策合规性

        这是 CRITICAL 维度：违反政策直接阻断
        """
        violations = []
        score = 1.0

        # 1. 预算限制（CRITICAL）
        if "max_budget" in constraints:
            if response.total_cost > constraints["max_budget"]:
                violations.append({
                    "type": "budget_exceeded",
                    "severity": "critical",
                    "actual": response.total_cost,
                    "limit": constraints["max_budget"],
                    "message": f"预算超标：{response.total_cost} > {constraints['max_budget']}"
                })
                score = 0  # 预算超标直接零分

        # 2. 舱位限制（HIGH）
        if "allowed_flight_classes" in constraints and response.flight_class:
            allowed = constraints["allowed_flight_classes"]
            if response.flight_class not in allowed:
                violations.append({
                    "type": "flight_class_violation",
                    "severity": "high",
                    "actual": response.flight_class,
                    "allowed": allowed,
                    "message": f"舱位不符合政策：{response.flight_class} 不在 {allowed} 中"
                })
                score -= 0.5

        # 3. 酒店星级限制（MEDIUM）
        if "max_hotel_rating" in constraints and response.hotel_rating:
            if response.hotel_rating > constraints["max_hotel_rating"]:
                violations.append({
                    "type": "hotel_rating_exceeded",
                    "severity": "medium",
                    "actual": response.hotel_rating,
                    "limit": constraints["max_hotel_rating"],
                    "message": f"酒店星级超标：{response.hotel_rating} > {constraints['max_hotel_rating']}"
                })
                score -= 0.3

        return {
            "score": max(0, score),
            "violations": violations,
            "compliant": len(violations) == 0,
            "critical_violations": [v for v in violations if v["severity"] == "critical"]
        }

    def check_output_keywords(
        self,
        response: AgentResponse,
        expected: List[str],
        forbidden: List[str]
    ) -> Dict[str, Any]:
        """检查输出关键词"""
        answer_lower = response.answer.lower()

        missing_keywords = [k for k in expected if k.lower() not in answer_lower]
        forbidden_found = [k for k in forbidden if k.lower() in answer_lower]

        score = 1.0
        if missing_keywords:
            score -= 0.15 * len(missing_keywords)
        if forbidden_found:
            score -= 0.25 * len(forbidden_found)  # 包含禁用词扣分更重

        return {
            "score": max(0, score),
            "missing_keywords": missing_keywords,
            "forbidden_found": forbidden_found,
            "passed": score >= 0.7
        }

    def evaluate(
        self,
        test_case: TestCase,
        response: AgentResponse
    ) -> CodeBasedEvalResult:
        """执行完整的确定性评估"""
        start_time = time.time()

        # 三个维度检查
        tool_check = self.check_tool_calls(response, test_case.expected_tools)
        policy_check = self.check_policy_compliance(response, test_case.policy_constraints)
        keyword_check = self.check_output_keywords(
            response,
            test_case.expected_output_keywords,
            test_case.forbidden_keywords
        )

        # 加权计算（政策合规权重最高）
        dimensions = {
            "tool_accuracy": tool_check["score"],
            "policy_compliance": policy_check["score"],
            "output_format": keyword_check["score"]
        }

        total_score = (
            0.3 * tool_check["score"] +
            0.5 * policy_check["score"] +  # 政策合规最重要
            0.2 * keyword_check["score"]
        )

        # 确定级别
        if policy_check["critical_violations"]:
            level = ScoreLevel.CRITICAL
        elif total_score < 0.5:
            level = ScoreLevel.HIGH
        elif total_score < 0.7:
            level = ScoreLevel.MEDIUM
        elif total_score < 0.9:
            level = ScoreLevel.LOW
        else:
            level = ScoreLevel.PASS

        # 汇总详情
        details = f"""
工具调用: {'✓' if tool_check['passed'] else '✗'} {tool_check['score']:.2f}
政策合规: {'✓' if policy_check['compliant'] else '✗'} {policy_check['score']:.2f}
输出格式: {'✓' if keyword_check['passed'] else '✗'} {keyword_check['score']:.2f}
        """.strip()

        return CodeBasedEvalResult(
            score=total_score,
            level=level,
            dimensions=dimensions,
            violations=policy_check["violations"],
            details=details,
            execution_time=time.time() - start_time
        )


# ==================== Layer 2: Model-based 评分器（集成现有）====================

class ModelBasedGraderAdapter:
    """
    Model-based 评分器适配器
    封装现有的 LLM-as-Judge 评估器
    """

    def __init__(self, llm):
        self.evaluator = ComprehensiveEvaluator(llm, temperature=0.0)
        self.name = "model_based_grader"

    def evaluate(
        self,
        test_case: TestCase,
        response: AgentResponse
    ) -> Dict[str, Any]:
        """
        使用现有的 LLM-as-Judge 评估器

        评估维度：
        1. Correctness - 答案正确性
        2. Relevance - 答案相关性
        3. Groundedness - 基于检索上下文（如果有）
        4. Retrieval Relevance - 检索质量（如果有）
        """
        start_time = time.time()

        try:
            # 调用现有评估器
            llm_results = self.evaluator.evaluate_rag_pipeline(
                question=test_case.user_query,
                answer=response.answer,
                retrieved_contexts=test_case.retrieved_contexts or [],
                reference=test_case.reference_answer
            )

            # 提取分数
            scores = {
                metric: result.score / 5.0  # 归一化到 0-1
                for metric, result in llm_results.items()
            }

            # 计算加权平均
            weights = {
                "correctness": 0.35,
                "relevance": 0.30,
                "groundedness": 0.20,
                "retrieval_relevance": 0.15
            }

            total_score = sum(
                scores.get(metric, 0.5) * weight
                for metric, weight in weights.items()
            )

            return {
                "score": total_score,
                "individual_scores": scores,
                "llm_results": {
                    metric: {
                        "score": result.score,
                        "reasoning": result.reasoning,
                        "passed": result.passed
                    }
                    for metric, result in llm_results.items()
                },
                "execution_time": time.time() - start_time
            }

        except Exception as e:
            logger.error(f"Model-based evaluation failed: {e}")
            return {
                "score": 0.5,  # 失败时返回中等分数
                "error": str(e),
                "execution_time": time.time() - start_time
            }


# ==================== Layer 3: Human 评分器 ====================

class HumanGrader:
    """
    人工评审器

    用途：
    1. 校准 Model-based 评分器
    2. 处理边缘案例
    3. 构建黄金数据集
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.name = "human_grader"

    def save_for_review(
        self,
        test_case: TestCase,
        response: AgentResponse,
        code_result: CodeBasedEvalResult,
        model_result: Optional[Dict[str, Any]]
    ) -> Path:
        """保存待人工审核的案例"""
        review_case = {
            "task_id": test_case.task_id,
            "test_case": asdict(test_case),
            "response": asdict(response),
            "evaluations": {
                "code_based": asdict(code_result),
                "model_based": model_result
            },
            "human_review": {
                "score": None,
                "level": None,
                "comments": "",
                "dimensions": {},
                "reviewer": "",
                "reviewed_at": None,
                "should_add_to_golden_set": False
            }
        }

        filepath = self.output_dir / f"{test_case.task_id}_review.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(review_case, f, ensure_ascii=False, indent=2)

        return filepath

    def load_human_score(self, task_id: str) -> Optional[Dict[str, Any]]:
        """加载人工评分结果"""
        filepath = self.output_dir / f"{task_id}_review.json"
        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        human_review = data["human_review"]
        if human_review["score"] is None:
            return None  # 尚未评审

        return human_review


# ==================== 综合评估引擎 ====================

class ComprehensiveEvalEngine:
    """
    三层评分器集成引擎

    评分器组合策略：
    - 快速任务：80% code-based + 20% model-based
    - 复杂任务：30% code-based + 60% model-based + 10% human
    """

    def __init__(self, llm, output_dir: Path):
        self.code_grader = CodeBasedGrader()
        self.model_grader = ModelBasedGraderAdapter(llm)
        self.human_grader = HumanGrader(output_dir / "human_reviews")

    def evaluate(
        self,
        test_case: TestCase,
        response: AgentResponse,
        use_model_grader: bool = True,
        save_for_human: bool = False
    ) -> FinalEvalResult:
        """执行完整评估"""
        start_time = time.time()

        # Layer 1: Code-based（总是执行）
        logger.info(f"[{test_case.task_id}] Running code-based evaluation...")
        code_result = self.code_grader.evaluate(test_case, response)

        # Layer 2: Model-based（可选）
        model_result = None
        model_score = None
        if use_model_grader:
            logger.info(f"[{test_case.task_id}] Running model-based evaluation...")
            model_result = self.model_grader.evaluate(test_case, response)
            model_score = model_result["score"]

        # Layer 3: Human（保存待审核）
        human_score = None
        human_comments = None
        if save_for_human:
            filepath = self.human_grader.save_for_review(
                test_case, response, code_result, model_result
            )
            logger.info(f"[{test_case.task_id}] Saved for human review: {filepath}")

        # 检查是否已有人工评分
        human_review = self.human_grader.load_human_score(test_case.task_id)
        if human_review:
            human_score = human_review["score"]
            human_comments = human_review["comments"]

        # 计算最终得分
        final_score, final_level = self._calculate_final_score(
            code_result, model_score, human_score
        )

        return FinalEvalResult(
            task_id=test_case.task_id,
            final_score=final_score,
            final_level=final_level,
            code_based_score=code_result.score,
            model_based_score=model_score,
            human_score=human_score,
            code_based_details=code_result,
            model_based_details=model_result,
            human_comments=human_comments,
            total_time=time.time() - start_time,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )

    def _calculate_final_score(
        self,
        code_result: CodeBasedEvalResult,
        model_score: Optional[float],
        human_score: Optional[float]
    ) -> tuple[float, ScoreLevel]:
        """计算最终综合得分"""
        # 如果有人工评分，优先使用
        if human_score is not None:
            final_score = human_score
        # 否则融合 code-based 和 model-based
        elif model_score is not None:
            final_score = 0.6 * code_result.score + 0.4 * model_score
        else:
            final_score = code_result.score

        # 如果 code-based 发现 CRITICAL 问题，直接阻断
        if code_result.level == ScoreLevel.CRITICAL:
            final_level = ScoreLevel.CRITICAL
        elif final_score >= 0.85:
            final_level = ScoreLevel.PASS
        elif final_score >= 0.70:
            final_level = ScoreLevel.LOW
        elif final_score >= 0.50:
            final_level = ScoreLevel.MEDIUM
        else:
            final_level = ScoreLevel.HIGH

        return final_score, final_level


# ==================== 批量评估和报告生成 ====================

class BatchEvaluator:
    """批量评估器"""

    def __init__(self, engine: ComprehensiveEvalEngine):
        self.engine = engine

    def evaluate_batch(
        self,
        test_cases: List[TestCase],
        responses: List[AgentResponse],
        use_model_grader: bool = True
    ) -> List[FinalEvalResult]:
        """批量评估"""
        results = []
        for test_case, response in zip(test_cases, responses):
            result = self.engine.evaluate(test_case, response, use_model_grader)
            results.append(result)
        return results

    def generate_report(
        self,
        results: List[FinalEvalResult],
        output_path: Path
    ) -> Dict[str, Any]:
        """生成评估报告"""
        total = len(results)

        # 统计各级别分布
        level_counts = {}
        for r in results:
            level = r.final_level.value
            level_counts[level] = level_counts.get(level, 0) + 1

        # 计算平均分
        avg_score = sum(r.final_score for r in results) / total
        pass_rate = level_counts.get(ScoreLevel.PASS.value, 0) / total

        # 按复杂度统计
        complexity_stats = {}
        # 需要从 test_cases 获取复杂度信息（这里简化处理）

        # 找出失败案例
        failures = [
            {
                "task_id": r.task_id,
                "score": r.final_score,
                "level": r.final_level.value,
                "violations": r.code_based_details.violations
            }
            for r in results
            if r.final_level in [ScoreLevel.CRITICAL, ScoreLevel.HIGH]
        ]

        report = {
            "summary": {
                "total_tasks": total,
                "average_score": round(avg_score, 3),
                "pass_rate": round(pass_rate, 3),
                "level_distribution": level_counts,
                "critical_count": level_counts.get(ScoreLevel.CRITICAL.value, 0),
                "total_time": sum(r.total_time for r in results)
            },
            "failures": failures,
            "top_performers": [
                {"task_id": r.task_id, "score": r.final_score}
                for r in sorted(results, key=lambda x: x.final_score, reverse=True)[:5]
            ],
            "bottom_performers": [
                {"task_id": r.task_id, "score": r.final_score}
                for r in sorted(results, key=lambda x: x.final_score)[:5]
            ]
        }

        # 保存报告
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"Report saved to {output_path}")
        return report


# ==================== 导出 ====================

__all__ = [
    "TestCase",
    "AgentResponse",
    "CodeBasedEvalResult",
    "FinalEvalResult",
    "CodeBasedGrader",
    "ModelBasedGraderAdapter",
    "HumanGrader",
    "ComprehensiveEvalEngine",
    "BatchEvaluator",
    "QueryComplexity",
    "ScoreLevel"
]
