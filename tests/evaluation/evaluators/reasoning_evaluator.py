"""
推理能力评估器 - 评估简单推理和复杂推理能力
"""
import json
import re
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from .llm_judge import get_judge


@dataclass
class ReasoningEvaluationResult:
    """推理评估结果"""
    test_id: str
    query: str
    system_answer: str

    # 评分（1-5分）
    reasoning_score: float  # 推理路径正确性
    accuracy_score: float   # 答案准确性
    speed_score: float      # 响应速度
    overall_score: float    # 综合得分

    # 详细信息
    reasoning_detail: str   # 推理评估详情
    missing_keywords: List[str]  # 缺失的关键词
    latency_ms: int        # 响应时间

    # 标记
    passed: bool           # 是否通过（overall >= 3）
    needs_review: bool     # 是否需要人工review


class SimpleReasoningEvaluator:
    """简单推理评估器"""

    def __init__(self):
        self.judge = get_judge()

    def evaluate(
        self,
        test_case: Dict,
        system_output: Dict
    ) -> ReasoningEvaluationResult:
        """
        评估简单推理能力

        Args:
            test_case: 测试用例（来自reasoning_simple.json）
            system_output: 系统输出 {
                'answer': str,
                'latency_ms': int,
                'retrieved_docs': List[str],
                'tool_calls': List[Dict]
            }

        Returns:
            评估结果
        """
        # 1. 推理路径正确性（LLM-as-Judge）
        reasoning_result = self._evaluate_reasoning_path(
            test_case,
            system_output
        )
        reasoning_score = reasoning_result['score']

        # 2. 答案准确性（代码规则）
        accuracy_score = self._evaluate_accuracy(
            test_case,
            system_output
        )

        # 3. 响应速度（代码规则）
        speed_score = self._evaluate_speed(
            system_output['latency_ms']
        )

        # 4. 综合得分
        overall_score = (
            reasoning_score * 0.5 +
            accuracy_score * 0.3 +
            speed_score * 0.2
        )

        # 5. 检查缺失关键词
        missing_keywords = self._check_keywords(
            test_case.get('expected_keywords', []),
            system_output['answer']
        )

        # 6. 判断是否需要review
        needs_review = (
            overall_score < 3 or
            reasoning_score < 2 or
            len(missing_keywords) > 0
        )

        return ReasoningEvaluationResult(
            test_id=test_case['id'],
            query=test_case['query'],
            system_answer=system_output['answer'],
            reasoning_score=reasoning_score,
            accuracy_score=accuracy_score,
            speed_score=speed_score,
            overall_score=overall_score,
            reasoning_detail=reasoning_result['reasoning'],
            missing_keywords=missing_keywords,
            latency_ms=system_output['latency_ms'],
            passed=(overall_score >= 3),
            needs_review=needs_review
        )

    def _evaluate_reasoning_path(
        self,
        test_case: Dict,
        system_output: Dict
    ) -> Dict:
        """评估推理路径正确性"""
        criteria = f"""
评估系统是否正确执行了推理步骤。

**期望推理路径**:
{test_case['expected_reasoning']}

请检查：
1. 是否识别出关键信息（如职级、地点、部门等）
2. 是否匹配到正确的规则/数据
3. 是否得出正确结论

评分标准：
- 5分：推理路径完全正确
- 4分：推理方向正确，细节有小瑕疵
- 3分：推理部分正确，但遗漏关键步骤
- 2分：推理逻辑混乱
- 1分：完全错误
"""
        return self.judge.judge_with_criteria(
            query=test_case['query'],
            system_output=system_output['answer'],
            criteria=criteria,
            purpose='simple_reasoning'
        )

    def _evaluate_accuracy(
        self,
        test_case: Dict,
        system_output: Dict
    ) -> float:
        """评估答案准确性（基于关键词匹配）"""
        answer = system_output['answer'].lower()
        expected_keywords = test_case.get('expected_keywords', [])

        if not expected_keywords:
            # 没有关键词要求，默认满分
            return 5.0

        matched = sum(
            1 for keyword in expected_keywords
            if keyword.lower() in answer
        )

        ratio = matched / len(expected_keywords)

        if ratio >= 1.0:
            return 5.0
        elif ratio >= 0.8:
            return 4.0
        elif ratio >= 0.6:
            return 3.0
        elif ratio >= 0.4:
            return 2.0
        else:
            return 1.0

    def _evaluate_speed(self, latency_ms: int) -> float:
        """评估响应速度"""
        if latency_ms < 1000:
            return 5.0
        elif latency_ms < 2000:
            return 4.0
        elif latency_ms < 3000:
            return 3.0
        elif latency_ms < 5000:
            return 2.0
        else:
            return 1.0

    def _check_keywords(
        self,
        expected_keywords: List[str],
        answer: str
    ) -> List[str]:
        """检查缺失的关键词"""
        answer_lower = answer.lower()
        missing = [
            kw for kw in expected_keywords
            if kw.lower() not in answer_lower
        ]
        return missing


