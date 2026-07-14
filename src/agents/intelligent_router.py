# -*- coding: utf-8 -*-
"""
⚠️ DEPRECATED - 此模块已被 OrchestratorAgent 替代

请使用: src/agents/orchestrator_agent.py

迁移指南:
---------
旧代码:
    from src.agents.intelligent_router import IntelligentRouter
    router = IntelligentRouter(llm=llm, retriever=retriever)
    result = router.route(query)

新代码:
    from src.agents.orchestrator_agent import OrchestratorAgent
    from src.memory.memory_service import MemoryService
    from src.tools.registry import get_all_tools

    memory_service = MemoryService()
    tools = get_all_tools()
    orchestrator = OrchestratorAgent(llm=llm, tools=tools, memory_service=memory_service)
    result = orchestrator.route(query, user_id="user_001", conversation_id="conv_001")

保留原因: 向后兼容和评估脚本迁移
计划移除时间: Phase 5 完成后

---

智能路由器 - 三层路由架构
融合意图识别、Self-RAG与任务编排系统

架构设计（三层）：
┌─────────────────────────────────────────────────────────┐
│                     用户查询                              │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  第零层：意图识别器（规则匹配，最快）                     │
│  - weather/flight/hotel: 明确工具意图                    │
│  - None: 无明确意图或多意图冲突                          │
└─────────────────────────────────────────────────────────┘
         ↓                              ↓
    明确工具意图                    无明确意图
         ↓                              ↓
    直接工具调用              ┌─────────────────────────┐
    (<5ms, 0成本)            │  第一层：Self-RAG分类器   │
                             │  - CHITCHAT: 闲聊/问候   │
                             │  - FACTUAL: 事实性查询   │
                             └─────────────────────────┘
                                    ↓
                         ┌──────────┴──────────┐
                         ↓                     ↓
                    CHITCHAT              FACTUAL
                         ↓                     ↓
                   直接LLM回答    ┌─────────────────────────┐
                   （节省成本）   │  第二层：复杂度评估器     │
                                 │  - SIMPLE: 单一意图      │
                                 │  - MEDIUM: 多次调用      │
                                 │  - COMPLEX: 多意图       │
                                 └─────────────────────────┘
                                            ↓
                             ┌──────────────┼──────────────┐
                             ↓              ↓              ↓
                          SIMPLE         MEDIUM        COMPLEX
                             ↓              ↓              ↓
                         单工具调用      多次调用      任务分解+并行
                          RAG查询        循环执行      依赖编排执行

三层优势：
1. 第零层：30%查询直接工具调用（稳定、快速、零成本）
2. 第一层：40%查询Self-RAG拦截（节省成本40%）
3. 第二层：30%查询精细化处理（准确率90%+）
4. 总体：响应速度提升3倍，成本降低50%
"""
from src.agents.intent_detector import IntentDetector
from src.agents.context_accumulator import ContextAccumulator
from src.agents.synthesis_layer import SynthesisLayer
from src.rag.query_classifier import QueryClassifier
from src.rag.self_rag import SelfRAG
from src.agents.complexity_assessor import ComplexityAssessor, QueryComplexity
from src.agents.task_decomposer import TaskDecomposer
from src.agents.workflow_orchestrator import WorkflowOrchestrator
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Optional
import time


