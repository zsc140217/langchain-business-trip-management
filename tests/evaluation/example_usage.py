"""
评估器使用示例

演示如何使用四大评测指标评估RAG系统
"""

import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi

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
    print_evaluation_result,
    print_comprehensive_summary,
)

# 加载环境变量
load_dotenv()


def example_1_correctness():
    """示例1: 答案正确性评估"""
    print("\n" + "="*60)
    print("示例1: 答案正确性评估")
    print("="*60)

    # 初始化LLM
    llm = ChatTongyi(
        model_name="qwen-plus",
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
    )

    # 创建评估器
    evaluator = CorrectnessEvaluator(llm)

    # 评估数据
    input_data = CorrectnessInput(
        question="公司差旅政策中，经理级别的每日住宿标准是多少？",
        answer="根据公司差旅政策，经理级别的每日住宿标准为500元人民币。",
        reference="经理级别的每日住宿标准为600元人民币。"  # 实际正确答案
    )

    # 执行评估
    result = evaluator.evaluate(input_data)

    # 打印结果
    print_evaluation_result(result)


def example_2_relevance():
    """示例2: 答案相关性评估"""
    print("\n" + "="*60)
    print("示例2: 答案相关性评估")
    print("="*60)

    # 初始化LLM
    llm = ChatTongyi(
        model_name="qwen-plus",
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
    )

    # 创建评估器
    evaluator = RelevanceEvaluator(llm)

    # 评估数据
    input_data = RelevanceInput(
        question="如何申请国际差旅？",
        answer="申请国际差旅需要提前2周提交申请，填写国际差旅申请表，说明出差目的、行程安排等。"
        "申请需要部门经理和总经理审批。另外，公司今年的营收增长了20%，市场份额也有所提升。"
    )

    # 执行评估
    result = evaluator.evaluate(input_data)

    # 打印结果
    print_evaluation_result(result)


def example_3_groundedness():
    """示例3: 基础性/忠实度评估"""
    print("\n" + "="*60)
    print("示例3: 基础性/忠实度评估")
    print("="*60)

    # 初始化LLM
    llm = ChatTongyi(
        model_name="qwen-plus",
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
    )

    # 创建评估器
    evaluator = GroundednessEvaluator(llm)

    # 评估数据
    input_data = GroundednessInput(
        answer="根据政策，员工级别的每日住宿标准为300元，经理级别为600元，总监级别为1000元。"
        "所有级别都可以乘坐高铁商务座，并且可以享受五星级酒店的免费早餐。",
        retrieved_contexts=[
            "第三条 住宿标准\n员工级别：每日住宿费不超过300元\n经理级别：每日住宿费不超过600元\n总监级别：每日住宿费不超过1000元",
            "第四条 交通标准\n国内差旅优先选择高铁二等座，特殊情况可申请商务座。\n飞机出行选择经济舱，3小时以上航程可申请公务舱。"
        ]
    )

    # 执行评估
    result = evaluator.evaluate(input_data)

    # 打印结果
    print_evaluation_result(result)


def example_4_retrieval_relevance():
    """示例4: 检索相关性评估"""
    print("\n" + "="*60)
    print("示例4: 检索相关性评估")
    print("="*60)

    # 初始化LLM
    llm = ChatTongyi(
        model_name="qwen-plus",
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
    )

    # 创建评估器
    evaluator = RetrievalRelevanceEvaluator(llm)

    # 评估数据
    input_data = RetrievalRelevanceInput(
        question="出差期间的餐费报销标准是什么？",
        retrieved_contexts=[
            "第五条 餐费标准\n国内差旅每日餐费补贴100元，国际差旅每日餐费补贴200元。实际支出超过标准需提供发票。",
            "第三条 住宿标准\n员工级别：每日住宿费不超过300元\n经理级别：每日住宿费不超过600元",
            "公司2024年年度工作总结：全年营收增长25%，员工满意度提升10个百分点。"
        ]
    )

    # 执行评估
    result = evaluator.evaluate(input_data)

    # 打印结果
    print_evaluation_result(result)


