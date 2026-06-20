"""
评估器单元测试

测试四大评测指标的实现
使用Mock LLM避免实际API调用
"""

import pytest
from unittest.mock import Mock, MagicMock
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage

from tests.evaluation import (
    CorrectnessEvaluator,
    RelevanceEvaluator,
    GroundednessEvaluator,
    RetrievalRelevanceEvaluator,
    ComprehensiveEvaluator,
    CorrectnessInput,
    RelevanceInput,
    GroundednessInput,
    RetrievalRelevanceInput,
)


# ============================================================================
# 测试工具
# ============================================================================

def create_mock_llm(response_content: str) -> BaseChatModel:
    """创建Mock LLM用于测试"""
    mock_llm = Mock(spec=BaseChatModel)

    # Mock invoke方法
    mock_response = AIMessage(content=response_content)
    mock_llm.invoke = Mock(return_value=mock_response)

    return mock_llm


# ============================================================================
# CorrectnessEvaluator测试
# ============================================================================

def test_correctness_evaluator_high_score():
    """测试正确性评估器 - 高分情况"""
    # 准备Mock LLM响应
    mock_response = """
    {
        "score": 5,
        "reasoning": "答案完全正确，信息准确无误，逻辑清晰，完美回答了用户的问题。"
    }
    """
    mock_llm = create_mock_llm(mock_response)

    # 创建评估器
    evaluator = CorrectnessEvaluator(mock_llm)

    # 准备输入数据
    input_data = CorrectnessInput(
        question="公司差旅政策中，经理级别的每日住宿标准是多少？",
        answer="根据公司差旅政策，经理级别的每日住宿标准为600元人民币。",
        reference="经理级别的每日住宿标准为600元人民币。"
    )

    # 执行评估
    result = evaluator.evaluate(input_data)

    # 验证结果
    assert result.score == 5
    assert result.passed is True
    assert result.metric_name == "correctness"
    assert "完全正确" in result.reasoning


def test_correctness_evaluator_low_score():
    """测试正确性评估器 - 低分情况"""
    mock_response = """
    {
        "score": 2,
        "reasoning": "答案包含错误信息，住宿标准不准确，需要修正。"
    }
    """
    mock_llm = create_mock_llm(mock_response)

    evaluator = CorrectnessEvaluator(mock_llm)

    input_data = CorrectnessInput(
        question="公司差旅政策中，经理级别的每日住宿标准是多少？",
        answer="根据公司差旅政策，经理级别的每日住宿标准为500元人民币。",
        reference="经理级别的每日住宿标准为600元人民币。"
    )

    result = evaluator.evaluate(input_data)

    assert result.score == 2
    assert result.passed is False
    assert "错误" in result.reasoning


# ============================================================================
# RelevanceEvaluator测试
# ============================================================================

def test_relevance_evaluator_relevant():
    """测试相关性评估器 - 相关答案"""
    mock_response = """
    {
        "score": 5,
        "reasoning": "答案完全切题，直接回答了用户的问题，没有无关内容。"
    }
    """
    mock_llm = create_mock_llm(mock_response)

    evaluator = RelevanceEvaluator(mock_llm)

    input_data = RelevanceInput(
        question="如何申请国际差旅？",
        answer="申请国际差旅需要提前2周提交申请，填写国际差旅申请表，说明出差目的、行程安排，并需要部门经理和总经理审批。"
    )

    result = evaluator.evaluate(input_data)

    assert result.score == 5
    assert result.passed is True
    assert result.metric_name == "relevance"


def test_relevance_evaluator_irrelevant():
    """测试相关性评估器 - 不相关答案"""
    mock_response = """
    {
        "score": 2,
        "reasoning": "答案包含大量无关信息，如公司营收数据，偏离了用户问题的核心。"
    }
    """
    mock_llm = create_mock_llm(mock_response)

    evaluator = RelevanceEvaluator(mock_llm)

    input_data = RelevanceInput(
        question="如何申请国际差旅？",
        answer="申请国际差旅需要填表。另外，公司今年的营收增长了20%，市场份额也有所提升。"
    )

    result = evaluator.evaluate(input_data)

    assert result.score == 2
    assert result.passed is False
    assert "无关" in result.reasoning


# ============================================================================
# GroundednessEvaluator测试
# ============================================================================

def test_groundedness_evaluator_grounded():
    """测试基础性评估器 - 有依据的答案"""
    mock_response = """
    {
        "score": 5,
        "reasoning": "答案完全基于检索上下文，所有陈述都能在提供的文档中找到明确来源，无任何幻觉。"
    }
    """
    mock_llm = create_mock_llm(mock_response)

    evaluator = GroundednessEvaluator(mock_llm)

    input_data = GroundednessInput(
        answer="根据政策，员工级别的每日住宿标准为300元，经理级别为600元。",
        retrieved_contexts=[
            "第三条 住宿标准\n员工级别：每日住宿费不超过300元\n经理级别：每日住宿费不超过600元"
        ]
    )

    result = evaluator.evaluate(input_data)

    assert result.score == 5
    assert result.passed is True
    assert result.metric_name == "groundedness"


