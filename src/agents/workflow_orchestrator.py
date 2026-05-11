"""
工作流编排器
中央路由引擎，负责所有查询的分发和执行

对应Spring AI的：
src/main/java/com/jblmj/aiagent/app/WorkflowOrchestrator.java
"""
from src.agents.complexity_assessor import ComplexityAssessor, QueryComplexity
from src.agents.task_decomposer import TaskDecomposer, SubTask
from typing import Optional, Dict
import asyncio


class WorkflowOrchestrator:
    """
    工作流编排器

    核心功能：
    1. 智能路由：根据查询复杂度选择处理策略
    2. Skill优先：优先使用Skill处理（未实现）
    3. 复杂度降级：Skill无法处理时使用复杂度评估
    4. 任务编排：COMPLEX查询自动分解和并行执行

    路由策略：
    - SIMPLE：单工具调用，直接返回结果
    - MEDIUM：多次工具调用，循环执行
    - COMPLEX：任务分解 → 拓扑排序 → 批次并行执行 → LLM整合

    设计思路：
    - 不完全依赖LLM决策，通过代码控制工作流
    - 保证生产环境稳定性（工具调用率100%）
    - 适配所有模型（包括工具调用能力较弱的国产模型）
    """

    def __init__(
        self,
        llm,
        complexity_assessor: ComplexityAssessor,
        task_decomposer: TaskDecomposer,
        rag_chain=None,
        tools: Dict = None
    ):
        self.llm = llm
        self.complexity_assessor = complexity_assessor
        self.task_decomposer = task_decomposer
        self.rag_chain = rag_chain
        self.tools = tools or {}

    def route(self, query: str, chat_id: str, mode: str = "default") -> str:
        """
        智能路由查询到合适的处理器

        Args:
            query: 用户查询
            chat_id: 会话ID
            mode: 执行模式（default/thinking）

        Returns:
            处理结果
        """
        print(f"\n{'='*60}")
        print(f"工作流路由开始")
        print(f"查询：{query}")
        print(f"会话ID：{chat_id}")
        print(f"模式：{mode}")
        print(f"{'='*60}")

        if mode == "thinking":
            # 思考模式：使用ReAct Agent（未实现）
            print("思考模式暂未实现，降级为默认模式")
            return self._route_by_complexity(query, chat_id)
        else:
            # 默认模式：使用复杂度评估
            return self._route_by_complexity(query, chat_id)

    def _route_by_complexity(self, query: str, chat_id: str) -> str:
        """
        基于复杂度的路由

        流程：
        1. 评估查询复杂度
        2. 根据复杂度选择处理策略
        3. 执行并返回结果

        Args:
            query: 用户查询
            chat_id: 会话ID

        Returns:
            处理结果
        """
        # 1. 评估复杂度
        complexity = self.complexity_assessor.assess(query)

        # 2. 根据复杂度选择策略
        if complexity == QueryComplexity.SIMPLE:
            return self._handle_simple(query, chat_id)
        elif complexity == QueryComplexity.MEDIUM:
            return self._handle_medium(query, chat_id)
        else:
            return self._handle_complex(query, chat_id)

    def _handle_simple(self, query: str, chat_id: str) -> str:
        """
        处理SIMPLE查询

        策略：单工具调用或RAG查询

        Args:
            query: 用户查询
            chat_id: 会话ID

        Returns:
            处理结果
        """
        print(f"\n========== 处理SIMPLE查询 ==========")

        # 判断是否为天气查询
        if any(keyword in query for keyword in ["天气", "温度", "下雨"]):
            return self._handle_weather_query(query)

        # 默认使用RAG
        return self._handle_rag_query(query, chat_id)

    def _handle_medium(self, query: str, chat_id: str) -> str:
        """
        处理MEDIUM查询

        策略：多次工具调用（如天气对比）

        Args:
            query: 用户查询
            chat_id: 会话ID

        Returns:
            处理结果
        """
        print(f"\n========== 处理MEDIUM查询 ==========")

        # 判断是否为天气对比
        if any(keyword in query for keyword in ["天气", "温度"]):
            return self._handle_weather_comparison(query)

        # 默认使用RAG
        return self._handle_rag_query(query, chat_id)

    def _handle_complex(self, query: str, chat_id: str) -> str:
        """
        处理COMPLEX查询

        策略：
        1. 任务分解
        2. 拓扑排序
        3. 批次并行执行
        4. LLM整合结果

        Args:
            query: 用户查询
            chat_id: 会话ID

        Returns:
            处理结果
        """
        print(f"\n========== 处理COMPLEX查询 ==========")

        try:
            # 1. 任务分解
            tasks = self.task_decomposer.decompose(query)

            # 2. 拓扑排序
            batches = self.task_decomposer.sort_tasks_by_dependency(tasks)

            # 3. 批次执行
            all_results = {}
            for i, batch in enumerate(batches, 1):
                print(f"\n执行批次 {i}/{len(batches)}...")

                if len(batch) == 1:
                    # 单个任务，直接执行
                    task = batch[0]
                    result = self._execute_subtask(task)
                    all_results[task.id] = result
                    task.result = result
                    task.success = True
                else:
                    # 多个任务，并行执行
                    batch_results = asyncio.run(
                        self.task_decomposer.execute_tasks_parallel(
                            batch,
                            self._execute_subtask_async
                        )
                    )
                    all_results.update(batch_results)

            # 4. LLM整合结果
            return self._integrate_results(query, tasks, all_results)

        except Exception as e:
            print(f"❌ COMPLEX查询处理失败：{e}")
            print("降级为RAG查询")
            return self._handle_rag_query(query, chat_id)

    def _execute_subtask(self, task: SubTask) -> str:
        """
        执行单个子任务（同步）

        Args:
            task: 子任务

        Returns:
            执行结果
        """
        print(f"  执行任务{task.id}: {task.description}")

        if task.task_type == "QUERY_WEATHER":
            city = task.parameters.get("city")
            return self._query_weather(city)

        elif task.task_type == "QUERY_POLICY":
            keyword = task.parameters.get("keyword")
            return self._query_policy(keyword)

        elif task.task_type == "QUERY_HOTEL":
            city = task.parameters.get("city")
            return f"{city}推荐酒店：如家快捷酒店、汉庭酒店（协议价400元/晚）"

        elif task.task_type == "QUERY_CUSTOMER":
            keyword = task.parameters.get("keyword")
            return f"客户{keyword}：地址为杭州市西湖区文三路，联系人张经理"

        elif task.task_type == "QUERY_ROUTE":
            origin = task.parameters.get("origin")
            destination = task.parameters.get("destination")
            return f"从{origin}到{destination}：建议乘坐地铁2号线，约30分钟"

        else:
            return f"未知任务类型: {task.task_type}"

    async def _execute_subtask_async(self, task: SubTask) -> str:
        """
        执行单个子任务（异步）

        Args:
            task: 子任务

        Returns:
            执行结果
        """
        # 简单包装同步方法为异步
        return self._execute_subtask(task)

    def _integrate_results(self, query: str, tasks: list, results: Dict) -> str:
        """
        整合子任务结果

        使用LLM将多个子任务的结果整合成连贯的回答

        Args:
            query: 原始查询
            tasks: 任务列表
            results: 任务结果映射

        Returns:
            整合后的回答
        """
        print(f"\n========== LLM整合结果 ==========")

        # 构建上下文
        context = []
        for task in tasks:
            if task.success and task.result:
                context.append(f"- {task.description}：{task.result}")

        context_str = "\n".join(context)

        prompt = f"""你是企业差旅助手。请根据以下信息，整合成一个连贯的回答。

用户问题：{query}

子任务结果：
{context_str}

请给出完整、连贯的回答："""

        try:
            response = self.llm.predict(prompt, temperature=0.5)
            print(f"整合完成")
            return response
        except Exception as e:
            print(f"整合失败：{e}，返回原始结果")
            return context_str

    def _handle_weather_query(self, query: str) -> str:
        """处理天气查询"""
        # 提取城市
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都"]
        city = next((c for c in cities if c in query), "北京")

        return self._query_weather(city)

    def _handle_weather_comparison(self, query: str) -> str:
        """处理天气对比"""
        # 提取城市
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都"]
        found_cities = [c for c in cities if c in query]

        if len(found_cities) >= 2:
            weather1 = self._query_weather(found_cities[0])
            weather2 = self._query_weather(found_cities[1])
            return f"天气对比：\n{weather1}\n{weather2}"
        else:
            return "请提供两个城市进行对比"

    def _query_weather(self, city: str) -> str:
        """查询天气（调用工具）"""
        if "query_weather" in self.tools:
            return self.tools["query_weather"].invoke({"city": city})
        else:
            return f"{city}：晴天，温度25°C（模拟数据）"

    def _query_policy(self, keyword: str) -> str:
        """查询政策（调用RAG）"""
        if self.rag_chain:
            result = self.rag_chain.invoke({"query": keyword})
            return result.get("result", "未找到相关政策")
        else:
            return "RAG系统未初始化"

    def _handle_rag_query(self, query: str, chat_id: str) -> str:
        """处理RAG查询"""
        print(f"\n========== 使用RAG处理 ==========")

        if self.rag_chain:
            result = self.rag_chain.invoke({"query": query})
            return result.get("result", "未找到相关信息")
        else:
            return "RAG系统未初始化，请先配置向量存储"


# 测试代码
if __name__ == "__main__":
    """
    测试工作流编排器
    """
    print("测试工作流编排器...\n")

    from src.models.llm import get_llm

    try:
        llm = get_llm(temperature=0.3)

        # 初始化组件
        complexity_assessor = ComplexityAssessor(llm)
        task_decomposer = TaskDecomposer(llm)

        # 创建编排器
        orchestrator = WorkflowOrchestrator(
            llm=llm,
            complexity_assessor=complexity_assessor,
            task_decomposer=task_decomposer
        )

        # 测试用例
        test_queries = [
            "北京天气怎么样",
            "上海和广州天气对比",
            "去杭州出差，查天气并推荐酒店"
        ]

        for query in test_queries:
            result = orchestrator.route(query, "test123")
            print(f"\n最终结果：{result}\n")
            print(f"{'='*60}\n")

        print("✅ 工作流编排器测试完成！")

    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
