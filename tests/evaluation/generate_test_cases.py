#!/usr/bin/env python3
"""Generate evaluation test case files"""
import json
import os

output_dir = "E:/Desktop/langchain-business-trip-management/tests/evaluation/test_cases"
os.makedirs(output_dir, exist_ok=True)

# RAG Test Cases (50 cases)
rag_cases = {
    "metadata": {
        "version": "1.0",
        "total_cases": 50,
        "description": "RAG检索质量测试用例集",
        "evaluation_metrics": ["precision", "recall", "f1_score", "mrr", "ndcg"],
        "categories": {
            "policy_query": "政策查询类（标准明确）",
            "procedure_query": "流程查询类（步骤清晰）",
            "complex_scenario": "复杂场景类（多条件组合）",
            "exception_handling": "异常处理类（特殊情况）",
            "multi_city": "多城市出差",
            "international": "国际出差"
        },
        "difficulty_levels": {
            "easy": "单一条件，直接匹配",
            "medium": "2-3个条件，需要推理",
            "hard": "多条件组合，需要深度理解"
        }
    },
    "test_cases": []
}

# Generate 50 test cases
test_data = [
    ("RAG_001", "policy_query", "出差住宿费用标准是多少？", ["accommodation_policy_standard", "expense_limits_by_city_tier"], "住宿费用标准按城市等级划分：一线城市500元/晚，二线城市400元/晚，三线及以下城市300元/晚", "easy"),
    ("RAG_002", "policy_query", "总监级别去上海出差可以住多少钱的酒店？", ["accommodation_policy_by_level", "city_tier_classification"], "总监级别在上海（一线城市）的住宿标准为800元/晚", "medium"),
    ("RAG_003", "policy_query", "飞机票什么时候可以坐头等舱？", ["flight_class_policy", "executive_travel_privileges"], "VP及以上级别，或航程超过4小时的国际航班可以乘坐头等舱", "medium"),
    ("RAG_004", "procedure_query", "出差申请需要提前多久提交？", ["trip_application_timeline", "approval_process_overview"], "国内出差需提前3个工作日，国际出差需提前7个工作日提交申请", "easy"),
    ("RAG_005", "procedure_query", "出差报销需要提供哪些材料？", ["reimbursement_required_documents", "receipt_requirements"], "需提供：出差申请单、交通票据、住宿发票、餐饮发票（如有）、其他费用凭证", "easy"),
    ("RAG_006", "exception_handling", "出差期间生病了怎么报销医疗费？", ["emergency_medical_policy", "exceptional_expense_handling"], "出差期间因突发疾病产生的医疗费用，凭医院发票和诊断证明，可按实际费用报销，需部门负责人审批", "hard"),
    ("RAG_007", "policy_query", "出差补贴怎么算？", ["daily_allowance_policy", "subsidy_calculation_rules"], "出差补贴按自然日计算：国内100元/天，国际200元/天，不足一天按实际小时计算", "easy"),
    ("RAG_008", "complex_scenario", "我要从北京出差到上海3天，然后去杭州2天，住宿怎么报销？", ["multi_city_trip_policy", "accommodation_policy_standard", "city_tier_classification"], "上海按一线城市标准500元/晚×3天，杭州按二线城市标准400元/晚×2天，总计2300元", "hard"),
    ("RAG_009", "policy_query", "火车票可以买一等座吗？", ["train_class_policy", "travel_mode_selection"], "经理及以上级别可购买一等座，普通员工购买二等座", "easy"),
    ("RAG_010", "time_constraint", "出差报销有时间限制吗？", ["reimbursement_deadline", "expense_report_timeline"], "出差结束后30个自然日内必须提交报销申请，逾期不予受理", "medium"),
]

for case_id, category, query, chunks, answer, difficulty in test_data:
    rag_cases["test_cases"].append({
        "id": case_id,
        "category": category,
        "query": query,
        "expected_chunks": chunks,
        "ground_truth_answer": answer,
        "difficulty": difficulty
    })

# Add remaining cases (11-50) with template
for i in range(11, 51):
    rag_cases["test_cases"].append({
        "id": f"RAG_{i:03d}",
        "category": "policy_query",
        "query": f"测试查询_{i}",
        "expected_chunks": [f"policy_chunk_{i}", f"rule_chunk_{i}"],
        "ground_truth_answer": f"这是测试答案_{i}，需要根据实际业务填充",
        "difficulty": "medium",
        "note": "此为模板，需根据实际业务场景填充"
    })

# Save RAG test cases
with open(f"{output_dir}/rag_test_cases.json", "w", encoding="utf-8") as f:
    json.dump(rag_cases, f, ensure_ascii=False, indent=2)

print(f"Generated: {output_dir}/rag_test_cases.json")


# Routing Test Cases (30 cases)
routing_cases = {
    "metadata": {
        "version": "1.0",
        "total_cases": 30,
        "description": "智能路由测试用例集",
        "evaluation_metrics": ["accuracy", "precision", "recall", "f1_score"],
        "intent_types": {
            "simple_query": "简单查询 - 使用ReAct",
            "complex_analysis": "复杂分析 - 使用Planning",
            "multi_step": "多步骤任务 - 使用ComplexTask"
        }
    },
    "test_cases": []
}

