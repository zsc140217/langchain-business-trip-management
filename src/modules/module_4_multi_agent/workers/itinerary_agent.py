"""
Itinerary Planning Worker Agent
Specialized agent for trip planning and itinerary creation

Responsibilities:
- Create trip itineraries based on user requirements
- Integrate weather and policy information
- Provide hotel and transportation recommendations

Reuses:
- BaseAgent for common functionality
- Weather and Policy results from other agents
"""
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
import logging

logger = logging.getLogger(__name__)


class ItineraryWorkerAgent(BaseAgent):
    """
    Itinerary planning worker agent

    Creates comprehensive trip itineraries combining:
    - Weather information
    - Policy compliance
    - Hotel recommendations
    - Transportation suggestions

    Example:
        agent = ItineraryWorkerAgent(llm)
        result = agent.execute({
            "query": "去杭州出差3天",
            "context": {},
            "results": {
                "weather": "杭州：晴天，24°C",
                "policy": "住宿标准≤500元/晚"
            }
        })
    """

    def __init__(
        self,
        llm: BaseChatModel,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize itinerary worker agent

        Args:
            llm: Language model instance
            config: Agent configuration
        """
        super().__init__(
            name="ItineraryWorkerAgent",
            llm=llm,
            tools=[],
            config=config or {}
        )
        logger.info("ItineraryWorkerAgent initialized")

    @traceable(name="itinerary_worker_execute")
    def execute(self, task: Dict[str, Any]) -> str:
        """
        Execute itinerary planning task

        Args:
            task: Task dictionary with:
                - query: User query
                - context: Additional context
                - results: Results from other agents (weather, policy)

        Returns:
            Itinerary planning result
        """
        query = task.get("query", "")
        context = task.get("context", {})
        results = task.get("results", {})

        logger.info(f"ItineraryWorker: Processing query: {query}")

        try:
            # Extract trip details
            trip_details = self._extract_trip_details(query)

            # Build itinerary using LLM
            itinerary = self._build_itinerary(query, trip_details, results)

            logger.info("ItineraryWorker: Planning completed successfully")
            return itinerary

        except Exception as e:
            logger.error(f"ItineraryWorker failed: {e}")
            return f"行程规划失败：{str(e)}"

    def _extract_trip_details(self, query: str) -> Dict[str, Any]:
        """
        Extract trip details from query

        Args:
            query: User query

        Returns:
            Trip details dictionary
        """
        details = {
            "destination": None,
            "duration": None,
            "purpose": "business"
        }

        # Extract cities
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "武汉"]
        for city in cities:
            if city in query:
                details["destination"] = city
                break

        # Extract duration
        import re
        duration_match = re.search(r'(\d+)\s*[天日]', query)
        if duration_match:
            details["duration"] = int(duration_match.group(1))

        logger.debug(f"Extracted trip details: {details}")
        return details

    def _build_itinerary(
        self,
        query: str,
        trip_details: Dict[str, Any],
        other_results: Dict[str, Any]
    ) -> str:
        """
        Build comprehensive itinerary using LLM

        Args:
            query: Original query
            trip_details: Extracted trip details
            other_results: Results from other agents

        Returns:
            Formatted itinerary
        """
        # Build context from other agents
        context_parts = []

        if "weather" in other_results:
            context_parts.append(f"天气信息：{other_results['weather']}")

        if "policy" in other_results:
            context_parts.append(f"政策信息：{other_results['policy']}")

        context_str = "\n".join(context_parts) if context_parts else "无额外信息"

        # Build prompt
        prompt = f"""你是专业的企业差旅规划助手。请根据以下信息，制定一个详细的出差行程安排。

用户需求：{query}

目的地：{trip_details.get('destination', '未指定')}
出差天数：{trip_details.get('duration', '未指定')}

参考信息：
{context_str}

请提供以下内容：
1. **行程概览**：出差目的地和时间
2. **交通建议**：往返交通方式和时间
3. **住宿推荐**：符合公司政策的酒店推荐（2-3个选项）
4. **注意事项**：根据天气和政策的特别提醒
5. **预算估算**：大致费用预算

要求：
- 所有建议必须符合公司差旅政策
- 考虑天气因素给出合理建议
- 提供具体可行的方案
- 格式清晰，条理分明

请直接给出行程规划："""

        try:
            # Call LLM
            messages = [
                SystemMessage(content="你是专业的企业差旅规划助手，精通行程安排、酒店推荐和差旅政策。"),
                HumanMessage(content=prompt)
            ]

            response = self.llm.invoke(messages, temperature=0.7)
            itinerary = response.content.strip()

            return itinerary

        except Exception as e:
            logger.error(f"LLM call failed: {e}, using fallback")
            return self._fallback_itinerary(trip_details, other_results)

    def _fallback_itinerary(
        self,
        trip_details: Dict[str, Any],
        other_results: Dict[str, Any]
    ) -> str:
        """
        Fallback itinerary when LLM fails

        Args:
            trip_details: Trip details
            other_results: Results from other agents

        Returns:
            Basic itinerary
        """
        destination = trip_details.get("destination", "目的地")
        duration = trip_details.get("duration", "N")

        weather_info = other_results.get("weather", "天气信息未获取")
        policy_info = other_results.get("policy", "政策信息未获取")

        return f"""**出差行程规划**

**行程概览**
• 目的地：{destination}
• 出差天数：{duration}天

**交通建议**
• 往返交通：建议选择高铁或飞机经济舱
• 市内交通：公共交通或出租车

**住宿推荐**
• 推荐酒店：
  - 如家快捷酒店（经济型，约300元/晚）
  - 汉庭酒店（舒适型，约400元/晚）
  - 全季酒店（商务型，约500元/晚）

**参考信息**
• 天气：{weather_info}
• 政策：{policy_info}

**注意事项**
• 请根据天气准备合适衣物
• 住宿选择需符合公司标准
• 保留所有报销凭证

**预算估算**
• 交通费：约800-1500元
• 住宿费：约{300 * trip_details.get('duration', 3)}-{500 * trip_details.get('duration', 3)}元
• 餐饮费：约{160 * trip_details.get('duration', 3)}元
• 合计：约{1260 + 300 * trip_details.get('duration', 3)}-{2460 + 500 * trip_details.get('duration', 3)}元

[注意：这是基础规划，详细安排请根据实际情况调整]"""


# ============================================================================
# Test Code
# ============================================================================

if __name__ == "__main__":
    """
    Test ItineraryWorkerAgent
    """
    print("Testing ItineraryWorkerAgent...\n")

    from models.llm import get_llm

    try:
        llm = get_llm(temperature=0.7)
        agent = ItineraryWorkerAgent(llm)

        # Test queries
        test_queries = [
            {
                "query": "去杭州出差3天",
                "results": {
                    "weather": "杭州：晴天，24°C，适合出行",
                    "policy": "住宿标准：一线城市≤500元/晚"
                }
            },
            {
                "query": "下周去北京开会",
                "results": {}
            }
        ]

        for test_case in test_queries:
            query = test_case["query"]
            results = test_case.get("results", {})

            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"Other Results: {list(results.keys())}")
            print(f"{'='*60}")

            result = agent.execute({
                "query": query,
                "context": {"user_id": "test_user"},
                "results": results
            })

            print(f"Result:\n{result}")

        print("\n✅ ItineraryWorkerAgent test completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