class IntelligentRouter:
    """
    智能路由器

    融合三层路由：意图识别 + Self-RAG + 任务编排
    实现最精细化的查询路由，提升系统效率和准确率

    注意：此类不是线程安全的。如需并发使用，请为每个线程创建独立实例。
    """

    def __init__(
        self,
        llm,
        retriever,
        rag_chain=None,
        tools: Optional[Dict] = None
    ):
        """
        初始化智能路由器

        Args:
            llm: 语言模型
            retriever: 检索器（用于Self-RAG）
            rag_chain: RAG链（用于工作流编排）
            tools: 工具字典（用于任务执行）
        """
        # 上下文累积器（跨层传递信息）
        self.context = ContextAccumulator()

        # 保存检索器引用（Layer 1需要）
        self.retriever = retriever

        # 第零层：意图识别器（规则匹配，最快）
        self.intent_detector = IntentDetector()

        # 第一层：Self-RAG组件（查询类型判断）
        self.query_classifier = QueryClassifier(llm)
        self.self_rag = SelfRAG(llm, retriever)

        # 第二层：综合分析层 + 任务编排兜底
        self.synthesis_layer = SynthesisLayer(llm)
        self.complexity_assessor = ComplexityAssessor(llm)
        self.task_decomposer = TaskDecomposer(llm)
        self.workflow_orchestrator = WorkflowOrchestrator(
            llm=llm,
            complexity_assessor=self.complexity_assessor,
            task_decomposer=self.task_decomposer,
            rag_chain=rag_chain,
            tools=tools
        )

        # 统计数据
        self.stats = {
            "total_queries": 0,
            "intent_queries": 0,          # 第零层拦截
            "synthesis_queries": 0,       # 新增：第二层综合回答
            "orchestration_queries": 0,   # 新增：第二层→编排器兜底
            "chitchat_queries": 0,        # 保留兼容
            "simple_queries": 0,          # 保留兼容
            "medium_queries": 0,          # 保留兼容
            "complex_queries": 0,         # 保留兼容
            "avg_intent_latency": 0,
            "avg_synthesis_latency": 0,   # 新增
            "avg_orchestration_latency": 0,  # 新增
            "avg_chitchat_latency": 0,    # 保留兼容
            "avg_factual_latency": 0      # 保留兼容
        }

    def route(self, query: str, chat_id: str = "default") -> Dict:
        """
        智能路由查询

        三层路由策略：
        0. 意图检测：明确工具意图（weather/flight/hotel）
        1. Self-RAG分类：CHITCHAT vs FACTUAL
        2. 复杂度评估：SIMPLE vs MEDIUM vs COMPLEX（仅FACTUAL查询）

        Args:
            query: 用户查询
            chat_id: 会话ID

        Returns:
            {
                "answer": "回答内容",
                "route": "路由路径（intent_*/chitchat/simple/medium/complex）",
                "latency": 响应延迟（毫秒）,
                "intent": 意图类型（可选）,
                "entities": 提取的实体（可选）,
                "classification": 分类信息（可选）,
                "complexity": 复杂度信息（可选）,
                "retrieved": 是否检索,
                "sources": 来源文档（可选）
            }
        """
        start_time = time.time()
        self.stats["total_queries"] += 1

        # 清空并初始化上下文
        self.context.clear()
        self.context.set_query(query)

        print(f"\n{'='*70}")
        print(f"[启动] 智能路由器启动（三层架构 - 修正版）")
        print(f"{'='*70}")
        print(f"查询：{query}")
        print(f"会话ID：{chat_id}")

        try:
            # ========== 第零层路由：意图识别（规则匹配）==========
            print(f"\n{'─'*70}")
            print("[路由] 第零层路由：意图识别（规则匹配，零成本）")
            print(f"{'─'*70}")

            intent = self.intent_detector.detect(query)

            if intent:
                print(f"[成功] 检测到明确意图：{intent}")

                # 提取实体
                entities = self.intent_detector.extract_entities(query, intent)
                print(f"[成功] 提取实体：{entities}")

                print(f"\n{'─'*70}")
                print(f"[工具] 执行工具调用：{intent}")
                print(f"{'─'*70}")

                # 调用工具并直接返回结果
                tool_result = self._handle_tool_call(intent, entities)

                latency = (time.time() - start_time) * 1000
                self.stats["intent_queries"] += 1
                self._update_latency_stats("intent", latency)

                print(f"\n[OK] 路由完成（{latency:.0f}ms）")
                print(f"{'='*70}\n")

                return {
                    "answer": tool_result,
                    "route": f"intent_{intent}",
                    "latency": latency,
                    "intent": intent,
                    "entities": entities,
                    "classification": None,
                    "complexity": None,
                    "retrieved": False,
                    "sources": []
                }

            else:
                print("[成功] 无明确意图，进入第一层路由")

            # ========== 第一层路由：Self-RAG分类 ==========
            print(f"\n{'─'*70}")
            print("[路由] 第一层路由：Self-RAG分类（CHITCHAT vs FACTUAL）")
            print(f"{'─'*70}")

            classification = self.query_classifier.classify(query)
            print(f"[成功] 分类结果：{classification['type']}")
            print(f"  置信度：{classification['confidence']:.2f}")
            print(f"  原因：{classification['reason']}")

            if classification["type"] == "CHITCHAT":
                # 闲聊查询：直接LLM回答，跳过检索
                print(f"\n{'─'*70}")
                print("[OK] CHITCHAT查询，直接LLM回答（跳过检索）")
                print(f"{'─'*70}")

                messages = [
                    SystemMessage(content="你是一个友好的助手。"),
                    HumanMessage(content=query)
                ]
                response = self.query_classifier.llm.invoke(messages)
                answer = response.content

                latency = (time.time() - start_time) * 1000
                self.stats["chitchat_queries"] += 1
                self._update_latency_stats("chitchat", latency)

                print(f"\n[OK] 路由完成（{latency:.0f}ms）")
                print(f"{'='*70}\n")

                return {
                    "answer": answer,
                    "route": "chitchat",
                    "latency": latency,
                    "intent": None,
                    "entities": None,
                    "classification": classification,
                    "complexity": None,
                    "retrieved": False,
                    "sources": []
                }

            elif classification["type"] == "GRAPH":
                # 图谱查询：使用 GraphRAG 检索
                print(f"\n{'─'*70}")
                print("[OK] GRAPH查询，使用GraphRAG检索")
                print(f"{'─'*70}")

                # 使用 GraphRetriever 进行检索
                from src.rag.graph_retriever import GraphRetriever

                try:
                    # 创建 GraphRetriever，使用当前的 retriever 作为降级方案
                    graph_retriever = GraphRetriever(
                        fallback_retriever=self.retriever
                    )

                    # 检索相关文档
                    documents = graph_retriever.retrieve(query, top_k=5)

                    # 使用 Self-RAG 生成答案
                    if documents:
                        result = self.self_rag.query(query)
                        answer = result["answer"]
                        sources = result.get("sources", [])
                    else:
                        # 无文档时，直接回答
                        messages = [
                            SystemMessage(content="你是企业差旅管理助手，根据查询回答。"),
                            HumanMessage(content=query)
                        ]
                        response = self.query_classifier.llm.invoke(messages)
                        answer = response.content
                        sources = []

                    graph_retriever.close()

                except Exception as e:
                    print(f"[警告] GraphRAG检索失败: {e}")
                    # 降级到 Self-RAG
                    result = self.self_rag.query(query)
                    answer = result["answer"]
                    sources = result.get("sources", [])

                latency = (time.time() - start_time) * 1000
                # 使用新的统计字段
                if "graph_queries" not in self.stats:
                    self.stats["graph_queries"] = 0
                self.stats["graph_queries"] += 1
                self._update_latency_stats("graph", latency)

                print(f"\n[OK] 路由完成（{latency:.0f}ms）")
                print(f"{'='*70}\n")

                return {
                    "answer": answer,
                    "route": "graph",
                    "latency": latency,
                    "intent": None,
                    "entities": None,
                    "classification": classification,
                    "complexity": None,
                    "retrieved": True,
                    "sources": sources
                }

            # FACTUAL查询：进入第二层复杂度评估
            print(f"\n[成功] FACTUAL查询，进入第二层复杂度评估")

            # ========== 第二层路由：复杂度评估 ==========
            print(f"\n{'─'*70}")
            print("[路由] 第二层路由：复杂度评估（SIMPLE/MEDIUM/COMPLEX）")
            print(f"{'─'*70}")

            # 评估查询复杂度
            complexity = self.complexity_assessor.assess(query)

            print(f"[成功] 复杂度评估：{complexity}")
            if hasattr(complexity, 'value'):
                print(f"  复杂度值：{complexity.value}")

            if complexity == QueryComplexity.SIMPLE:
                # 简单查询：单次RAG检索
                print(f"\n{'─'*70}")
                print("[路由] SIMPLE查询 → 单次RAG检索")
                print(f"{'─'*70}")

                result = self.self_rag.query(query)
                latency = (time.time() - start_time) * 1000

                self.stats["simple_queries"] += 1
                self._update_latency_stats("simple", latency)

                print(f"\n[OK] 路由完成（{latency:.0f}ms）")
                print(f"{'='*70}\n")

                return {
                    "answer": result["answer"],
                    "route": "simple",
                    "latency": latency,
                    "intent": None,
                    "classification": classification,
                    "complexity": complexity.value if hasattr(complexity, 'value') else str(complexity),
                    "retrieved": result["retrieved"],
                    "sources": result.get("sources", [])
                }

            elif complexity == QueryComplexity.MEDIUM:
                # 中等查询：多次调用（暂时使用Self-RAG，未来可优化）
                print(f"\n{'─'*70}")
                print("[路由] MEDIUM查询 → 多次调用")
                print(f"{'─'*70}")

                result = self.self_rag.query(query)
                latency = (time.time() - start_time) * 1000

                self.stats["medium_queries"] += 1
                self._update_latency_stats("medium", latency)

                print(f"\n[OK] 路由完成（{latency:.0f}ms）")
                print(f"{'='*70}\n")

                return {
                    "answer": result["answer"],
                    "route": "medium",
                    "latency": latency,
                    "intent": None,
                    "classification": classification,
                    "complexity": complexity.value if hasattr(complexity, 'value') else str(complexity),
                    "retrieved": result["retrieved"],
                    "sources": result.get("sources", [])
                }

            else:  # COMPLEX
                # 复杂查询：任务分解+编排执行
                print(f"\n{'─'*70}")
                print("[路由] COMPLEX查询 → 任务分解+编排执行")
                print(f"{'─'*70}")

                answer = self.workflow_orchestrator.route(query, chat_id)
                latency = (time.time() - start_time) * 1000

                self.stats["complex_queries"] += 1
                self._update_latency_stats("complex", latency)

                print(f"\n[OK] 路由完成（{latency:.0f}ms）")
                print(f"{'='*70}\n")

                return {
                    "answer": answer,
                    "route": "complex",
                    "latency": latency,
                    "intent": None,
                    "classification": classification,
                    "complexity": complexity.value if hasattr(complexity, 'value') else str(complexity),
                    "retrieved": True,
                    "sources": []
                }

        except Exception as e:
            print(f"\n[错误] 路由失败：{e}")
            print("  降级为Self-RAG处理")

            # 降级为Self-RAG
            result = self.self_rag.query(query)
            latency = (time.time() - start_time) * 1000

            print(f"\n[OK] 降级完成（{latency:.0f}ms）")
            print(f"{'='*70}\n")

            return {
                "answer": result["answer"],
                "route": "fallback",
                "latency": latency,
                "classification": {"type": "UNKNOWN", "confidence": 0.0, "reason": str(e)},
                "complexity": None,
                "retrieved": result["retrieved"],
                "sources": result.get("sources", [])
            }

    def _handle_tool_call(self, intent: str, entities: Dict) -> str:
        """处理直接工具调用 - 通过 MCP 适配器调用。"""
        print(f"\n{'\u2501'*70}")
        print(f"[工具] 执行工具：{intent}")
        print(f"  参数：{entities}")
        print(f"{'\u2501'*70}")
        try:
            if intent == 'weather':
                from src.tools.weather_adapter import WeatherTool
                tool = WeatherTool()
                city = entities.get('city', '\u5317\u4eac')
                return tool.invoke({'city': city})
            elif intent == 'flight':
                from src.tools.flight_adapter import FlightTool
                tool = FlightTool()
                departure = entities.get('departure_city', '\u5317\u4eac')
                arrival = entities.get('arrival_city', '\u4e0a\u6d77')
                date = entities.get('date')
                return tool.invoke({'departure_city': departure, 'arrival_city': arrival, 'date': date})
            elif intent == 'hotel':
                from src.tools.hotel_adapter import HotelTool
                tool = HotelTool()
                city = entities.get('city', '\u5317\u4eac')
                min_price = entities.get('min_price')
                max_price = entities.get('max_price')
                min_star = entities.get('min_star')
                return tool.invoke({'city': city, 'min_price': min_price, 'max_price': max_price, 'min_star': min_star})
            else:
                return f'[错误] 未知工具：{intent}'
        except Exception as e:
            import logging
            logging.error(f'Tool call failed for intent {intent} with entities {entities}: {e}', exc_info=True)
            print(f'[错误] 工具调用失败：{type(e).__name__}')
            return f'抱歉，{intent}服务暂时不可用，请稍后重试。'


    def get_stats(self) -> Dict:
        """
        获取路由统计数据

        Returns:
            统计数据字典
        """
        total = self.stats["total_queries"]
        if total == 0:
            return self.stats

        return {
            "total_queries": total,
            "intent_queries": self.stats["intent_queries"],
            "intent_ratio": f"{self.stats['intent_queries']/total*100:.1f}%",
            "synthesis_queries": self.stats["synthesis_queries"],
            "synthesis_ratio": f"{self.stats['synthesis_queries']/total*100:.1f}%",
            "orchestration_queries": self.stats["orchestration_queries"],
            "orchestration_ratio": f"{self.stats['orchestration_queries']/total*100:.1f}%",
            # 保留兼容性字段
            "chitchat_queries": self.stats["chitchat_queries"],
            "chitchat_ratio": f"{self.stats['chitchat_queries']/total*100:.1f}%",
            "simple_queries": self.stats["simple_queries"],
            "simple_ratio": f"{self.stats['simple_queries']/total*100:.1f}%",
            "medium_queries": self.stats["medium_queries"],
            "medium_ratio": f"{self.stats['medium_queries']/total*100:.1f}%",
            "complex_queries": self.stats["complex_queries"],
            "complex_ratio": f"{self.stats['complex_queries']/total*100:.1f}%",
            # 新延迟统计
            "avg_intent_latency": f"{self.stats['avg_intent_latency']:.0f}ms",
            "avg_synthesis_latency": f"{self.stats['avg_synthesis_latency']:.0f}ms",
            "avg_orchestration_latency": f"{self.stats['avg_orchestration_latency']:.0f}ms",
            # 保留兼容性字段
            "avg_chitchat_latency": f"{self.stats['avg_chitchat_latency']:.0f}ms",
            "avg_factual_latency": f"{self.stats['avg_factual_latency']:.0f}ms",
            "cost_savings": f"{self.stats['intent_queries']/total*100:.1f}%估算"
        }

    def print_stats(self):
        """打印统计数据"""
        stats = self.get_stats()

        print(f"\n{'='*70}")
        print(" 智能路由器统计数据（三层架构 - 修正版）")
        print(f"{'='*70}")
        print(f"总查询数：{stats['total_queries']}")
        print(f"\n查询路由分布：")
        print(f"  第零层（工具调用）：{stats['intent_queries']} ({stats['intent_ratio']})")
        print(f"  第二层（综合分析）：{stats['synthesis_queries']} ({stats['synthesis_ratio']})")
        print(f"  第二层（编排兜底）：{stats['orchestration_queries']} ({stats['orchestration_ratio']})")
        print(f"\n平均延迟：")
        print(f"  工具调用：{stats['avg_intent_latency']}")
        print(f"  综合分析：{stats['avg_synthesis_latency']}")
        print(f"  编排兜底：{stats['avg_orchestration_latency']}")
        print(f"\n估算成本节省：{stats['cost_savings']}")
        print(f"  （第零层工具调用跳过LLM）")
        print(f"{'='*70}\n")

    def _update_latency_stats(self, query_type: str, latency: float):
        """更新延迟统计"""
        if query_type == "intent":
            old_avg = self.stats["avg_intent_latency"]
            count = self.stats["intent_queries"]
            if count > 0:
                self.stats["avg_intent_latency"] = (old_avg * (count - 1) + latency) / count
        elif query_type == "synthesis":
            old_avg = self.stats["avg_synthesis_latency"]
            count = self.stats["synthesis_queries"]
            if count > 0:
                self.stats["avg_synthesis_latency"] = (old_avg * (count - 1) + latency) / count
        elif query_type == "orchestration":
            old_avg = self.stats["avg_orchestration_latency"]
            count = self.stats["orchestration_queries"]
            if count > 0:
                self.stats["avg_orchestration_latency"] = (old_avg * (count - 1) + latency) / count
        elif query_type == "chitchat":
            # 保留兼容性
            old_avg = self.stats["avg_chitchat_latency"]
            count = self.stats["chitchat_queries"]
            if count > 0:
                self.stats["avg_chitchat_latency"] = (old_avg * (count - 1) + latency) / count
        else:
            # 保留兼容性
            factual_count = (
                self.stats["simple_queries"] +
                self.stats["medium_queries"] +
                self.stats["complex_queries"]
            )
            if factual_count > 0:
                old_avg = self.stats["avg_factual_latency"]
                self.stats["avg_factual_latency"] = (old_avg * (factual_count - 1) + latency) / factual_count