def test_groundedness_evaluator_hallucination():
    """测试基础性评估器 - 存在幻觉的答案"""
    mock_response = """
    {
        "score": 2,
        "reasoning": "答案包含多处幻觉：五星级酒店免费早餐在检索上下文中完全没有提及，属于模型编造的信息。"
    }
    """
    mock_llm = create_mock_llm(mock_response)

    evaluator = GroundednessEvaluator(mock_llm)

    input_data = GroundednessInput(
        answer="员工级别的每日住宿标准为300元，并且可以享受五星级酒店的免费早餐。",
        retrieved_contexts=[
            "第三条 住宿标准\n员工级别：每日住宿费不超过300元"
        ]
    )

    result = evaluator.evaluate(input_data)

    assert result.score == 2
    assert result.passed is False
    assert "幻觉" in result.reasoning


# ============================================================================
# RetrievalRelevanceEvaluator测试
# ============================================================================

def test_retrieval_relevance_evaluator_relevant():
    """测试检索相关性评估器 - 相关的检索结果"""
    mock_response = """
    {
        "score": 5,
        "reasoning": "所有检索结果都高度相关，第一个结果直接回答了餐费报销的问题，能够充分回答用户提问。"
    }
    """
    mock_llm = create_mock_llm(mock_response)

    evaluator = RetrievalRelevanceEvaluator(mock_llm)

    input_data = RetrievalRelevanceInput(
        question="出差期间的餐费报销标准是什么？",
        retrieved_contexts=[
            "第五条 餐费标准\n国内差旅每日餐费补贴100元，国际差旅每日餐费补贴200元。"
        ]
    )

    result = evaluator.evaluate(input_data)

    assert result.score == 5
    assert result.passed is True
    assert result.metric_name == "retrieval_relevance"


def test_retrieval_relevance_evaluator_irrelevant():
    """测试检索相关性评估器 - 不相关的检索结果"""
    mock_response = """
    {
        "score": 2,
        "reasoning": "检索结果大部分不相关，包含了无关的公司工作总结，仅有少量有用信息。"
    }
    """
    mock_llm = create_mock_llm(mock_response)

    evaluator = RetrievalRelevanceEvaluator(mock_llm)

    input_data = RetrievalRelevanceInput(
        question="出差期间的餐费报销标准是什么？",
        retrieved_contexts=[
            "第三条 住宿标准\n员工级别：每日住宿费不超过300元",
            "公司2024年年度工作总结：全年营收增长25%，员工满意度提升10个百分点。"
        ]
    )

    result = evaluator.evaluate(input_data)

    assert result.score == 2
    assert result.passed is False


# ============================================================================
# ComprehensiveEvaluator测试
# ============================================================================

def test_comprehensive_evaluator():
    """测试综合评估器"""
    # 为不同的评估创建不同的响应
    responses = {
        0: '{"score": 5, "reasoning": "检索相关性很高"}',  # retrieval_relevance
        1: '{"score": 4, "reasoning": "答案基本基于检索内容"}',  # groundedness
        2: '{"score": 5, "reasoning": "答案高度相关"}',  # relevance
        3: '{"score": 5, "reasoning": "答案完全正确"}',  # correctness
    }

    call_count = [0]

    def mock_invoke_side_effect(messages, **kwargs):
        response_content = responses.get(call_count[0], '{"score": 5, "reasoning": "测试"}')
        call_count[0] += 1
        return AIMessage(content=response_content)

    mock_llm = Mock(spec=BaseChatModel)
    mock_llm.invoke = Mock(side_effect=mock_invoke_side_effect)

    evaluator = ComprehensiveEvaluator(mock_llm)

    # 执行综合评估
    results = evaluator.evaluate_rag_pipeline(
        question="测试问题",
        answer="测试答案",
        retrieved_contexts=["测试上下文1", "测试上下文2"],
        reference="参考答案"
    )

    # 验证结果
    assert len(results) == 4
    assert "correctness" in results
    assert "relevance" in results
    assert "groundedness" in results
    assert "retrieval_relevance" in results

    # 验证汇总功能
    summary = evaluator.summarize_results(results)
    assert "average_score" in summary
    assert "total_score" in summary
    assert "all_passed" in summary
    assert summary["average_score"] > 0


# ============================================================================
# 错误处理测试
# ============================================================================

def test_evaluator_invalid_json():
    """测试无效JSON响应的错误处理"""
    mock_llm = create_mock_llm("这不是有效的JSON")

    evaluator = CorrectnessEvaluator(mock_llm)

    input_data = CorrectnessInput(
        question="测试问题",
        answer="测试答案"
    )

    with pytest.raises(RuntimeError, match="evaluation failed"):
        evaluator.evaluate(input_data)


def test_evaluator_invalid_score():
    """测试无效分数的错误处理"""
    mock_response = """
    {
        "score": 10,
        "reasoning": "分数超出范围"
    }
    """
    mock_llm = create_mock_llm(mock_response)

    evaluator = CorrectnessEvaluator(mock_llm)

    input_data = CorrectnessInput(
        question="测试问题",
        answer="测试答案"
    )

    with pytest.raises(RuntimeError):
        evaluator.evaluate(input_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
