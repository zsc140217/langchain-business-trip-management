"""
OrchestratorAgent - 统一入口 Agent

职责：
1. 加载记忆（上下文）
2. 规则匹配（快路径）- 天气/航班/酒店/政策关键词
3. LLM 分析 → 路由到 Q&A 域或审批域
4. 记忆更新
5. 监控埋点

对应架构文档：
- 入口层：统一入口
- 两个业务域：Q&A 域、审批域
"""
from typing import Dict, Optional
from langchain_core.messages import HumanMessage
import logging
from src.monitoring import track_unified_metric, track_tool_call_metric, trace_operation
import time

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    统一入口 Agent

    负责：
    1. 规则匹配快路径（天气/航班/酒店等明确意图）
    2. 路由到 Q&A 域或审批域
    3. 记忆管理和监控埋点
    """

    def __init__(
        self,
        llm,
        tools: Dict,
        qa_engine=None,
        approval_engine=None,
        memory_service=None
    ):
        """
        初始化 Orchestrator Agent

        Args:
            llm: 语言模型
            tools: 工具字典 {tool_name: tool}
            qa_engine: Q&A 域执行器（可选，延迟初始化）
            approval_engine: 审批域执行器（可选，未实现）
            memory_service: 记忆服务（可选，待集成）
        """
        self.llm = llm
        self.tools = tools
        self._qa_engine = qa_engine
        self._approval_engine = approval_engine
        self.memory_service = memory_service

        # 审批域关键词（优先级最高，先检查）
        self.approval_keywords = [
            "报销", "提交报销", "报销申请", "申请", "审批", "提交出差",
            "我的申请", "审批进度", "审批状态"
        ]

        # 快路径规则（关键词匹配）
        self.fast_rules = {
            "weather": ["天气", "温度", "下雨", "气温", "冷不冷", "热不热"],
            "flight": ["航班", "机票", "飞机", "航空"],
            "hotel": ["酒店", "宾馆", "住宿推荐", "酒店推荐"],
            "policy": ["标准", "补贴", "规定", "政策", "制度"],  # 移除"报销"避免冲突
        }

        # 统计信息
        self.stats = {
            "fast_path": 0,  # 快路径命中次数
            "qa_domain": 0,  # Q&A 域路由次数
            "approval_domain": 0,  # 审批域路由次数
            "total": 0,  # 总请求数
        }

    @property
    def qa_engine(self):
        """延迟初始化 QAEngine"""
        if self._qa_engine is None:
            from src.agents.qa_engine import QAEngine

            self._qa_engine = QAEngine(
                llm=self.llm,
                tools=self.tools
            )
            logger.info("[OrchestratorAgent] QAEngine 延迟初始化完成")

        return self._qa_engine

    @trace_operation("orchestrator_route", domain="orchestrator", channel="unified")
    def route(
        self,
        query: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        路由用户查询

        流程：
        1. 加载记忆（上下文）
        2. 规则匹配（快路径）
        3. 审批域判断
        4. Q&A 域路由
        5. 记忆更新

        Args:
            query: 用户查询
            user_id: 用户ID（可选）
            conversation_id: 会话ID（可选）

        Returns:
            答案文本
        """
        logger.info(f"[OrchestratorAgent] 收到查询: {query}")
        start_time = time.time()
        self.stats["total"] += 1
        _domain, _channel = "unknown", "unknown"
        #_domain, _channel = "unknown", "unknown"
        _domain, _channel = "unknown", "unknown"
        #_domain, _channel = "unknown", "unknown"
        _domain, _channel = "unknown", "unknown"
        request_domain = "unknown"
        request_channel = "unknown"

        try:
            # 1. 加载记忆（上下文）
            context = self._load_context(user_id, conversation_id)

            # 2. 审批域判断（优先级最高）
            if self._is_approval_query(query):
                self.stats["approval_domain"] += 1
                logger.info("[OrchestratorAgent] 路由到审批域")
                elapsed = time.time() - start_time
                logger.info(f"[OrchestratorAgent] 审批域完成，耗时 {elapsed:.2f}s")
                return self._route_to_approval(query, user_id, conversation_id)

            # 3. 规则匹配（快路径）
            fast_result = self._try_fast_path(query, context)
            if fast_result:
                self.stats["fast_path"] += 1
                elapsed = time.time() - start_time
                logger.info(f"[OrchestratorAgent] 快路径完成，耗时 {elapsed:.2f}s")
                track_unified_metric(
                    domain="fast_path",
                    channel="rule",
                    duration_seconds=elapsed,
                    success=True
                )
                return fast_result

            # 4. Q&A 域路由（默认）
            self.stats["qa_domain"] += 1
            logger.info("[OrchestratorAgent] 路由到 Q&A 域")
            result = self.qa_engine.execute(
                query=query,
                context=context,
                user_id=user_id,
                conversation_id=conversation_id
            )

            # 5. 记忆更新（待实现）
            self._update_memory(query, result, user_id, conversation_id)

            elapsed = time.time() - start_time
            logger.info(f"[OrchestratorAgent] 完成，耗时 {elapsed:.2f}s")
            _domain, _channel = "qa_domain", "unknown"
            track_unified_metric(domain=_domain, channel=_channel, duration_seconds=elapsed, success=True)
            return result

        except Exception as e:
            logger.error(f"[OrchestratorAgent] 路由失败: {e}", exc_info=True)
            return f"抱歉，处理您的请求时出现错误：{str(e)}"

    def _load_context(
        self,
        user_id: Optional[str],
        conversation_id: Optional[str]
    ) -> Optional[str]:
        """
        加载记忆上下文

        Args:
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            上下文文本
        """
        if not self.memory_service:
            return None

        try:
            # 调用记忆服务构建增强提示
            context = self.memory_service.build_enhanced_prompt(
                user_id=user_id,
                conversation_id=conversation_id
            )
            logger.info(f"[OrchestratorAgent] 加载上下文，长度 {len(context)} 字符")
            return context

        except Exception as e:
            logger.warning(f"[OrchestratorAgent] 加载上下文失败: {e}")
            return None

    def _try_fast_path(self, query: str, context: Optional[str]) -> Optional[str]:
        """
        尝试快路径（规则匹配）

        Args:
            query: 用户查询
            context: 上下文信息

        Returns:
            如果命中快路径，返回结果；否则返回 None
        """
        # 检查是否命中快路径规则
        matched_type = None
        for rule_type, keywords in self.fast_rules.items():
            if any(keyword in query for keyword in keywords):
                matched_type = rule_type
                break

        if not matched_type:
            return None

        logger.info(f"[OrchestratorAgent] 命中快路径: {matched_type}")

        # 映射规则类型到工具名称
        tool_mapping = {
            "weather": "query_weather",
            "flight": "search_flights",
            "hotel": "search_hotels",
            "policy": "search_policy",
        }

        tool_name = tool_mapping.get(matched_type)
        if not tool_name or tool_name not in self.tools:
            logger.warning(f"[OrchestratorAgent] 快路径工具 {tool_name} 不存在")
            return None

        try:
            tool = self.tools[tool_name]

            # 执行工具（传入查询作为参数）
            result = tool.execute(query=query)
            track_tool_call_metric(tool_name, success=True)

            track_tool_call_metric(tool_name, success=True)
            return result

        except Exception as e:
            logger.error(f"[OrchestratorAgent] 快路径执行失败: {e}")
            return None

    def _is_approval_query(self, query: str) -> bool:
        """
        判断是否为审批域查询

        Args:
            query: 用户查询

        Returns:
            是否为审批域查询
        """
        return any(keyword in query for keyword in self.approval_keywords)

    def _route_to_approval(
        self,
        query: str,
        user_id: Optional[str],
        conversation_id: Optional[str]
    ) -> str:
        """
        路由到审批域

        Args:
            query: 用户查询
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            审批结果
        """
        if self._approval_engine:
            return self._approval_engine.execute(
                query=query,
                user_id=user_id,
                conversation_id=conversation_id
            )
        else:
            logger.warning("[OrchestratorAgent] 审批域引擎未实现")
            return "抱歉，审批功能暂未开放，请稍后再试。"

    def _update_memory(
        self,
        query: str,
        result: str,
        user_id: Optional[str],
        conversation_id: Optional[str]
    ) -> None:
        """
        更新记忆

        Args:
            query: 用户查询
            result: 系统回复
            user_id: 用户ID
            conversation_id: 会话ID
        """
        if not self.memory_service:
            return

        try:
            # 保存对话历史
            self.memory_service.process_user_message(
                user_id=user_id,
                conversation_id=conversation_id,
                message=query
            )

            self.memory_service.process_assistant_message(
                user_id=user_id,
                conversation_id=conversation_id,
                message=result
            )

            logger.info("[OrchestratorAgent] 记忆更新完成")

        except Exception as e:
            logger.warning(f"[OrchestratorAgent] 记忆更新失败: {e}")

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            统计数据字典
        """
        stats = self.stats.copy()

        # 添加 QAEngine 的统计信息
        if self._qa_engine:
            stats["qa_engine"] = self._qa_engine.get_stats()

        return stats

    def reset_stats(self) -> None:
        """重置统计信息"""
        for key in self.stats:
            self.stats[key] = 0

        if self._qa_engine:
            self._qa_engine.reset_stats()

        logger.info("[OrchestratorAgent] 统计信息已重置")
