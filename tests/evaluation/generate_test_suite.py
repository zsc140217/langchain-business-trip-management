"""
企业差旅助手 - 测试数据集生成器

根据企业差旅场景生成评估测试用例：
1. 简单场景 - 单一预订查询
2. 复杂场景 - 多步骤行程规划
3. 政策合规场景 - 测试预算和政策限制
4. 异常场景 - 航班取消、改签等
"""

from pathlib import Path
import json
import sys
from typing import List

# 添加路径以支持导入
sys.path.insert(0, str(Path(__file__).parent))

from comprehensive_eval_framework import (
    TestCase,
    QueryComplexity,
    AgentResponse
)


def create_test_suite() -> List[TestCase]:
    """创建完整的测试套件"""

    test_cases = []

    # ==================== 简单场景 ====================

    # 测试1: 基础机票查询
    test_cases.append(TestCase(
        task_id="simple_001",
        complexity=QueryComplexity.SIMPLE,
        user_query="帮我查询明天从上海到北京的经济舱机票",
        expected_tools=["search_flights"],
        expected_output_keywords=["上海", "北京", "经济舱", "价格"],
        forbidden_keywords=["商务舱", "头等舱"],
        policy_constraints={
            "max_budget": 2000,
            "allowed_flight_classes": ["economy"]
        },
        reference_answer="已为您找到明天从上海到北京的经济舱航班，CA1234次，08:30出发，10:45到达，价格1200元。",
        retrieved_contexts=[
            "航班CA1234: 上海浦东-北京首都，经济舱1200元",
            "航班MU5678: 上海虹桥-北京大兴，经济舱1150元"
        ],
        category="booking",
        metadata={"priority": "high"}
    ))

    # 测试2: 酒店查询
    test_cases.append(TestCase(
        task_id="simple_002",
        complexity=QueryComplexity.SIMPLE,
        user_query="推荐北京三环内四星级以下的酒店",
        expected_tools=["search_hotels"],
        expected_output_keywords=["北京", "酒店", "价格", "位置"],
        forbidden_keywords=["五星级", "奢华"],
        policy_constraints={
            "max_budget": 800,
            "max_hotel_rating": 4
        },
        reference_answer="推荐北京希尔顿酒店，四星级，位于朝阳区，房价650元/晚。",
        retrieved_contexts=[
            "希尔顿酒店：四星级，朝阳区，650元/晚",
            "如家酒店：三星级，海淀区，380元/晚"
        ],
        category="booking",
        metadata={"priority": "medium"}
    ))

    # 测试3: 天气查询
    test_cases.append(TestCase(
        task_id="simple_003",
        complexity=QueryComplexity.SIMPLE,
        user_query="北京明天天气怎么样？",
        expected_tools=["get_weather"],
        expected_output_keywords=["北京", "天气", "温度"],
        forbidden_keywords=[],
        policy_constraints={},
        reference_answer="北京明天晴，气温18-28度，适合出行。",
        retrieved_contexts=["北京天气预报：晴，18-28℃，空气质量良好"],
        category="weather",
        metadata={"priority": "low"}
    ))

    # ==================== 中等复杂度场景 ====================

    # 测试4: 机票+酒店组合查询
    test_cases.append(TestCase(
        task_id="medium_001",
        complexity=QueryComplexity.MEDIUM,
        user_query="我要去深圳出差3天，帮我订经济舱机票和酒店",
        expected_tools=["search_flights", "search_hotels"],
        expected_output_keywords=["深圳", "机票", "酒店", "总价"],
        forbidden_keywords=["商务舱"],
        policy_constraints={
            "max_budget": 4000,
            "allowed_flight_classes": ["economy"],
            "max_hotel_rating": 4
        },
        reference_answer="已为您规划深圳3日行程：往返经济舱机票2400元，酒店3晚1350元，总计3750元。",
        retrieved_contexts=[
            "深圳往返机票：经济舱2400元",
            "深圳锦江之星：三星级，450元/晚"
        ],
        category="booking",
        metadata={"priority": "high", "duration_days": 3}
    ))

    # 测试5: 政策查询+预订
    test_cases.append(TestCase(
        task_id="medium_002",
        complexity=QueryComplexity.MEDIUM,
        user_query="我想订商务舱去杭州，公司政策允许吗？",
        expected_tools=["check_policy", "search_flights"],
        expected_output_keywords=["政策", "经济舱", "建议"],
        forbidden_keywords=[],
        policy_constraints={
            "max_budget": 1500,
            "allowed_flight_classes": ["economy"]
        },
        reference_answer="根据公司差旅政策，国内航班仅允许预订经济舱。已为您查询经济舱航班，价格800元。",
        retrieved_contexts=[
            "差旅政策：国内航班限经济舱，预算1500元以内",
            "杭州经济舱航班：800元"
        ],
        category="policy",
        metadata={"priority": "high"}
    ))

    # ==================== 复杂场景 ====================

    # 测试6: 多城市行程规划
    test_cases.append(TestCase(
        task_id="complex_001",
        complexity=QueryComplexity.COMPLEX,
        user_query="我需要去北京、上海、深圳三地出差，每个城市停留2天，帮我规划最优路线和预订",
        expected_tools=["plan_itinerary", "search_flights", "search_hotels", "calculate_budget"],
        expected_output_keywords=["行程", "路线", "北京", "上海", "深圳", "总预算"],
        forbidden_keywords=["头等舱"],
        policy_constraints={
            "max_budget": 8000,
            "allowed_flight_classes": ["economy"],
            "max_hotel_rating": 4
        },
        reference_answer="已为您规划6日三城行程：北京(2天)->上海(2天)->深圳(2天)，机票4200元，酒店2700元，总计6900元。",
        retrieved_contexts=[
            "多城市航线推荐：北京-上海-深圳，总计4200元",
            "酒店预算：每城市2晚约900元"
        ],
        category="complex",
        metadata={"priority": "high", "cities": 3, "duration_days": 6}
    ))

    # 测试7: 紧急改签场景
    test_cases.append(TestCase(
        task_id="complex_002",
        complexity=QueryComplexity.COMPLEX,
        user_query="我的CA1234航班取消了，帮我改签到最近的航班",
        expected_tools=["check_flight_status", "search_alternative_flights", "rebooking"],
        expected_output_keywords=["改签", "航班", "时间", "费用"],
        forbidden_keywords=[],
        policy_constraints={
            "max_budget": 2500
        },
        reference_answer="CA1234航班已取消。为您改签到CA1236，12:30出发，补差价200元，改签费50元。",
        retrieved_contexts=[
            "CA1234航班状态：已取消",
            "备选航班CA1236：12:30出发，经济舱1400元"
        ],
        category="emergency",
        metadata={"priority": "critical"}
    ))

    # ==================== 政策合规测试 ====================

    # 测试8: 预算超标（应该被拒绝）
    test_cases.append(TestCase(
        task_id="policy_001_violation",
        complexity=QueryComplexity.SIMPLE,
        user_query="帮我订一张去上海的商务舱机票",
        expected_tools=["check_policy"],
        expected_output_keywords=["政策", "不允许", "经济舱"],
        forbidden_keywords=["商务舱"],
        policy_constraints={
            "max_budget": 1500,
            "allowed_flight_classes": ["economy"]
        },
        reference_answer="抱歉，根据公司差旅政策，国内航班仅允许预订经济舱。已为您查询经济舱航班。",
        retrieved_contexts=["差旅政策：国内航班限经济舱"],
        category="policy",
        metadata={"expected_violation": True}
    ))

    # 测试9: 酒店星级超标
    test_cases.append(TestCase(
        task_id="policy_002_violation",
        complexity=QueryComplexity.SIMPLE,
        user_query="我想住五星级酒店",
        expected_tools=["check_policy", "search_hotels"],
        expected_output_keywords=["政策", "四星", "建议"],
        forbidden_keywords=["五星"],
        policy_constraints={
            "max_hotel_rating": 4,
            "max_budget": 800
        },
        reference_answer="根据公司政策，酒店限四星级及以下。为您推荐四星级酒店。",
        retrieved_contexts=["差旅政策：酒店限四星级以下，预算800元/晚"],
        category="policy",
        metadata={"expected_violation": True}
    ))

    # ==================== 边缘案例 ====================

    # 测试10: 模糊查询
    test_cases.append(TestCase(
        task_id="edge_001",
        complexity=QueryComplexity.MEDIUM,
        user_query="我想出差",
        expected_tools=["clarify_requirements"],
        expected_output_keywords=["目的地", "日期", "需求"],
        forbidden_keywords=[],
        policy_constraints={},
        reference_answer="请问您的出差目的地、出发日期和预计停留天数是多少？",
        retrieved_contexts=[],
        category="clarification",
        metadata={"requires_followup": True}
    ))

    return test_cases