class ComplexReasoningEvaluator:
    """复杂推理评估器"""

    def __init__(self):
        self.judge = get_judge()

    def evaluate(
        self,
        test_case: Dict,
        system_output: Dict
    ) -> ReasoningEvaluationResult:
        """
        评估复杂推理能力

        Args:
            test_case: 测试用例（来自reasoning_complex.json）
            system_output: 系统输出

        Returns:
            评估结果
        """
        # 1. 推理完整性（LLM-as-Judge）
        completeness_result = self._evaluate_completeness(
            test_case,
            system_output
        )
        completeness_score = completeness_result['score']

        # 2. 计算准确性（代码规则）
        calculation_score = self._evaluate_calculation(
            test_case,
            system_output
        )

        # 3. 工具调用正确性（代码规则）
        tool_score = self._evaluate_tool_usage(
            test_case,
            system_output
        )

        # 4. 综合得分
        overall_score = (
            completeness_score * 0.4 +
            calculation_score * 0.4 +
            tool_score * 0.2
        )

        # 5. 检查是否需要review
        needs_review = (
            overall_score < 3 or
            completeness_score < 2 or
            calculation_score < 2
        )

        return ReasoningEvaluationResult(
            test_id=test_case['id'],
            query=test_case['query'],
            system_answer=system_output['answer'],
            reasoning_score=completeness_score,
            accuracy_score=calculation_score,
            speed_score=tool_score,
            overall_score=overall_score,
            reasoning_detail=completeness_result['reasoning'],
            missing_keywords=[],
            latency_ms=system_output.get('latency_ms', 0),
            passed=(overall_score >= 3),
            needs_review=needs_review
        )

    def _evaluate_completeness(
        self,
        test_case: Dict,
        system_output: Dict
    ) -> Dict:
        """评估推理完整性"""
        criteria = f"""
评估系统是否完成了所有推理步骤。

**期望推理步骤** (共{test_case['reasoning_steps']}步):
{test_case['expected_reasoning']}

请检查：
- 是否遗漏了某些步骤？
- 中间计算是否正确？
- 逻辑链条是否连贯？

评分标准：
- 5分：所有步骤完整且正确
- 4分：步骤完整但有小错误
- 3分：遗漏1-2个步骤
- 2分：逻辑链断裂，多个步骤缺失
- 1分：完全错误
"""
        return self.judge.judge_with_criteria(
            query=test_case['query'],
            system_output=system_output['answer'],
            criteria=criteria,
            purpose='complex_reasoning'
        )

    def _evaluate_calculation(
        self,
        test_case: Dict,
        system_output: Dict
    ) -> float:
        """评估计算准确性"""
        expected_numbers = test_case.get('expected_numbers', [])

        if not expected_numbers:
            # 没有数字要求，跳过计算评估
            return 5.0

        answer = system_output['answer']

        # 提取答案中的所有数字
        actual_numbers = re.findall(r'\d+', answer)

        # 检查期望数字是否都出现
        matched = sum(
            1 for num in expected_numbers
            if num in actual_numbers
        )

        ratio = matched / len(expected_numbers)

        if ratio >= 1.0:
            return 5.0
        elif ratio >= 0.75:
            return 4.0
        elif ratio >= 0.5:
            return 3.0
        elif ratio >= 0.25:
            return 2.0
        else:
            return 1.0

    def _evaluate_tool_usage(
        self,
        test_case: Dict,
        system_output: Dict
    ) -> float:
        """评估工具调用正确性"""
        requires_tool = test_case.get('requires_tool', False)

        if not requires_tool:
            # 不需要工具，默认满分
            return 5.0

        tool_calls = system_output.get('tool_calls', [])
        expected_tool = test_case.get('expected_tool', '')

        if not tool_calls:
            # 需要工具但未调用
            return 1.0

        # 检查是否调用了正确的工具
        actual_tool = tool_calls[0].get('tool_name', '')

        if actual_tool == expected_tool:
            return 5.0
        elif actual_tool:
            # 调用了工具，但不是期望的
            return 3.0
        else:
            return 1.0


def run_reasoning_evaluation(
    test_data_path: str,
    system_responses: List[Dict],
    evaluator_type: str = 'simple'
) -> List[ReasoningEvaluationResult]:
    """
    运行推理能力评估

    Args:
        test_data_path: 测试数据文件路径
        system_responses: 系统响应列表 [{
            'test_id': str,
            'answer': str,
            'latency_ms': int,
            'tool_calls': List[Dict]
        }]
        evaluator_type: 'simple' or 'complex'

    Returns:
        评估结果列表
    """
    # 加载测试数据
    with open(test_data_path, 'r', encoding='utf-8') as f:
        test_data = json.load(f)

    test_cases = test_data['test_cases']

    # 创建评估器
    if evaluator_type == 'simple':
        evaluator = SimpleReasoningEvaluator()
    else:
        evaluator = ComplexReasoningEvaluator()

    # 创建响应映射
    response_map = {
        resp['test_id']: resp
        for resp in system_responses
    }

    # 评估
    results = []
    for test_case in test_cases:
        test_id = test_case['id']

        if test_id not in response_map:
            print(f"警告: 未找到测试用例 {test_id} 的系统响应")
            continue

        system_output = response_map[test_id]
        result = evaluator.evaluate(test_case, system_output)
        results.append(result)

    return results