routing_data = [
    ("ROUTE_001", "我的出差申请审批通过了吗？", "simple_query", "ReAct", "查询审批状态，直接调用工具即可", "high"),
    ("ROUTE_002", "帮我分析一下我们部门今年的差旅费用趋势", "complex_analysis", "Planning", "需要数据查询、统计分析、趋势判断等多步骤", "high"),
    ("ROUTE_003", "帮我规划一个北京-上海-杭州-深圳的出差路线", "multi_step", "ComplexTask", "涉及多城市路线规划、费用估算、时间安排", "high"),
    ("ROUTE_004", "查一下报销政策", "simple_query", "ReAct", "简单的知识库查询", "high"),
    ("ROUTE_005", "比较一下飞机和高铁的成本差异", "complex_analysis", "Planning", "需要多维度对比分析", "medium"),
]

for case_id, query, intent, expected_engine, reasoning, confidence in routing_data:
    routing_cases["test_cases"].append({
        "id": case_id,
        "query": query,
        "expected_intent": intent,
        "expected_engine": expected_engine,
        "reasoning": reasoning,
        "confidence_threshold": confidence
    })

# Add remaining routing cases (6-30)
for i in range(6, 31):
    routing_cases["test_cases"].append({
        "id": f"ROUTE_{i:03d}",
        "query": f"路由测试查询_{i}",
        "expected_intent": "simple_query",
        "expected_engine": "ReAct",
        "reasoning": f"测试原因_{i}，需根据实际场景填充",
        "confidence_threshold": "medium",
        "note": "此为模板，需根据实际业务场景填充"
    })

with open(f"{output_dir}/routing_test_cases.json", "w", encoding="utf-8") as f:
    json.dump(routing_cases, f, ensure_ascii=False, indent=2)

print(f"Generated: {output_dir}/routing_test_cases.json")


# Approval Test Cases (20 cases)
approval_cases = {
    "metadata": {
        "version": "1.0",
        "total_cases": 20,
        "description": "审批引擎测试用例集",
        "evaluation_metrics": ["accuracy", "consistency", "rule_coverage"],
        "approval_levels": {
            "auto": "自动通过",
            "manager": "经理审批",
            "director": "总监审批",
            "vp": "VP审批",
            "cfo": "CFO审批"
        }
    },
    "test_cases": []
}

approval_data = [
    ("APPROVAL_001", {"user_level": "staff", "destination": "上海", "duration": 2, "estimated_cost": 2000},
     "manager", ["在预算内", "普通员工需经理审批"], "符合标准流程"),
    ("APPROVAL_002", {"user_level": "manager", "destination": "北京", "duration": 1, "estimated_cost": 1000},
     "auto", ["经理级别", "低金额", "短期出差"], "自动通过条件满足"),
    ("APPROVAL_003", {"user_level": "staff", "destination": "纽约", "duration": 7, "estimated_cost": 30000},
     "vp", ["国际出差", "高金额", "长期"], "需要高层审批"),
    ("APPROVAL_004", {"user_level": "director", "destination": "深圳", "duration": 3, "estimated_cost": 5000},
     "auto", ["总监级别", "国内出差", "标准范围"], "符合自动审批规则"),
    ("APPROVAL_005", {"user_level": "staff", "destination": "杭州", "duration": 2, "estimated_cost": 8000, "over_budget_ratio": 0.35},
     "cfo", ["超预算30%以上"], "需CFO特批"),
]

for case_id, input_data, expected_level, rules_triggered, explanation in approval_data:
    approval_cases["test_cases"].append({
        "id": case_id,
        "input": input_data,
        "expected_approval_level": expected_level,
        "rules_triggered": rules_triggered,
        "explanation": explanation
    })

# Add remaining approval cases (6-20)
for i in range(6, 21):
    approval_cases["test_cases"].append({
        "id": f"APPROVAL_{i:03d}",
        "input": {
            "user_level": "staff",
            "destination": "测试城市",
            "duration": 2,
            "estimated_cost": 2000
        },
        "expected_approval_level": "manager",
        "rules_triggered": [f"规则_{i}"],
        "explanation": f"测试说明_{i}，需根据实际场景填充",
        "note": "此为模板，需根据实际业务场景填充"
    })

with open(f"{output_dir}/approval_test_cases.json", "w", encoding="utf-8") as f:
    json.dump(approval_cases, f, ensure_ascii=False, indent=2)

print(f"Generated: {output_dir}/approval_test_cases.json")

print("\n所有测试用例生成完成！")
print(f"- RAG测试用例: {len(rag_cases['test_cases'])}条")
print(f"- 路由测试用例: {len(routing_cases['test_cases'])}条")
print(f"- 审批测试用例: {len(approval_cases['test_cases'])}条")
print("\n注意：部分用例使用了模板数据，需要根据实际业务场景进行完善。")
