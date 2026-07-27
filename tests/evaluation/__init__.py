"""
评估模块

提供多种评测能力：
1. LLM-as-Judge评测指标实现 (evaluators.py)
2. 推理能力与工具使用评测 (evaluators/ 目录)
"""

# 旧版评估器导入（保持向后兼容）
try:
    from .evaluators import (
        EvaluationResult,
        CorrectnessInput,
        RelevanceInput,
        GroundednessInput,
        RetrievalRelevanceInput,
        BaseEvaluator,
        CorrectnessEvaluator,
        RelevanceEvaluator,
        GroundednessEvaluator,
        RetrievalRelevanceEvaluator,
        ComprehensiveEvaluator,
        create_evaluators,
        print_evaluation_result,
        print_comprehensive_summary,
    )

    __all__ = [
        "EvaluationResult",
        "CorrectnessInput",
        "RelevanceInput",
        "GroundednessInput",
        "RetrievalRelevanceInput",
        "BaseEvaluator",
        "CorrectnessEvaluator",
        "RelevanceEvaluator",
        "GroundednessEvaluator",
        "RetrievalRelevanceEvaluator",
        "ComprehensiveEvaluator",
        "create_evaluators",
        "print_evaluation_result",
        "print_comprehensive_summary",
    ]
except ImportError:
    # 如果evaluators.py不存在，只导出新版评估器
    __all__ = []
