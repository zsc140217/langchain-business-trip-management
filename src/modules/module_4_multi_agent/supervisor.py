"""
Supervisor Agent
Routes queries to appropriate worker agents and integrates results

Architecture:
- Supervisor-Worker pattern (similar to LangChain's supervisor agent)
- LLM-based routing decisions
- Result integration and task completion detection

Responsibilities:
1. Query Analysis: Understand user intent and required capabilities
2. Task Routing: Decide which worker agent(s) to invoke
3. Result Integration: Combine worker results into coherent answer
4. Completion Detection: Determine when task is fully complete

Design Principles:
- Single Responsibility: Only routing and integration, no domain logic
- Explainability: Log routing decisions for debugging
- Fallback Handling: Graceful degradation if routing fails
"""
from typing import Dict, Any, List
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
import logging
import json
import re

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor agent for multi-agent orchestration

    Routes tasks to specialized worker agents:
    - policy_worker: Company policy queries
    - weather_worker: Weather information
    - itinerary_worker: Trip planning and itineraries

    Example:
        supervisor = SupervisorAgent(llm)
        result = supervisor.execute({
            "query": "Check weather in Beijing and recommend hotels",
            "context": {},
            "results": {},
            "iteration": 0
        })
        # Returns: {"next_agent": "weather_worker", "reason": "Need weather data first"}
    """

    def __init__(self, llm: BaseChatModel, temperature: float = 0.3):
        """
        Initialize supervisor agent

        Args:
            llm: Language model for routing decisions
            temperature: Lower temperature for consistent routing
        """
        self.llm = llm
        self.temperature = temperature
        self.available_workers = ["policy_worker", "weather_worker", "itinerary_worker"]

        logger.info(f"Supervisor initialized with workers: {self.available_workers}")

    @traceable(name="supervisor_execute")
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute supervisor logic: routing or integration

        Decision flow:
        1. If no results yet → Route to first worker
        2. If partial results → Route to next worker or integrate
        3. If all results → Integrate and return END

        Args:
            task: Task dictionary with:
                - query: User query
                - context: Shared context
                - results: Completed worker results
                - iteration: Current iteration count

        Returns:
            Dictionary with:
                - next_agent: Next worker or "END"
                - reason: Routing decision explanation
                - final_answer: (if next_agent is END) Integrated answer
        """
        query = task["query"]
        results = task.get("results", {})
        iteration = task.get("iteration", 0)

        logger.info(f"Supervisor: Analyzing query (iteration {iteration})")
        logger.debug(f"Completed workers: {list(results.keys())}")

        # Determine if task is complete
        if self._is_task_complete(query, results):
            logger.info("Supervisor: Task complete, integrating results")
            return self._integrate_results(query, results)

        # Route to next worker
        next_worker = self._route_to_worker(query, results)
        logger.info(f"Supervisor: Routing to {next_worker}")

        return {
            "next_agent": next_worker,
            "reason": self._explain_routing(query, next_worker, results)
        }

    def _is_task_complete(self, query: str, results: Dict[str, Any]) -> bool:
        """
        Determine if task is complete

        Task is complete when:
        1. All required workers have executed
        2. Query intent is satisfied

        Args:
            query: User query
            results: Completed worker results

        Returns:
            True if task complete, False otherwise
        """
        # Extract required workers from query
        required_workers = self._identify_required_workers(query)

        # Check if all required workers have results
        completed_workers = set(results.keys())
        missing_workers = required_workers - completed_workers

        if missing_workers:
            logger.debug(f"Missing workers: {missing_workers}")
            return False

        logger.debug("All required workers completed")
        return True

    def _identify_required_workers(self, query: str) -> set:
        """
        Identify which workers are needed for the query

        Uses keyword matching for efficiency (LLM alternative possible)

        Args:
            query: User query

        Returns:
            Set of required worker names
        """
        query_lower = query.lower()
        required = set()

        # Weather keywords
        if any(kw in query_lower for kw in ["天气", "气温", "温度", "下雨", "weather", "temperature"]):
            required.add("weather")

        # Policy keywords
        if any(kw in query_lower for kw in ["政策", "规定", "标准", "报销", "policy", "expense", "reimbursement"]):
            required.add("policy")

        # Itinerary keywords
        if any(kw in query_lower for kw in ["行程", "安排", "规划", "酒店", "推荐", "itinerary", "hotel", "plan"]):
            required.add("itinerary")

        # If no specific keywords, default to itinerary (general planning)
        if not required:
            required.add("itinerary")

        logger.debug(f"Required workers for query: {required}")
        return required

    def _route_to_worker(self, query: str, results: Dict[str, Any]) -> str:
        """
        Route to next worker

        Strategy:
        1. Check which workers have completed
        2. Select next worker based on priority and dependencies
        3. Weather → Policy → Itinerary (typical flow)

        Args:
            query: User query
            results: Completed worker results

        Returns:
            Next worker name
        """
        completed = set(results.keys())
        required = self._identify_required_workers(query)
        remaining = required - completed

        if not remaining:
            return "END"

        # Priority order: weather → policy → itinerary
        priority_order = ["weather", "policy", "itinerary"]

        for worker_type in priority_order:
            if worker_type in remaining:
                return f"{worker_type}_worker"

        # Should not reach here, but fallback to END
        return "END"

    def _explain_routing(self, query: str, next_worker: str, results: Dict[str, Any]) -> str:
        """
        Explain routing decision (for debugging/logging)

        Args:
            query: User query
            next_worker: Selected worker
            results: Completed results

        Returns:
            Explanation string
        """
        if next_worker == "END":
            return "All required tasks completed"

        reasons = {
            "weather_worker": "需要查询天气信息",
            "policy_worker": "需要查询公司政策",
            "itinerary_worker": "需要规划行程安排"
        }

        return reasons.get(next_worker, f"路由到 {next_worker}")

    @traceable(name="supervisor_integrate")
    def _integrate_results(self, query: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate worker results into final answer

        Uses LLM to combine multiple worker outputs into coherent response

        Args:
            query: Original user query
            results: Worker results dictionary

        Returns:
            Dictionary with next_agent="END" and final_answer
        """
        logger.info("Integrating results from workers")

        # Build context from results
        context_parts = []
        for worker, result in results.items():
            context_parts.append(f"**{worker}结果**:\n{result}")

        context_str = "\n\n".join(context_parts)

        # Integration prompt
        prompt = f"""你是企业差旅助手。请根据以下信息，给用户一个完整、连贯的回答。

用户问题：{query}

各模块查询结果：
{context_str}

要求：
1. 综合所有信息，给出完整回答
2. 语言连贯自然，不要简单罗列
3. 重点突出，结构清晰
4. 如果有建议或注意事项，请明确指出

请直接给出最终回答："""

        try:
            # Call LLM for integration
            messages = [
                SystemMessage(content="你是专业的企业差旅助手，擅长整合多源信息并给出专业建议。"),
                HumanMessage(content=prompt)
            ]

            response = self.llm.invoke(messages, temperature=self.temperature)
            final_answer = response.content.strip()

            logger.info("Integration completed successfully")

            return {
                "next_agent": "END",
                "final_answer": final_answer
            }

        except Exception as e:
            logger.error(f"Integration failed: {e}, returning raw results")

            # Fallback: concatenate results
            fallback_answer = f"查询完成，结果如下：\n\n{context_str}"

            return {
                "next_agent": "END",
                "final_answer": fallback_answer
            }

    def get_available_workers(self) -> List[str]:
        """
        Get list of available workers

        Returns:
            List of worker names
        """
        return self.available_workers.copy()


# ============================================================================
# Alternative: LLM-based Routing (More Flexible)
# ============================================================================

class LLMSupervisorAgent(SupervisorAgent):
    """
    LLM-based supervisor (alternative implementation)

    Uses LLM to make routing decisions instead of rule-based logic.
    More flexible but potentially less predictable.

    Trade-offs:
    + More adaptable to complex queries
    + Can handle edge cases better
    - Higher latency (extra LLM call)
    - Less deterministic routing
    - Higher cost
    """

    @traceable(name="llm_supervisor_route")
    def _route_to_worker(self, query: str, results: Dict[str, Any]) -> str:
        """
        LLM-based routing decision

        Args:
            query: User query
            results: Completed worker results

        Returns:
            Next worker name
        """
        completed = list(results.keys())

        prompt = f"""你是一个任务路由器。根据用户问题和已完成的任务，决定下一步该调用哪个Agent。

可用Agent：
- weather_worker: 查询天气信息
- policy_worker: 查询公司差旅政策
- itinerary_worker: 规划行程安排

用户问题：{query}

已完成任务：{completed if completed else "无"}

规则：
1. 如果问题已经完全回答，返回 END
2. 如果需要某个Agent的数据，返回对应的worker名称
3. 优先级：weather_worker → policy_worker → itinerary_worker

请只返回一个词：weather_worker、policy_worker、itinerary_worker 或 END"""

        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages, temperature=0.1)
            decision = response.content.strip()

            # Parse decision
            if "END" in decision.upper():
                return "END"

            for worker in self.available_workers:
                if worker in decision:
                    return worker

            # Fallback to rule-based
            logger.warning("LLM routing failed, falling back to rule-based")
            return super()._route_to_worker(query, results)

        except Exception as e:
            logger.error(f"LLM routing failed: {e}, using rule-based fallback")
            return super()._route_to_worker(query, results)