def create_mock_responses() -> List[AgentResponse]:
    """创建模拟的智能体响应（用于测试）"""

    responses = [
        # simple_001 - 正常响应
        AgentResponse(
            answer="已为您找到明天从上海到北京的经济舱航班：CA1234，08:30-10:45，价格1200元；MU5678，09:15-11:30，价格1150元。推荐MU5678性价比更高。",
            tool_calls=[
                {
                    "name": "search_flights",
                    "params": {"origin": "上海", "destination": "北京", "class": "economy"},
                    "result": {"flights": ["CA1234", "MU5678"]}
                }
            ],
            total_cost=1150,
            flight_class="economy",
            execution_time=1.2
        ),

        # simple_002 - 正常响应
        AgentResponse(
            answer="推荐以下北京三环内酒店：1) 希尔顿酒店，四星级，朝阳区，650元/晚；2) 如家酒店，三星级，海淀区，380元/晚。",
            tool_calls=[
                {
                    "name": "search_hotels",
                    "params": {"city": "北京", "max_rating": 4},
                    "result": {"hotels": ["希尔顿", "如家"]}
                }
            ],
            total_cost=650,
            hotel_rating=4,
            execution_time=0.8
        ),

        # simple_003 - 正常响应
        AgentResponse(
            answer="北京明天天气晴，气温18-28℃，空气质量良好，适合出行。建议穿轻便衣物。",
            tool_calls=[
                {
                    "name": "get_weather",
                    "params": {"city": "北京", "date": "明天"},
                    "result": {"weather": "晴", "temp": "18-28℃"}
                }
            ],
            total_cost=0,
            execution_time=0.5
        ),

        # medium_001 - 正常响应
        AgentResponse(
            answer="已为您规划深圳3日出差行程：\n往返经济舱机票：2400元\n锦江之星酒店3晚：1350元\n总计：3750元（符合预算）",
            tool_calls=[
                {"name": "search_flights", "params": {"destination": "深圳"}, "result": {}},
                {"name": "search_hotels", "params": {"city": "深圳", "nights": 3}, "result": {}}
            ],
            total_cost=3750,
            flight_class="economy",
            hotel_rating=3,
            execution_time=2.1
        ),

        # medium_002 - 政策拒绝
        AgentResponse(
            answer="根据公司差旅政策，国内航班仅允许预订经济舱。已为您查询杭州经济舱航班：CA9876，价格800元，符合政策要求。",
            tool_calls=[
                {"name": "check_policy", "params": {"query": "商务舱"}, "result": {"allowed": False}},
                {"name": "search_flights", "params": {"class": "economy"}, "result": {}}
            ],
            total_cost=800,
            flight_class="economy",
            execution_time=1.5
        ),

        # complex_001 - 复杂规划
        AgentResponse(
            answer="已为您规划6日三城行程：\n第1-2天：北京（酒店900元）\n第3-4天：上海（酒店900元）\n第5-6天：深圳（酒店900元）\n机票总计：4200元\n总预算：6900元",
            tool_calls=[
                {"name": "plan_itinerary", "params": {"cities": ["北京", "上海", "深圳"]}, "result": {}},
                {"name": "search_flights", "params": {}, "result": {}},
                {"name": "search_hotels", "params": {}, "result": {}},
                {"name": "calculate_budget", "params": {}, "result": {"total": 6900}}
            ],
            total_cost=6900,
            flight_class="economy",
            hotel_rating=4,
            execution_time=3.5
        ),

        # complex_002 - 紧急改签
        AgentResponse(
            answer="CA1234航班已取消。已为您改签到CA1236，12:30出发，14:45到达。补差价200元，改签费50元，总计250元。",
            tool_calls=[
                {"name": "check_flight_status", "params": {"flight": "CA1234"}, "result": {"status": "cancelled"}},
                {"name": "search_alternative_flights", "params": {}, "result": {}},
                {"name": "rebooking", "params": {"new_flight": "CA1236"}, "result": {}}
            ],
            total_cost=250,
            flight_class="economy",
            execution_time=2.0
        ),

        # policy_001_violation - 应该被拒绝（但这里模拟错误响应）
        AgentResponse(
            answer="已为您查询到上海商务舱机票，价格2800元。",
            tool_calls=[
                {"name": "search_flights", "params": {"class": "business"}, "result": {}}
            ],
            total_cost=2800,
            flight_class="business",  # 违反政策
            execution_time=1.0
        ),

        # policy_002_violation - 应该被拒绝
        AgentResponse(
            answer="已为您推荐五星级酒店，价格1200元/晚。",
            tool_calls=[
                {"name": "search_hotels", "params": {"rating": 5}, "result": {}}
            ],
            total_cost=1200,
            hotel_rating=5,  # 违反政策
            execution_time=0.9
        ),

        # edge_001 - 澄清需求
        AgentResponse(
            answer="我需要了解更多信息才能帮您规划出差：\n1. 您的目的地是哪里？\n2. 计划什么时候出发？\n3. 预计停留几天？",
            tool_calls=[
                {"name": "clarify_requirements", "params": {}, "result": {}}
            ],
            total_cost=0,
            execution_time=0.4
        ),
    ]

    return responses


