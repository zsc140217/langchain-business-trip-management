"""
工具使用能力评估器 - 评估工具选择、参数构造、结果解读
"""
import json
from typing import Dict, List
from dataclasses import dataclass
from .llm_judge import get_judge


@dataclass
class ToolEvaluationResult:
    """工具评估结果"""
    test_id: str
    query: str
    test_type: str  # tool_selection / tool_parameters / tool_interpretation

    # 评分
    primary_score: float    # 主要评分
    secondary_score: float  # 次要评分
    overall_score: float    # 综合得分

    # 详细信息
    evaluation_detail: str
    expected: str
    actual: str

    # 标记
    passed: bool
    needs_review: bool


class ToolSelectionEvaluator:
    """工具选择评估器"""

    def evaluate(
        self,
        test_case: Dict,
        system_output: Dict
    ) -> ToolEvaluationResult:
        """
        评估工具选择准确性

        Args:
            test_case: {
                'id': str,
                'query': str,
                'expected_tool': str,
                'reason': str
            }
            system_output: {
                'tool_calls': [{'tool_name': str, 'parameters': dict}]
            }
        """
        tool_calls = system_output.get('tool_calls', [])
        expected_tool = test_case['expected_tool']

        if not tool_calls:
            return ToolEvaluationResult(
                test_id=test_case['id'],
                query=test_case['query'],
                test_type='tool_selection',
                primary_score=1.0,
                secondary_score=5.0,
                overall_score=1.0,
                evaluation_detail='未调用任何工具',
                expected=expected_tool,
                actual='None',
                passed=False,
                needs_review=True
            )

        actual_tool = tool_calls[0]['tool_name']

        if actual_tool == expected_tool:
            score = 5.0
            detail = f"工具选择正确: {actual_tool}"
            passed = True
            needs_review = False
        else:
            score = 1.0
            detail = f"工具选择错误: 期望{expected_tool}，实际{actual_tool}"
            passed = False
            needs_review = True

        return ToolEvaluationResult(
            test_id=test_case['id'],
            query=test_case['query'],
            test_type='tool_selection',
            primary_score=score,
            secondary_score=5.0,
            overall_score=score,
            evaluation_detail=detail,
            expected=expected_tool,
            actual=actual_tool,
            passed=passed,
            needs_review=needs_review
        )


class ToolParametersEvaluator:
    """工具参数评估器"""

    def evaluate(
        self,
        test_case: Dict,
        system_output: Dict
    ) -> ToolEvaluationResult:
        """
        评估工具参数正确性

        Args:
            test_case: {
                'id': str,
                'query': str,
                'expected_tool_call': dict,
                'key_parameters': List[str]
            }
            system_output: {
                'tool_calls': [{'tool_name': str, 'parameters': dict}]
            }
        """
        tool_calls = system_output.get('tool_calls', [])

        if not tool_calls:
            return self._create_failed_result(
                test_case,
                '未调用工具',
                'N/A',
                'None'
            )

        actual_call = tool_calls[0]
        key_params = test_case['key_parameters']

        # 检查关键参数是否存在
        params_str = str(actual_call.get('parameters', {}))
        missing_params = [
            p for p in key_params
            if p not in params_str
        ]

        if not missing_params:
            param_score = 5.0
            detail = "所有关键参数都存在"
        elif len(missing_params) < len(key_params):
            param_score = 3.0
            detail = f"缺少部分参数: {missing_params}"
        else:
            param_score = 1.0
            detail = f"缺少所有关键参数: {missing_params}"

        passed = param_score >= 3
        needs_review = param_score < 4

        return ToolEvaluationResult(
            test_id=test_case['id'],
            query=test_case['query'],
            test_type='tool_parameters',
            primary_score=param_score,
            secondary_score=5.0,
            overall_score=param_score,
            evaluation_detail=detail,
            expected=str(key_params),
            actual=params_str,
            passed=passed,
            needs_review=needs_review
        )

    def _create_failed_result(
        self,
        test_case: Dict,
        detail: str,
        expected: str,
        actual: str
    ) -> ToolEvaluationResult:
        """创建失败结果"""
        return ToolEvaluationResult(
            test_id=test_case['id'],
            query=test_case['query'],
            test_type='tool_parameters',
            primary_score=1.0,
            secondary_score=5.0,
            overall_score=1.0,
            evaluation_detail=detail,
            expected=expected,
            actual=actual,
            passed=False,
            needs_review=True
        )


