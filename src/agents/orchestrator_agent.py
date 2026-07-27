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

        # 快路径规则（关键词匹配）- 严格模式，避免过度拦截
        self.fast_rules = {
            "weather": ["天气", "温度", "下雨", "气温", "冷不冷", "热不热"],
            "flight": ["航班信息", "机票查询", "航班查询"],  # 更精确
            "hotel": ["酒店推荐", "宾馆推荐", "住宿推荐"],   # 更精确
            # 移除 policy 规则，避免拦截复杂查询（"标准"太宽泛）
        }

        # 复杂查询特征（排除词）
        self.complex_keywords = [
            "比较", "对比", "分析", "规划", "帮我", "怎么",
            "为什么", "哪个", "推荐", "建议", "安排"
        ]

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
    ) -> tuple[str, str]:
        """
        三层路由架构

        流程：
        【第1层】快路径（规则匹配）- 减少LLM调用
        【第2层】LLM意图识别 - 判断业务域（审批/Q&A/闲聊）
        【第3层】Q&A域内路由 - 由QAEngine处理4通道

        Args:
            query: 用户查询
            user_id: 用户ID（可选）
            conversation_id: 会话ID（可选）

        Returns:
            (答案文本, 路由类型)
        """
        logger.info(f"[OrchestratorAgent] 收到查询: {query}")
        start_time = time.time()
        self.stats["total"] += 1

        try:
            # ========== 第1层：快路径（规则匹配，无需上下文）==========
            # 性能优化：快路径不需要记忆上下文，避免15-20秒延迟
            fast_result = self._try_fast_path(query, context=None)
            if fast_result:
                self.stats["fast_path"] += 1
                elapsed = time.time() - start_time
                logger.info(f"[第1层-快路径] ✅ 命中，耗时 {elapsed:.2f}s")
                track_unified_metric(
                    domain="fast_path",
                    channel="rule",
                    duration_seconds=elapsed,
                    success=True
                )
                return fast_result, "fast_path"

            # ========== 仅在快路径未命中时才加载上下文 ==========
            logger.info("[第1层] 快路径未命中，开始加载记忆上下文")
            context_start = time.time()
            context = self._load_context(user_id, conversation_id)
            context_elapsed = time.time() - context_start
            logger.info(f"[记忆服务] 上下文加载完成，耗时 {context_elapsed:.2f}s")

            # ========== 第2层：LLM意图识别（业务域）==========
            logger.info("[第2层] 使用LLM判断意图")
            intent = self._llm_classify_intent(query)
            logger.info(f"[第2层] LLM判断结果: {intent}")

            # 审批域
            if intent == "approval":
                self.stats["approval_domain"] += 1
                logger.info("[第2层] 路由到审批域")
                result = self._route_to_approval(query, user_id, conversation_id)
                elapsed = time.time() - start_time
                logger.info(f"[第2层-审批域] 完成，耗时 {elapsed:.2f}s")
                track_unified_metric(
                    domain="approval",
                    channel="llm",
                    duration_seconds=elapsed,
                    success=True
                )
                return result, "approval_domain"

            # 闲聊
            elif intent == "chat":
                logger.info("[第2层] 识别为闲聊，简单回复")
                result = self._handle_chat(query)
                elapsed = time.time() - start_time
                return result, "chat"

            # Q&A域（默认）
            else:
                self.stats["qa_domain"] += 1
                logger.info("[第2层] 路由到Q&A域")
                # ========== 第3层：QAEngine内部4通道路由 ==========
                result = self.qa_engine.execute(
                    query=query,
                    context=context,
                    user_id=user_id,
                    conversation_id=conversation_id
                )

                # 记忆更新
                self._update_memory(query, result, user_id, conversation_id)

                elapsed = time.time() - start_time
                logger.info(f"[第3层-Q&A域] 完成，耗时 {elapsed:.2f}s")
                track_unified_metric(
                    domain="qa",
                    channel="unknown",
                    duration_seconds=elapsed,
                    success=True
                )
                return result, "qa_domain"

        except Exception as e:
            logger.error(f"[OrchestratorAgent] 路由失败: {e}", exc_info=True)
            return f"抱歉，处理您的请求时出现错误：{str(e)}", "error"

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

        规则：
        1. 排除复杂查询特征（比较、分析、规划等）
        2. 精确关键词匹配（天气、酒店推荐、航班查询）
        3. 长度限制（避免复杂查询）

        Args:
            query: 用户查询
            context: 上下文信息

        Returns:
            如果命中快路径，返回结果；否则返回 None
        """
        logger.info(f"[_try_fast_path] 开始检查快路径，查询: {query}")

        # 第一步：排除复杂查询特征
        if any(keyword in query for keyword in self.complex_keywords):
            logger.info(f"[_try_fast_path] 检测到复杂查询特征，跳过快路径")
            return None

        # 第二步：长度限制（复杂查询通常较长）
        if len(query) > 20:
            logger.info(f"[_try_fast_path] 查询过长（{len(query)}字符），跳过快路径")
            return None

        # 第三步：检查是否命中快路径规则
        matched_type = None
        for rule_type, keywords in self.fast_rules.items():
            if any(keyword in query for keyword in keywords):
                matched_type = rule_type
                logger.info(f"[_try_fast_path] 匹配到规则: {rule_type}")
                break

        if not matched_type:
            logger.info(f"[_try_fast_path] 未匹配任何快路径规则")
            return None

        logger.info(f"[_try_fast_path] 命中快路径: {matched_type}")

        # 映射规则类型到工具名称
        tool_mapping = {
            "weather": "query_weather",
            "flight": "search_flights",
            "hotel": "search_hotels",
            "policy": "search_policy",
        }

        tool_name = tool_mapping.get(matched_type)
        logger.info(f"[_try_fast_path] 映射到工具: {tool_name}")

        if not tool_name or tool_name not in self.tools:
            logger.warning(f"[_try_fast_path] 快路径工具 {tool_name} 不存在，可用工具: {list(self.tools.keys())}")
            return None

        try:
            tool = self.tools[tool_name]
            logger.info(f"[_try_fast_path] 开始执行工具: {tool_name}")

            # 执行工具 - 针对不同工具类型传入不同参数
            if matched_type == "weather":
                # 天气工具：从查询中提取城市名
                city = query.replace("天气", "").replace("温度", "").replace("气温", "").strip()
                result = tool.invoke({"city": city})

            elif matched_type == "hotel":
                # 酒店工具：提取城市名（其他参数可选）
                city = query.replace("酒店", "").replace("宾馆", "").replace("住宿", "").replace("推荐", "")
                city = city.replace("有什么", "").replace("哪里有", "").strip()
                result = tool.invoke({"city": city})

            elif matched_type == "flight":
                # 航班工具：提取出发地和目的地
                # 简单实现：寻找"到"字分割
                if "到" in query:
                    parts = query.split("到")
                    departure_city = parts[0].replace("航班", "").replace("机票", "").replace("飞机", "").strip()
                    arrival_city = parts[1].replace("的航班", "").replace("航班", "").replace("机票", "").strip()
                    result = tool.invoke({"departure_city": departure_city, "arrival_city": arrival_city})
                else:
                    # 无法提取，返回None让LLM处理
                    logger.warning(f"[_try_fast_path] 无法从查询中提取航班参数: {query}")
                    return None

            else:
                # 其他工具（如政策查询）：直接传入查询
                result = tool.invoke({"query": query})

            logger.info(f"[_try_fast_path] 工具执行成功，结果长度: {len(str(result))}")
            track_tool_call_metric(tool_name, success=True)
            return result

        except Exception as e:
            logger.error(f"[_try_fast_path] 快路径执行失败: {e}", exc_info=True)
            return None

    def _is_approval_query(self, query: str) -> bool:
        """
        判断是否为审批域查询（已废弃，保留向后兼容）

        注意：现在使用LLM意图识别，此方法仅作兜底

        Args:
            query: 用户查询

        Returns:
            是否为审批域查询
        """
        return any(keyword in query for keyword in self.approval_keywords)

    def _llm_classify_intent(self, query: str) -> str:
        """
        使用LLM判断用户意图（业务域分类）

        分类：
        - approval: 报销申请、审批查询
        - qa: 政策咨询、信息查询、出差规划
        - chat: 问候、闲聊

        Args:
            query: 用户查询

        Returns:
            意图类型: "approval" | "qa" | "chat"
        """
        try:
            prompt = f"""你是一个意图识别专家。判断用户查询属于哪个业务类型。