def save_test_suite(output_dir: Path):
    """保存测试套件到文件"""
    output_dir.mkdir(parents=True, exist_ok=True)

    test_cases = create_test_suite()
    responses = create_mock_responses()

    # 保存测试用例
    test_cases_data = [
        {
            "task_id": tc.task_id,
            "complexity": tc.complexity.value,
            "user_query": tc.user_query,
            "expected_tools": tc.expected_tools,
            "expected_output_keywords": tc.expected_output_keywords,
            "forbidden_keywords": tc.forbidden_keywords,
            "policy_constraints": tc.policy_constraints,
            "reference_answer": tc.reference_answer,
            "retrieved_contexts": tc.retrieved_contexts,
            "category": tc.category,
            "metadata": tc.metadata
        }
        for tc in test_cases
    ]

    with open(output_dir / "test_cases.json", "w", encoding="utf-8") as f:
        json.dump(test_cases_data, f, ensure_ascii=False, indent=2)

    # 保存模拟响应
    responses_data = [
        {
            "answer": r.answer,
            "tool_calls": r.tool_calls,
            "total_cost": r.total_cost,
            "flight_class": r.flight_class,
            "hotel_rating": r.hotel_rating,
            "execution_time": r.execution_time,
            "metadata": r.metadata
        }
        for r in responses
    ]

    with open(output_dir / "mock_responses.json", "w", encoding="utf-8") as f:
        json.dump(responses_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] 测试套件已保存到 {output_dir}")
    print(f"   - 测试用例: {len(test_cases)} 个")
    print(f"   - 模拟响应: {len(responses)} 个")

    # 打印统计信息
    categories = {}
    for tc in test_cases:
        categories[tc.category] = categories.get(tc.category, 0) + 1

    print("\n场景分布:")
    for category, count in categories.items():
        print(f"   - {category}: {count}")


if __name__ == "__main__":
    output_dir = Path(__file__).parent / "test_data"
    save_test_suite(output_dir)
