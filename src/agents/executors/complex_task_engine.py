"""
ComplexTaskEngine - 复杂任务执行引擎

职责：
1. 使用 TaskDecomposer 分解复杂查询
2. 根据任务依赖关系编排执行顺序
3. 并行执行无依赖的任务
4. 整合所有工具结果返回最终答案

对应架构文档：
- 通道类型：复杂通道（COMPLEX）
- 适用场景：多步骤、可分解为明确子任务
- 示例："去杭州出差3天，查天气查酒店算费用"
"""
from src.agents.task_decomposer import TaskDecomposer, SubTask
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ComplexTaskEngine:
    """
    复杂任务执行引擎

    使用任务分解器将复杂查询分解为多个子任务，
    然后根据依赖关系编排执行，最后整合结果。
    """

    def __init__(
        self,
        llm,
        task_decomposer: TaskDecomposer,
        tools: Dict
    ):
        """
        初始化复杂任务执行引擎

        Args:
            llm: 语言模型（用于结果整合）
            task_decomposer: 任务分解器
            tools: 工具字典 {tool_name: tool}
        """
        self.llm = llm
        self.task_decomposer = task_decomposer
        self.tools = tools

        # 任务类型到工具名称的映射
        self.task_type_to_tool = {
            "QUERY_WEATHER": "query_weather",
            "QUERY_HOTEL": "search_hotels",
            "QUERY_POLICY": "search_policy",
            "QUERY_GRAPH": "query_graph",
            "QUERY_FLIGHT": "search_flights",
            "CALCULATE_EXPENSE": "calculate_expense",
        }

    def execute(self, query: str, context: Optional[str] = None) -> str:
        """
        执行复杂查询

        流程：
        1. 任务分解
        2. 拓扑排序（按依赖关系）
        3. 批次并行执行
        4. 结果整合

        Args:
            query: 用户查询
            context: 上下文信息（可选）

        Returns:
            整合后的最终答案
        """
        logger.info(f"[ComplexTaskEngine] 开始执行复杂查询: {query}")

        try:
            # 1. 任务分解
            tasks = self.task_decomposer.decompose(query)

            if not tasks:
                logger.warning("[ComplexTaskEngine] 任务分解失败，无法生成子任务")
                return "抱歉，我无法分解这个查询，请尝试简化您的问题。"

            logger.info(f"[ComplexTaskEngine] 分解为 {len(tasks)} 个子任务")

            # 2. 执行任务（处理依赖关系）
            task_results = self._execute_tasks_with_dependencies(tasks)

            # 3. 整合结果
            final_answer = self._synthesize_results(query, tasks, task_results, context)

            logger.info("[ComplexTaskEngine] 执行完成")
            return final_answer

        except Exception as e:
            logger.error(f"[ComplexTaskEngine] 执行失败: {e}", exc_info=True)
            return f"抱歉，执行过程中出现错误：{str(e)}"

    def _execute_tasks_with_dependencies(self, tasks: List[SubTask]) -> Dict[int, str]:
        """
        按依赖关系执行任务

        使用拓扑排序确定执行顺序，同一批次的任务并行执行

        Args:
            tasks: 子任务列表

        Returns:
            任务结果字典 {task_id: result}
        """
        results = {}
        completed_tasks = []
        remaining_tasks = tasks.copy()

        # 防止死循环
        max_iterations = len(tasks) * 2
        iteration = 0

        while remaining_tasks and iteration < max_iterations:
            iteration += 1

            # 找出当前可以执行的任务（依赖都已完成）
            ready_tasks = [
                task for task in remaining_tasks
                if task.can_execute_now(completed_tasks)
            ]

            if not ready_tasks:
                logger.error("[ComplexTaskEngine] 检测到循环依赖或无法执行的任务")
                break

            logger.info(f"[ComplexTaskEngine] 第 {iteration} 批次: {len(ready_tasks)} 个任务")

            # 并行执行这一批次的任务
            batch_results = self._execute_tasks_parallel(ready_tasks)

            # 更新结果和完成列表
            for task in ready_tasks:
                task.result = batch_results.get(task.id, "")
                task.success = task.id in batch_results
                results[task.id] = task.result
                completed_tasks.append(task)
                remaining_tasks.remove(task)

        return results

    def _execute_tasks_parallel(self, tasks: List[SubTask]) -> Dict[int, str]:
        """
        并行执行多个独立任务

        Args:
            tasks: 子任务列表

        Returns:
            任务结果字典 {task_id: result}
        """
        results = {}

        for task in tasks:
            try:
                # 获取工具名称
                tool_name = self._get_tool_name_from_task_type(task.task_type)

                if tool_name not in self.tools:
                    logger.warning(f"[ComplexTaskEngine] 工具 {tool_name} 不存在")
                    results[task.id] = f"工具 {tool_name} 不可用"
                    continue

                # 执行工具
                tool = self.tools[tool_name]
                logger.info(f"[ComplexTaskEngine] 执行任务 {task.id}: {tool_name}({task.parameters})")

                result = tool.execute(**task.parameters)
                results[task.id] = result

                logger.info(f"[ComplexTaskEngine] 任务 {task.id} 完成")

            except Exception as e:
                logger.error(f"[ComplexTaskEngine] 任务 {task.id} 执行失败: {e}")
                results[task.id] = f"执行失败: {str(e)}"

        return results

    def _get_tool_name_from_task_type(self, task_type: str) -> str:
        """
        将任务类型映射到工具名称

        Args:
            task_type: 任务类型（如 QUERY_WEATHER）

        Returns:
            工具名称（如 query_weather）
        """
        return self.task_type_to_tool.get(task_type, task_type.lower())

    def _synthesize_results(
        self,
        query: str,
        tasks: List[SubTask],
        results: Dict[int, str],
        context: Optional[str] = None
    ) -> str:
        """
        使用 LLM 整合所有任务结果

        Args:
            query: 原始查询
            tasks: 子任务列表
            results: 任务结果字典
            context: 上下文信息

        Returns:
            整合后的最终答案
        """
        # 构建整合提示词
        synthesis_prompt = f"""你是一个智能助手，需要根据多个工具的执行结果回答用户问题。

用户问题：{query}

"""

        if context:
            synthesis_prompt += f"上下文信息：\n{context}\n\n"

        synthesis_prompt += "工具执行结果：\n"

        for task in tasks:
            result = results.get(task.id, "未执行")
            synthesis_prompt += f"\n{task.description}:\n{result}\n"

        synthesis_prompt += """
请根据以上信息，用自然、完整的语言回答用户问题。
如果某些工具执行失败，请忽略失败的结果，基于成功的结果回答。
"""

        try:
            # 调用 LLM 整合
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=synthesis_prompt)])

            return response.content

        except Exception as e:
            logger.error(f"[ComplexTaskEngine] LLM 整合失败: {e}")

            # 降级：直接拼接结果
            fallback = f"根据您的问题「{query}」，我查询到以下信息：\n\n"
            for task in tasks:
                result = results.get(task.id, "查询失败")
                fallback += f"• {task.description}: {result}\n"

            return fallback