def example_5_comprehensive():
    """示例5: 综合评估（完整RAG流水线）"""
    print("\n" + "="*60)
    print("示例5: 综合评估（完整RAG流水线）")
    print("="*60)

    # 初始化LLM
    llm = ChatTongyi(
        model_name="qwen-plus",
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
    )

    # 创建综合评估器
    evaluator = ComprehensiveEvaluator(llm)

    # 模拟RAG流水线的输入输出
    question = "公司允许哪些级别的员工乘坐飞机公务舱？"
    answer = "根据公司差旅政策，经理及以上级别的员工在航程超过3小时的情况下可以申请乘坐飞机公务舱。"
    retrieved_contexts = [
        "第四条 交通标准\n国内差旅优先选择高铁二等座，特殊情况可申请商务座。\n"
        "飞机出行选择经济舱，3小时以上航程可申请公务舱（仅限经理及以上级别）。",
        "第二条 适用范围\n本政策适用于公司所有正式员工，包括普通员工、经理、总监和高管。"
    ]
    reference = "经理及以上级别的员工在航程超过3小时时可以申请乘坐公务舱。"

    # 执行综合评估
    results = evaluator.evaluate_rag_pipeline(
        question=question,
        answer=answer,
        retrieved_contexts=retrieved_contexts,
        reference=reference
    )

    # 打印各项指标结果
    for metric_name, result in results.items():
        print_evaluation_result(result)

    # 打印汇总信息
    summary = evaluator.summarize_results(results)
    print_comprehensive_summary(results, summary)


def example_6_batch_evaluation():
    """示例6: 批量评估多个问答对"""
    print("\n" + "="*60)
    print("示例6: 批量评估多个问答对")
    print("="*60)

    # 初始化LLM
    llm = ChatTongyi(
        model_name="qwen-plus",
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
    )

    # 创建综合评估器
    evaluator = ComprehensiveEvaluator(llm)

    # 测试数据集
    test_cases = [
        {
            "question": "员工级别的住宿标准是多少？",
            "answer": "员工级别的每日住宿费不超过300元。",
            "contexts": ["第三条 住宿标准\n员工级别：每日住宿费不超过300元"],
            "reference": "员工级别每日住宿费不超过300元。"
        },
        {
            "question": "国际差旅需要提前多久申请？",
            "answer": "国际差旅需要提前至少2周提交申请。",
            "contexts": ["第六条 申请流程\n国际差旅需提前2周申请，国内差旅提前3天申请。"],
            "reference": "国际差旅需提前2周申请。"
        }
    ]

    # 批量评估
    all_results = []
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- 测试案例 {i} ---")
        print(f"问题: {case['question']}")

        results = evaluator.evaluate_rag_pipeline(
            question=case["question"],
            answer=case["answer"],
            retrieved_contexts=case["contexts"],
            reference=case["reference"]
        )

        summary = evaluator.summarize_results(results)
        all_results.append({
            "case": i,
            "question": case["question"],
            "summary": summary
        })

        print(f"平均分: {summary['average_score']}/5")
        print(f"状态: {'通过' if summary['all_passed'] else '未通过'}")

    # 打印整体统计
    print("\n" + "="*60)
    print("批量评估整体统计")
    print("="*60)
    avg_scores = [r["summary"]["average_score"] for r in all_results]
    overall_avg = sum(avg_scores) / len(avg_scores)
    pass_count = sum(1 for r in all_results if r["summary"]["all_passed"])

    print(f"总测试案例数: {len(test_cases)}")
    print(f"整体平均分: {overall_avg:.2f}/5")
    print(f"全部通过案例数: {pass_count}/{len(test_cases)}")
    print(f"通过率: {pass_count/len(test_cases)*100:.1f}%")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LangChain企业差旅项目 - 评估器使用示例")
    print("="*60)

    # 运行所有示例
    try:
        example_1_correctness()
        example_2_relevance()
        example_3_groundedness()
        example_4_retrieval_relevance()
        example_5_comprehensive()
        example_6_batch_evaluation()

        print("\n所有示例运行完成！")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
