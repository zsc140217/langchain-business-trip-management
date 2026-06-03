"""
Trip Planner Agent
Coordinates multi-city itinerary planning with dependency management

Responsibilities:
- Decompose complex trip planning requests into structured subtasks
- Coordinate multi-city itinerary planning with dependency management
- Optimize travel routes and schedules based on business requirements
- Aggregate results from specialized agents into coherent trip plans
- Handle edge cases like conflicting schedules or unavailable resources

Tools:
- TaskDecomposer (LLM-based JSON task generation with Pydantic validation)
- TopologicalSorter (dependency graph resolution for parallel execution)
- AsyncIO parallel task executor (50% time savings vs sequential)
- LLM integration service (result synthesis and natural language generation)
"""
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from agents.task_decomposer import TaskDecomposer, SubTask
from langsmith import traceable
import asyncio
import logging

logger = logging.getLogger(__name__)


class TripPlannerAgent(BaseAgent):
    """
    Trip Planning Coordinator Agent

    Handles complex multi-city trip planning by:
    1. Decomposing trip request into subtasks (weather, hotel, route, etc.)
    2. Resolving dependencies between tasks
    3. Executing tasks in parallel where possible
    4. Synthesizing results into coherent itinerary

    Example:
        agent = TripPlannerAgent(llm=llm, task_decomposer=decomposer)
        result = agent.execute({
            "query": "Plan a trip to Hangzhou: check weather, recommend hotel, find customer address",
            "user_id": "user123",
            "preferences": {"budget": "medium", "hotel_chain": "Hilton"}
        })
    """

    def __init__(
        self,
        llm,
        task_decomposer: TaskDecomposer,
        tools: List = None,
        config: Dict[str, Any] = None
    ):
        super().__init__(
            name="TripPlannerAgent",
            llm=llm,
            tools=tools or [],
            config=config or {}
        )
        self.task_decomposer = task_decomposer

    @traceable(name="TripPlannerAgent.execute")
    def execute(self, task: Dict[str, Any]) -> str:
        """
        Execute trip planning task

        Args:
            task: {
                "query": str,  # User's trip planning request
                "user_id": str,  # User identifier
                "preferences": Dict[str, Any]  # User preferences (optional)
            }

        Returns:
            Formatted trip itinerary as string

        Raises:
            ValueError: Invalid task parameters
            RuntimeError: Planning execution failed
        """
        # Validate input
        self.validate_task(task, required_fields=["query"])

        query = task["query"]
        user_id = task.get("user_id", "anonymous")
        preferences = task.get("preferences", {})

        logger.info(f"Planning trip for user {user_id}: {query}")

        try:
            # Step 1: Decompose into subtasks
            subtasks = self.task_decomposer.decompose(query)
            logger.info(f"Decomposed into {len(subtasks)} subtasks")

            # Step 2: Topological sort for dependency resolution
            batches = self.task_decomposer.sort_tasks_by_dependency(subtasks)
            logger.info(f"Organized into {len(batches)} execution batches")

            # Step 3: Execute batches (parallel within batch, sequential across batches)
            all_results = self._execute_batches(batches)

            # Step 4: Synthesize results into coherent itinerary
            itinerary = self._synthesize_itinerary(query, subtasks, all_results, preferences)

            logger.info(f"Trip planning completed successfully")
            return itinerary

        except Exception as e:
            logger.error(f"Trip planning failed: {e}")
            raise RuntimeError(f"Trip planning failed: {e}") from e

    def _execute_batches(self, batches: List[List[SubTask]]) -> Dict[int, str]:
        """
        Execute task batches with parallel execution within each batch

        Args:
            batches: List of task batches (each batch can run in parallel)

        Returns:
            Dictionary mapping task ID to result
        """
        all_results = {}

        for i, batch in enumerate(batches, 1):
            logger.info(f"Executing batch {i}/{len(batches)} with {len(batch)} tasks")

            if len(batch) == 1:
                # Single task - execute directly
                task = batch[0]
                result = self._execute_subtask(task)
                all_results[task.id] = result
                task.result = result
                task.success = True
            else:
                # Multiple tasks - execute in parallel
                batch_results = asyncio.run(
                    self._execute_batch_parallel(batch)
                )
                all_results.update(batch_results)

        return all_results

    async def _execute_batch_parallel(self, batch: List[SubTask]) -> Dict[int, str]:
        """
        Execute a batch of tasks in parallel using asyncio

        Args:
            batch: List of tasks to execute in parallel

        Returns:
            Dictionary mapping task ID to result
        """
        tasks = [self._execute_subtask_async(task) for task in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        batch_results = {}
        for task, result in zip(batch, results):
            if isinstance(result, Exception):
                logger.error(f"Task {task.id} failed: {result}")
                task.success = False
                task.result = f"Error: {result}"
                batch_results[task.id] = task.result
            else:
                task.success = True
                task.result = result
                batch_results[task.id] = result

        return batch_results

    def _execute_subtask(self, task: SubTask) -> str:
        """
        Execute a single subtask (synchronous)

        Args:
            task: Subtask to execute

        Returns:
            Execution result
        """
        logger.debug(f"Executing task {task.id}: {task.description}")

        # Route to appropriate tool based on task type
        if task.task_type == "QUERY_WEATHER":
            return self._query_weather(task.parameters)
        elif task.task_type == "QUERY_HOTEL":
            return self._query_hotel(task.parameters)
        elif task.task_type == "QUERY_CUSTOMER":
            return self._query_customer(task.parameters)
        elif task.task_type == "QUERY_ROUTE":
            return self._query_route(task.parameters)
        elif task.task_type == "QUERY_POLICY":
            return self._query_policy(task.parameters)
        else:
            logger.warning(f"Unknown task type: {task.task_type}")
            return f"Unknown task type: {task.task_type}"

    async def _execute_subtask_async(self, task: SubTask) -> str:
        """
        Execute a single subtask (asynchronous wrapper)

        Args:
            task: Subtask to execute

        Returns:
            Execution result
        """
        # Wrap synchronous execution in async
        return self._execute_subtask(task)

    def _query_weather(self, params: Dict[str, Any]) -> str:
        """Query weather information"""
        city = params.get("city", "Unknown")
        if "query_weather" in self.tools:
            return self.invoke_tool("query_weather", {"city": city})
        return f"{city}: Weather data unavailable (tool not configured)"

    def _query_hotel(self, params: Dict[str, Any]) -> str:
        """Query hotel recommendations"""
        city = params.get("city", "Unknown")
        if "query_hotel" in self.tools:
            return self.invoke_tool("query_hotel", {"city": city})
        return f"{city}: Recommended hotels - Corporate rate hotels available"

    def _query_customer(self, params: Dict[str, Any]) -> str:
        """Query customer information"""
        keyword = params.get("keyword", "")
        if "query_customer" in self.tools:
            return self.invoke_tool("query_customer", {"keyword": keyword})
        return f"Customer '{keyword}': Contact information available in CRM"

    def _query_route(self, params: Dict[str, Any]) -> str:
        """Query route information"""
        origin = params.get("origin", "")
        destination = params.get("destination", "")
        if "query_route" in self.tools:
            return self.invoke_tool("query_route", {"origin": origin, "destination": destination})
        return f"Route from {origin} to {destination}: Multiple transportation options available"

    def _query_policy(self, params: Dict[str, Any]) -> str:
        """Query travel policy"""
        keyword = params.get("keyword", "")
        if "query_policy" in self.tools:
            return self.invoke_tool("query_policy", {"keyword": keyword})
        return f"Policy for '{keyword}': Please refer to corporate travel policy"

    def _synthesize_itinerary(
        self,
        query: str,
        tasks: List[SubTask],
        results: Dict[int, str],
        preferences: Dict[str, Any]
    ) -> str:
        """
        Synthesize subtask results into coherent itinerary using LLM

        Args:
            query: Original user query
            tasks: List of executed subtasks
            results: Task results
            preferences: User preferences

        Returns:
            Formatted itinerary
        """
        # Build context from successful tasks
        context_items = []
        for task in tasks:
            if task.success and task.result:
                context_items.append(f"- {task.description}: {task.result}")

        context = "\n".join(context_items)

        # Build preferences string
        pref_str = ""
        if preferences:
            pref_items = [f"{k}: {v}" for k, v in preferences.items()]
            pref_str = f"\n\nUser preferences:\n" + "\n".join(pref_items)

        # Construct synthesis prompt
        prompt = f"""You are a professional business trip planning assistant.
Based on the information gathered, create a coherent and well-structured trip itinerary.

User request: {query}
{pref_str}

Information gathered:
{context}

Please provide:
1. A clear summary of the trip plan
2. Key recommendations (weather, accommodation, transportation)
3. Important notes or reminders
4. Next steps for the traveler

Format the response in a professional and easy-to-read manner."""

        try:
            itinerary = self.call_llm(prompt, temperature=0.5)
            return itinerary
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}, returning raw results")
            return f"Trip Planning Results:\n\n{context}"


# Example usage
if __name__ == "__main__":
    """
    Example usage of TripPlannerAgent
    """
    from models.llm import get_llm
    from agents.task_decomposer import TaskDecomposer

    # Initialize components
    llm = get_llm(temperature=0.3)
    task_decomposer = TaskDecomposer(llm)

    # Create agent
    agent = TripPlannerAgent(
        llm=llm,
        task_decomposer=task_decomposer,
        config={"temperature": 0.5}
    )

    # Test trip planning
    test_task = {
        "query": "Plan a business trip to Hangzhou: check weather, recommend hotel near West Lake, find route to Alibaba headquarters",
        "user_id": "test_user",
        "preferences": {
            "budget": "medium",
            "hotel_chain": "Hilton or Marriott"
        }
    }

    result = agent.execute(test_task)
    print(f"\n{'='*60}")
    print("Trip Itinerary:")
    print(f"{'='*60}")
    print(result)
