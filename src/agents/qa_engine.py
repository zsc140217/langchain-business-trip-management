"""
QAEngine - Q&A 域执行器

职责：
1. 接收用户查询和上下文
2. 使用 LLM 判断查询类型（simple/complex/planning/open）
3. 路由到四个执行器之一
4. 返回最终答案

对应架构文档：
- 业务域：Q&A 域
- 四个通道：简单/复杂/规划/开放
"""
from typing import Dict, Optional
from langchain_core.messages import HumanMessage
import logging
from src.monitoring import track_unified_metric, trace_operation
import json
import re

logger = logging.getLogger(__name__)


class QAEngine:
    """
    Q&A 域执行器

    处理差旅政策查询、关系查询、比较推荐等问题。
    内部路由到四个通道：
    - simple: 单工具调用
    - complex: TaskDecomposer + Multi-Agent
    - planning: Planning Skill
    - open: ReAct 循环
    """

    def __init__(
        self,
        llm,
        tools: Dict,
        complex_engine=None,
        planning_engine=None,
        react_engine=None
    ):
        """
        初始化 Q&A 引擎

        Args:
            llm: 语言模型
            tools: 工具字典 {tool_name: tool}
            complex_engine: 复杂任务引擎（可选，延迟初始化）
            planning_engine: 规划引擎（可选，延迟初始化）
            react_engine: ReAct 引擎（可选，延迟初始化）
        """
        self.llm = llm
        self.tools = tools

        # 执行器（支持延迟初始化）
        self._complex_engine = complex_engine
        self._planning_engine = planning_engine
        self._react_engine = react_engine

        # 路由统计
        self.stats = {
            "simple": 0,
            "complex": 0,
            "planning": 0,
            "open": 0,
            "total": 0
        }

    @property
    def complex_engine(self):
        """延迟初始化 ComplexTaskEngine"""
        if self._complex_engine is None:
            from src.agents.executors.complex_task_engine import ComplexTaskEngine
            from src.agents.task_decomposer import TaskDecomposer

            task_decomposer = TaskDecomposer(self.llm)
            self._complex_engine = ComplexTaskEngine(
                llm=self.llm,
                task_decomposer=task_decomposer,
                tools=self.tools
            )
            logger.info("[QAEngine] ComplexTaskEngine 延迟初始化完成")

        return self._complex_engine

    @property
    def planning_engine(self):
        """延迟初始化 PlanningEngine"""
        if self._planning_engine is None:
            from src.agents.executors.planning_engine import PlanningEngine

            self._planning_engine = PlanningEngine(
                llm=self.llm,
                tools=self.tools,
                memory_service=None  # 待集成记忆层
            )
            logger.info("[QAEngine] PlanningEngine 延迟初始化完成")

        return self._planning_engine

    @property
    def react_engine(self):
        """延迟初始化 ReactEngine"""
        if self._react_engine is None:
            from src.agents.executors.react_engine import ReactEngine

            self._react_engine = ReactEngine(
                llm=self.llm,
                tools=self.tools,
                max_iterations=5
            )
            logger.info("[QAEngine] ReactEngine 延迟初始化完成")

        return self._react_engine

    @trace_operation("qa_execute", domain="qa_domain", channel="llm")
    def execute(
        self,
        query: str,
        context: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        执行 Q&A 查询

        流程：
        1. LLM 路由决策
        2. 调用对应执行器
        3. 返回答案

        Args:
            query: 用户查询
            context: 上下文信息（可选）
            user_id: 用户ID（用于规划通道）
            conversation_id: 会话ID（用于规划通道）

        Returns:
            答案文本
        """
        logger.info(f"[QAEngine] 开始执行: {query}")
        self.stats["total"] += 1
        _domain, _channel = "qa_domain", "unknown"

        try:
            # 1. LLM 路由决策
            decision = self._llm_route(query, context)

            query_type = decision.get("type", "complex")
            logger.info(f"[QAEngine] 路由决策: {query_type} - {decision.get('reason', '')}")

            # 2. 路由到对应执行器
            if query_type == "simple":
                self.stats["simple"] += 1
                return self._execute_simple(query, decision)

            elif query_type == "complex":
                self.stats["complex"] += 1
                return self.complex_engine.execute(query, context)

            elif query_type == "planning":
                self.stats["planning"] += 1
                # 规划通道需要 user_id 和 conversation_id
                if not user_id or not conversation_id:
                    logger.warning("[QAEngine] 规划通道缺少 user_id/conversation_id，降级到复杂通道")
                    self.stats["complex"] += 1
                    return self.complex_engine.execute(query, context)

                return self.planning_engine.execute(query, user_id, conversation_id)

            elif query_type == "open":
                self.stats["open"] += 1
                return self.react_engine.execute(query, context)

            else:
                # 未知类型，降级到复杂通道
                logger.warning(f"[QAEngine] 未知路由类型: {query_type}，降级到复杂通道")
                self.stats["complex"] += 1
                return self.complex_engine.execute(query, context)

        except Exception as e:
            logger.error(f"[QAEngine] 执行失败: {e}", exc_info=True)
            return f"抱歉，处理您的问题时出现错误：{str(e)}"

    def _llm_route(self, query: str, context: Optional[str]) -> dict:
        """
        使用 LLM 判断查询类型

        Args:
            query: 用户查询
            context: 上下文信息

        Returns:
            路由决策字典 {"type": "simple/complex/planning/open", "tool": "...", "reason": "..."}
        """
        prompt = f"""你是一个路由决策助手，负责判断用户查询应该走哪个通道。

用户查询：{query}
"""

        if context:
            prompt += f"\n上下文信息：\n{context}\n"

        prompt += """
请分析查询，返回 JSON 格式的路由决策。

分类标准：
1. **simple** - 单一意图，一个工具能回答
   示例："北京住宿标准是多少" → search_policy
   特征：明确的单一问题，不涉及多步骤

2. **complex** - 多步骤，可分解为明确子任务
   示例："去杭州出差3天，查天气查酒店算费用"
   特征：多个意图，需要多个工具，但步骤明确

3. **planning** - 需要完整差旅方案
   示例："帮我安排下周去深圳出差"
   特征：要求"安排"、"规划"、"方案"

4. **open** - 比较/推荐/评价类问题
   示例："飞机和高铁哪个划算"、"夏天适合去哪里出差"
   特征：需要推理和比较，没有明确的执行步骤

只返回 JSON（不要 markdown 代码块）：
{
  "type": "simple/complex/planning/open",
  "tool": "工具名(仅 simple 需要)",
  "reason": "判断原因"
}
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()

            # 尝试解析 JSON
            decision = self._parse_json_response(content)

            # 验证决策
            if not decision or "type" not in decision:
                logger.warning(f"[QAEngine] LLM 返回无效决策: {content}")
                return {"type": "complex", "reason": "LLM 返回无效决策，降级"}

            return decision

        except Exception as e:
            logger.error(f"[QAEngine] LLM 路由失败: {e}")
            # 降级：默认走复杂通道
            return {"type": "complex", "reason": f"LLM 调用失败: {str(e)}"}

    def _parse_json_response(self, content: str) -> dict:
        """
        解析 LLM 返回的 JSON

        Args:
            content: LLM 响应内容

        Returns:
            解析后的字典
        """
        try:
            # 直接解析
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取 JSON（处理 markdown 代码块）
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # 尝试提取裸 JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            logger.warning(f"[QAEngine] 无法解析 JSON: {content}")
            return {}

    def _execute_simple(self, query: str, decision: dict) -> str:
        """
        执行简单查询（单工具调用）

        Args:
            query: 用户查询
            decision: 路由决策

        Returns:
            工具执行结果
        """
        tool_name = decision.get("tool")

        # 如果 LLM 没有指定工具，默认使用 search_policy
        if not tool_name:
            logger.info("[QAEngine] LLM 未指定工具，默认使用 search_policy")
            tool_name = "search_policy"

        # 检查工具是否存在
        if tool_name not in self.tools:
            logger.warning(f"[QAEngine] 工具 {tool_name} 不存在，降级到复杂通道")
            return self.complex_engine.execute(query)

        try:
            tool = self.tools[tool_name]
            logger.info(f"[QAEngine] 调用工具: {tool_name}")

            # 调用工具（传入查询作为参数）
            result = tool.execute(query=query)

            return result

        except Exception as e:
            logger.error(f"[QAEngine] 工具 {tool_name} 执行失败: {e}")
            return f"工具执行失败：{str(e)}"

    def get_stats(self) -> dict:
        """
        获取路由统计信息

        Returns:
            统计数据字典
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """重置统计信息"""
        for key in self.stats:
            self.stats[key] = 0
        logger.info("[QAEngine] 统计信息已重置")