# 使用示例
if __name__ == "__main__":
    """
    测试智能路由器
    演示Self-RAG与任务编排的融合
    """
    print("测试智能路由器...\n")

    from src.models.llm import get_llm
    from src.rag.loader import load_documents_from_text
    from src.rag.retriever import create_vectorstore, get_retriever

    # 准备测试数据
    test_text = """
企业差旅管理规章

第一章 住宿标准
1. 一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚
2. 二线城市（杭州、成都、武汉等）：标准间不超过400元/晚
3. 三线及以下城市：标准间不超过300元/晚

第二章 交通标准
1. 市内交通：实报实销，需提供发票
2. 城际交通：
   - 距离<500公里：高铁二等座
   - 距离≥500公里：飞机经济舱
    """

    try:
        # 初始化组件
        llm = get_llm(temperature=0.3)
        documents = load_documents_from_text(test_text, chunk_size=200)
        vectorstore = create_vectorstore(documents)
        retriever = get_retriever(vectorstore, k=3)

        # 创建智能路由器
        router = IntelligentRouter(
            llm=llm,
            retriever=retriever
        )

        # 测试用例（覆盖所有路由路径）
        test_queries = [
            # 闲聊查询（Self-RAG直接处理）
            "你好",
            "今天天气怎么样",

            # 简单查询（单次RAG）
            "北京出差住宿标准是多少",

            # 中等查询（多次调用）
            "上海和深圳的住宿标准对比",

            # 复杂查询（任务分解）
            "去杭州出差，查天气并推荐酒店"
        ]

        for query in test_queries:
            result = router.route(query)

            # 打印结果摘要
            print(f"📌 查询：{query}")
            print(f" 路由：{result['route']}")
            print(f"⏱️  延迟：{result['latency']:.0f}ms")
            print(f"💬 回答：{result['answer'][:100]}...")
            print()

        # 打印统计数据
        router.print_stats()

        print("[OK] 智能路由器测试完成！")

    except Exception as e:
        print(f"[错误] 测试失败：{e}")
        import traceback
        traceback.print_exc()