class ToolInterpretationEvaluator:
    """工具结果解读评估器"""

    def __init__(self):
        self.judge = get_judge()

    def evaluate(
        self,
        test_case: Dict,
        system_output: Dict
    ) -> ToolEvaluationResult:
        """
        评估工具结果解读能力

        Args:
            test_case: {
                'id': str,
                'query': str,
                'mock_tool_result': dict,
                'expected_answer': str,
                'interpretation_requirements': List[str]
            }
            system_output: {
                'answer': str
            }
        """
        # 1. 答案正确性（代码规则）
        correctness_score = self._evaluate_correctness(
            test_case,
            system_output
        )

        # 2. 解读完整性（LLM-as-Judge）
        interpretation_result = self._evaluate_interpretation(
            test_case,
            system_output
        )
        interpretation_score = interpretation_result['score']

        # 3. 综合得分
        overall_score = (
            correctness_score * 0.5 +
            interpretation_score * 0.5
        )

        passed = overall_score >= 3
        needs_review = overall_score < 4

        return ToolEvaluationResult(
            test_id=test_case['id'],
            query=test_case['query'],
            test_type='tool_interpretation',
            primary_score=correctness_score,
            secondary_score=interpretation_score,
            overall_score=overall_score,
            evaluation_detail=interpretation_result['reasoning'],
            expected=test_case['expected_answer'],
            actual=system_output['answer'],
            passed=passed,
            needs_review=needs_review
        )

    def _evaluate_correctness(
        self,
        test_case: Dict,
        system_output: Dict
    ) -> float:
        """评估答案正确性"""
        import re

        expected = test_case['expected_answer']
        actual = system_output['answer']

        # 提取数字
        expected_numbers = set(re.findall(r'\d+', expected))
        actual_numbers = set(re.findall(r'\d+', actual))

        if not expected_numbers:
            # 没有数字要求，基于文本相似度
            expected_lower = expected.lower()
            actual_lower = actual.lower()

            # 简单的包含检查
            if expected_lower in actual_lower:
                return 5.0
            else:
                return 3.0

        # 基于数字匹配
        matched = len(expected_numbers & actual_numbers)
        total = len(expected_numbers)
        ratio = matched / total if total > 0 else 0

        if ratio >= 1.0:
            return 5.0
        elif ratio >= 0.8:
            return 4.0
        elif ratio >= 0.6:
            return 3.0
        else:
            return 2.0

    def _evaluate_interpretation(
        self,
        test_case: Dict,
        system_output: Dict
    ) -> Dict:
        """评估解读完整性"""
        requirements = test_case['interpretation_requirements']
        criteria = f"""
评估系统是否正确解读了工具返回结果。

**工具返回**:
{json.dumps(test_case['mock_tool_result'], ensure_ascii=False, indent=2)}

**解读要求**:
{chr(10).join(f"- {r}" for r in requirements)}

请检查系统回答是否满足所有解读要求。

评分标准：
- 5分：所有要求都满足
- 4分：大部分要求满足
- 3分：部分要求满足
- 2分：仅满足少数要求
- 1分：未满足任何要求
"""
        return self.judge.judge_with_criteria(
            query=test_case['query'],
            system_output=system_output['answer'],
            criteria=criteria,
            purpose='tool_interpretation'
        )


def run_tool_evaluation(
    test_data_path: str,
    system_responses: List[Dict]
) -> List[ToolEvaluationResult]:
    """
    运行工具使用评估

    Args:
        test_data_path: 测试数据文件路径
        system_responses: 系统响应列表

    Returns:
        评估结果列表
    """
    # 加载测试数据
    with open(test_data_path, 'r', encoding='utf-8') as f:
        test_data = json.load(f)

    test_cases = test_data['test_cases']

    # 创建评估器
    evaluators = {
        'tool_selection': ToolSelectionEvaluator(),
        'tool_parameters': ToolParametersEvaluator(),
        'tool_interpretation': ToolInterpretationEvaluator()
    }

    # 创建响应映射
    response_map = {
        resp['test_id']: resp
        for resp in system_responses
    }

    # 评估
    results = []
    for test_case in test_cases:
        test_id = test_case['id']
        test_type = test_case['test_type']

        if test_id not in response_map:
            print(f"警告: 未找到测试用例 {test_id} 的系统响应")
            continue

        evaluator = evaluators[test_type]
        system_output = response_map[test_id]
        result = evaluator.evaluate(test_case, system_output)
        results.append(result)

    return results