用户查询: {query}

业务类型定义：
1. approval（审批域）- 用户想要提交报销申请、查询审批进度、取消申请
   示例：
   - "我要报销去北京出差的费用800元"
   - "我的审批进度怎么样了"
   - "提交一个出差申请"
   - "取消我的报销申请"

2. qa（问答域）- 用户想要查询信息、获取建议、规划行程
   示例：
   - "北京的住宿标准是多少"
   - "去杭州出差3天需要多少钱"
   - "帮我安排下周去深圳出差"
   - "飞机和高铁哪个划算"
   - "上海有什么酒店推荐"

3. chat（闲聊）- 问候、感谢、无关内容
   示例：
   - "你好"
   - "谢谢"
   - "今天天气真好"
   - "你是谁"

只返回一个词: approval 或 qa 或 chat

判断:"""

            response = self.llm.invoke(prompt)
            content = response.content.lower().strip()

            # 解析LLM响应
            if "approval" in content:
                return "approval"
            elif "chat" in content:
                return "chat"
            else:
                return "qa"  # 默认Q&A域

        except Exception as e:
            logger.error(f"[OrchestratorAgent] LLM意图识别失败: {e}")
            # 降级：使用关键词匹配
            if self._is_approval_query(query):
                return "approval"
            else:
                return "qa"

    def _handle_chat(self, query: str) -> str:
        """
        处理闲聊（简单回复）

        Args:
            query: 用户查询

        Returns:
            回复文本
        """
        # 简单的闲聊响应
        greetings = ["你好", "您好", "hi", "hello"]
        thanks = ["谢谢", "感谢", "thank"]

        query_lower = query.lower()

        if any(g in query_lower for g in greetings):
            return "您好！我是差旅助手，可以帮您查询差旅政策、办理报销申请。有什么可以帮您的吗？"
        elif any(t in query_lower for t in thanks):
            return "不客气！很高兴能帮到您。如有其他问题，随时问我。"
        else:
            return "我是差旅助手，专注于差旅政策咨询和报销申请。您可以问我关于出差的问题哦。"

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
                user_message=query
            )

            self.memory_service.process_assistant_message(
                conversation_id=conversation_id,
                assistant_message=result
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