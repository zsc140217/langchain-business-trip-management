"""
Policy Query Worker Agent
Specialized agent for querying company travel policies

Responsibilities:
- Query travel policies using RAG
- Extract policy information (accommodation, meals, transportation)
- Provide policy compliance guidance

Reuses:
- BaseAgent for common functionality
- EnterpriseHybridRetriever for policy search
"""
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
import logging

logger = logging.getLogger(__name__)


class PolicyWorkerAgent(BaseAgent):
    """
    Policy query worker agent

    Queries company travel policies using RAG system.
    Provides specific policy information and compliance guidance.

    Example:
        agent = PolicyWorkerAgent(llm, rag_chain)
        result = agent.execute({
            "query": "北京出差住宿标准是多少",
            "context": {"user_id": "user123"}
        })
    """

    def __init__(
        self,
        llm: BaseChatModel,
        rag_chain=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize policy worker agent

        Args:
            llm: Language model instance
            rag_chain: RAG chain for policy retrieval
            config: Agent configuration
        """
        super().__init__(
            name="PolicyWorkerAgent",
            llm=llm,
            tools=[],
            config=config or {}
        )
        self.rag_chain = rag_chain
        logger.info("PolicyWorkerAgent initialized")

    @traceable(name="policy_worker_execute")
    def execute(self, task: Dict[str, Any]) -> str:
        """
        Execute policy query task

        Args:
            task: Task dictionary with:
                - query: User query
                - context: Additional context

        Returns:
            Policy query result
        """
        query = task.get("query", "")
        context = task.get("context", {})

        logger.info(f"PolicyWorker: Processing query: {query}")

        try:
            # Extract policy-related keywords
            policy_query = self._extract_policy_query(query)

            # Query RAG system
            if self.rag_chain:
                result = self._query_rag(policy_query)
            else:
                result = self._fallback_policy_info(policy_query)

            logger.info("PolicyWorker: Query completed successfully")
            return result

        except Exception as e:
            logger.error(f"PolicyWorker failed: {e}")
            return f"政策查询失败：{str(e)}"

    def _extract_policy_query(self, query: str) -> str:
        """
        Extract policy-specific query from user input

        Args:
            query: Original user query

        Returns:
            Refined policy query
        """
        # Policy keywords
        policy_keywords = [
            "政策", "标准", "规定", "住宿", "餐饮", "交通",
            "报销", "额度", "限额", "差旅", "出差"
        ]

        # If query already contains policy keywords, use as-is
        if any(kw in query for kw in policy_keywords):
            return query

        # Otherwise, add "差旅政策" context
        return f"差旅政策：{query}"

    def _query_rag(self, query: str) -> str:
        """
        Query RAG system for policy information

        Args:
            query: Policy query

        Returns:
            RAG result
        """
        logger.debug(f"Querying RAG with: {query}")

        try:
            result = self.rag_chain.invoke({"query": query})

            # Extract answer and sources
            answer = result.get("result", "未找到相关政策信息")
            sources = result.get("source_documents", [])

            # Format response with sources
            if sources:
                source_list = "\n".join([f"- {doc.metadata.get('source', 'Unknown')}" for doc in sources[:3]])
                return f"{answer}\n\n参考来源：\n{source_list}"
            else:
                return answer

        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            raise RuntimeError(f"RAG查询失败: {e}") from e

    def _fallback_policy_info(self, query: str) -> str:
        """
        Fallback policy information when RAG is unavailable

        Args:
            query: Policy query

        Returns:
            Mock policy information
        """
        logger.warning("RAG not available, using fallback policy data")

        # Mock policy data
        mock_policies = {
            "住宿": "住宿标准：一线城市不超过500元/晚，二线城市不超过400元/晚，三线城市不超过300元/晚。",
            "餐饮": "餐饮标准：早餐30元，午餐50元，晚餐80元。招待客户可适当提高标准，需提前申请。",
            "交通": "交通标准：市内交通使用公共交通或出租车，长途优先选择高铁或经济舱。",
            "报销": "报销流程：出差结束后7个工作日内提交报销申请，附完整票据。超标部分需提供说明并经理审批。",
            "审批": "审批流程：3天以内出差部门经理审批，3-7天总监审批，7天以上需VP审批。"
        }

        # Find relevant policy
        query_lower = query.lower()
        for keyword, policy_info in mock_policies.items():
            if keyword in query_lower:
                return f"{policy_info}\n\n[注意：这是示例数据，实际请查询公司正式政策文档]"

        # Default response
        return """差旅政策概要：
1. 住宿标准：一线城市≤500元/晚，二线城市≤400元/晚
2. 餐饮标准：早餐30元，午餐50元，晚餐80元
3. 交通标准：优先公共交通，长途优先高铁/经济舱
4. 报销期限：出差结束后7个工作日内提交

详细信息请查询公司差旅管理系统。

[注意：这是示例数据，实际请查询公司正式政策文档]"""


# ============================================================================
# Test Code
# ============================================================================

if __name__ == "__main__":
    """
    Test PolicyWorkerAgent
    """
    print("Testing PolicyWorkerAgent...\n")

    from models.llm import get_llm

    try:
        llm = get_llm(temperature=0.3)
        agent = PolicyWorkerAgent(llm)

        # Test queries
        test_queries = [
            "北京出差住宿标准",
            "餐饮报销额度",
            "出差审批流程",
            "交通费用标准"
        ]

        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"{'='*60}")

            result = agent.execute({
                "query": query,
                "context": {"user_id": "test_user"}
            })

            print(f"Result:\n{result}")

        print("\n✅ PolicyWorkerAgent test completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
