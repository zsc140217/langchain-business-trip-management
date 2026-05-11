"""
任务分解器
将复杂查询分解为结构化的子任务列表

对应Spring AI的：
src/main/java/com/jblmj/aiagent/service/TaskDecomposer.java
"""
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import asyncio
import json


class SubTask(BaseModel):
    """
    子任务模型

    对应Spring AI的SubTask类
    """
    id: int = Field(description="任务ID")
    task_type: str = Field(description="任务类型（QUERY_WEATHER等）")
    description: str = Field(description="任务描述")
    parameters: dict = Field(description="任务参数（JSON格式）")
    depends_on: List[int] = Field(default_factory=list, description="依赖的任务ID列表")
    priority: int = Field(default=0, description="优先级")
    result: Optional[str] = None
    success: bool = False

    def can_execute_now(self, completed_tasks: List['SubTask']) -> bool:
        """
        判断任务是否可以立即执行

        Args:
            completed_tasks: 已完成的任务列表

        Returns:
            是否可以执行
        """
        if not self.depends_on:
            return True

        completed_ids = [t.id for t in completed_tasks if t.success]
        return all(dep_id in completed_ids for dep_id in self.depends_on)


class TaskDecomposer:
    """
    任务分解器

    核心功能：
    1. 将复杂查询分解为结构化的子任务列表（JSON格式）
    2. 支持任务依赖关系和拓扑排序
    3. 检测循环依赖，防止死锁
    4. 支持并行执行无依赖的任务

    设计思路：
    - 使用LLM生成JSON格式的任务列表
    - 使用Pydantic验证和解析
    - 使用拓扑排序确定执行顺序
    - 使用asyncio并行执行任务
    """

    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=List[SubTask])
        self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser, llm=llm)
        self.chain = self._create_chain()

    def decompose(self, query: str) -> List[SubTask]:
        """
        分解复杂查询为子任务列表

        流程：
        1. 调用LLM生成任务列表（JSON格式）
        2. 解析JSON为SubTask对象
        3. 验证依赖关系（检测循环依赖）
        4. 返回任务列表

        Args:
            query: 用户查询

        Returns:
            子任务列表
        """
        print(f"\n========== 任务分解开始 ==========")
        print(f"查询：{query}")

        try:
            # 1. 调用LLM生成任务列表
            result = self.chain.run(query=query)
            print(f"LLM响应：{result[:200]}...")

            # 2. 解析JSON
            try:
                tasks = self.parser.parse(result)
            except Exception as e:
                print(f"解析失败，尝试自动修复：{e}")
                tasks = self.fixing_parser.parse(result)

            print(f"成功分解为 {len(tasks)} 个子任务")

            # 3. 验证依赖关系
            self._validate_dependencies(tasks)

            # 4. 打印任务详情
            for task in tasks:
                deps = f"依赖任务{task.depends_on}" if task.depends_on else "无依赖"
                print(f"  任务{task.id}: {task.description} ({deps})")

            print(f"========== 任务分解完成 ==========\n")
            return tasks

        except Exception as e:
            print(f"❌ 任务分解失败：{e}")
            print("降级为单个RAG任务")
            return self._create_fallback_tasks(query)

    def _create_chain(self):
        """
        创建任务分解链

        使用Few-shot Prompt提高LLM输出质量
        """
        prompt_template = """你是任务规划专家，请将用户查询分解为多个子任务，并标注依赖关系。

可用任务类型：
1. QUERY_WEATHER: 查询天气（参数：city）
2. QUERY_ROUTE: 查询路线（参数：origin, destination）
3. QUERY_CUSTOMER: 查询客户信息（参数：keyword）
4. QUERY_POLICY: 查询差旅政策（参数：keyword）
5. QUERY_HOTEL: 查询酒店推荐（参数：city）

任务依赖规则：
- 如果任务 B 需要任务 A 的结果，则 B 依赖 A（在 depends_on 中填写 A 的 id）
- 例如：查询路线需要先知道客户地址，所以路线查询依赖客户查询
- 没有依赖关系的任务可以并行执行

{format_instructions}

示例1：
用户查询："去杭州出差，查天气并推荐酒店"
输出：
[
  {{
    "id": 0,
    "task_type": "QUERY_WEATHER",
    "description": "查询杭州天气",
    "parameters": {{"city": "杭州"}},
    "depends_on": [],
    "priority": 0
  }},
  {{
    "id": 1,
    "task_type": "QUERY_HOTEL",
    "description": "推荐杭州酒店",
    "parameters": {{"city": "杭州"}},
    "depends_on": [],
    "priority": 0
  }}
]

示例2：
用户查询："查询阿里巴巴客户地址并规划路线"
输出：
[
  {{
    "id": 0,
    "task_type": "QUERY_CUSTOMER",
    "description": "查询阿里巴巴客户地址",
    "parameters": {{"keyword": "阿里巴巴"}},
    "depends_on": [],
    "priority": 0
  }},
  {{
    "id": 1,
    "task_type": "QUERY_ROUTE",
    "description": "规划到阿里巴巴的路线",
    "parameters": {{"origin": "酒店", "destination": "阿里巴巴"}},
    "depends_on": [0],
    "priority": 1
  }}
]

用户查询：{query}

子任务列表："""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["query"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

        return LLMChain(llm=self.llm, prompt=prompt)

    def _validate_dependencies(self, tasks: List[SubTask]):
        """
        验证任务依赖关系（检测循环依赖）

        Args:
            tasks: 任务列表

        Raises:
            ValueError: 如果检测到循环依赖
        """
        for task in tasks:
            if self._has_cyclic_dependency(task, tasks, []):
                raise ValueError(f"检测到循环依赖: 任务 {task.id}")

    def _has_cyclic_dependency(self, task: SubTask, all_tasks: List[SubTask], visited: List[int]) -> bool:
        """
        检测循环依赖（深度优先搜索）

        Args:
            task: 当前任务
            all_tasks: 所有任务
            visited: 已访问的任务ID列表

        Returns:
            是否存在循环依赖
        """
        if task.id in visited:
            return True  # 发现循环

        visited.append(task.id)

        for dep_id in task.depends_on:
            dep_task = next((t for t in all_tasks if t.id == dep_id), None)
            if dep_task and self._has_cyclic_dependency(dep_task, all_tasks, visited.copy()):
                return True

        return False

    def sort_tasks_by_dependency(self, tasks: List[SubTask]) -> List[List[SubTask]]:
        """
        按依赖关系排序任务（拓扑排序）

        返回批次列表，每个批次内的任务可以并行执行

        Args:
            tasks: 任务列表

        Returns:
            批次列表，每个批次是一个任务列表
        """
        print(f"\n========== 拓扑排序开始 ==========")

        result = []
        remaining = tasks.copy()
        completed = []

        while remaining:
            # 找出当前可以执行的任务（所有依赖都已完成）
            current_batch = [
                task for task in remaining
                if self._can_execute_now(task, completed)
            ]

            if not current_batch:
                raise ValueError("无法继续执行，可能存在循环依赖或无效依赖")

            # 按优先级排序
            current_batch.sort(key=lambda t: t.priority)

            print(f"批次 {len(result) + 1}: {len(current_batch)} 个任务")
            for task in current_batch:
                print(f"  - 任务{task.id}: {task.description}")

            result.append(current_batch)
            completed.extend(current_batch)
            remaining = [t for t in remaining if t not in current_batch]

        print(f"========== 拓扑排序完成（共{len(result)}个批次）==========\n")
        return result

    def _can_execute_now(self, task: SubTask, completed_tasks: List[SubTask]) -> bool:
        """
        判断任务是否可以执行

        Args:
            task: 任务
            completed_tasks: 已完成的任务列表

        Returns:
            是否可以执行
        """
        if not task.depends_on:
            return True

        completed_ids = [t.id for t in completed_tasks]
        return all(dep_id in completed_ids for dep_id in task.depends_on)

    async def execute_tasks_parallel(self, tasks: List[SubTask], executor_func) -> Dict[int, str]:
        """
        并行执行多个任务

        Args:
            tasks: 任务列表
            executor_func: 执行函数，接收SubTask，返回结果字符串

        Returns:
            任务ID到结果的映射
        """
        print(f"\n并行执行 {len(tasks)} 个任务...")

        async def execute_with_error_handling(task: SubTask):
            """带错误处理的任务执行"""
            try:
                result = await executor_func(task)
                task.result = result
                task.success = True
                print(f"  ✅ 任务{task.id}完成")
                return task.id, result
            except Exception as e:
                task.success = False
                error_msg = f"执行失败: {str(e)}"
                task.result = error_msg
                print(f"  ❌ 任务{task.id}失败: {e}")
                return task.id, error_msg

        # 并行执行所有任务
        results = await asyncio.gather(
            *[execute_with_error_handling(task) for task in tasks],
            return_exceptions=True  # 不因单个任务失败而中断
        )

        return dict(results)

    def _create_fallback_tasks(self, query: str) -> List[SubTask]:
        """
        创建降级任务列表（当分解失败时）

        Args:
            query: 用户查询

        Returns:
            单个RAG任务
        """
        return [SubTask(
            id=0,
            task_type="QUERY_POLICY",
            description="查询差旅政策",
            parameters={"keyword": query},
            depends_on=[],
            priority=0
        )]


# 测试代码
if __name__ == "__main__":
    """
    测试任务分解器
    """
    print("测试任务分解器...\n")

    from src.models.llm import get_llm

    try:
        llm = get_llm(temperature=0.3)
        decomposer = TaskDecomposer(llm)

        # 测试用例
        test_queries = [
            "去杭州出差，查天气并推荐酒店",
            "查询阿里巴巴客户地址并规划路线",
            "帮我规划明天去深圳的行程"
        ]

        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"测试查询：{query}")
            print(f"{'='*60}")

            # 1. 分解任务
            tasks = decomposer.decompose(query)

            # 2. 拓扑排序
            batches = decomposer.sort_tasks_by_dependency(tasks)

            print(f"\n执行计划：")
            for i, batch in enumerate(batches, 1):
                if len(batch) == 1:
                    print(f"  批次{i}：顺序执行任务{batch[0].id}")
                else:
                    task_ids = [t.id for t in batch]
                    print(f"  批次{i}：并行执行任务{task_ids}")

        print("\n✅ 任务分解器测试完成！")

    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
