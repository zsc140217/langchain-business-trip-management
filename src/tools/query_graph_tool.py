# -*- coding: utf-8 -*-
"""
图谱查询工具 - 封装 GraphRAG 检索能力

使用 Neo4j 知识图谱进行关系查询
"""
from src.tools.base_tool import BaseTool
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class QueryGraphTool(BaseTool):
    """
    图谱查询工具

    使用 Neo4j 知识图谱查询实体关系、组织架构等信息
    """

    name: str = "query_graph"
    description: str = """查询知识图谱中的实体关系和组织架构信息。

适用场景：
- 查询实体关系（如"A 和 B 的关系"）
- 查询组织架构（如"某人的上级是谁"）
- 查询人员信息（如"销售部有哪些员工"）
- 统计查询（如"出差最多的员工"）
- 多实体关联（如"涉及哪些部门"）

输入参数：
- query: 查询问题（字符串）

返回：图谱查询结果的文本描述
"""

    cache_enabled: bool = True
    cache_ttl_seconds: int = 300  # 图谱数据变化较少，缓存5分钟

    def __init__(self, graph_retriever=None, **kwargs):
        """
        初始化图谱查询工具

        Args:
            graph_retriever: GraphRetriever 实例
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        # 使用私有属性避免 Pydantic 验证
        self._graph_retriever = graph_retriever
        self._initialized = False
        self._neo4j_available = False  # 标记Neo4j是否可用

    def _lazy_init(self):
        """延迟初始化图谱检索器（带降级处理）"""
        if self._initialized:
            return

        if self._graph_retriever is None:
            logger.info("[QueryGraphTool] 延迟初始化图谱检索器")
            try:
                from src.rag.graph_retriever import GraphRetriever

                # 尝试创建图谱检索器
                self._graph_retriever = GraphRetriever(
                    fallback_retriever=None  # 图谱专用工具，不需要降级
                )
                self._neo4j_available = True
                logger.info("[QueryGraphTool] 图谱检索器初始化完成，Neo4j 可用")

            except Exception as e:
                # Neo4j 连接失败，记录警告但不抛出异常
                logger.warning(f"[QueryGraphTool] Neo4j 不可用: {e}")
                self._neo4j_available = False
                self._graph_retriever = None
                # 不抛出异常，允许工具初始化成功

        self._initialized = True

    def _run(self, query: str, **kwargs) -> str:
        """
        执行图谱查询

        Args:
            query: 查询问题
            **kwargs: 其他参数（如 top_k）

        Returns:
            查询结果文本
        """
        # 延迟初始化
        self._lazy_init()

        if not query or not query.strip():
            raise ValueError("查询不能为空")

        logger.info(f"[QueryGraphTool] 查询: {query}")

        # 检查 Neo4j 是否可用
        if not self._neo4j_available or self._graph_retriever is None:
            return (
                "图谱查询服务暂时不可用（Neo4j 未连接）。\n"
                "该查询需要知识图谱支持，请：\n"
                "1. 启动 Neo4j 服务（docker-compose up neo4j -d）\n"
                "2. 或使用其他查询方式（如政策文档检索）"
            )

        try:
            # 使用图谱检索器查询
            top_k = kwargs.get("top_k", 5)

            if hasattr(self._graph_retriever, 'retrieve'):
                documents = self._graph_retriever.retrieve(query, top_k=top_k)
            elif hasattr(self._graph_retriever, 'invoke'):
                documents = self._graph_retriever.invoke(query)
            elif hasattr(self._graph_retriever, 'get_relevant_documents'):
                documents = self._graph_retriever.get_relevant_documents(query)
            else:
                raise AttributeError("图谱检索器不支持标准检索方法")

            if not documents:
                return f"未找到与 '{query}' 相关的图谱信息。"

            # 格式化查询结果
            result_parts = []
            for i, doc in enumerate(documents, 1):
                content = doc.page_content.strip()

                # 提取元数据
                metadata = doc.metadata
                source_type = metadata.get("source_type", "unknown")

                if source_type == "cypher":
                    # Cypher 查询结果
                    cypher = metadata.get("cypher", "")
                    result_parts.append(
                        f"[{i}] {content}\n"
                        f"查询: {cypher[:100]}..."
                    )
                else:
                    # 普通文档结果
                    result_parts.append(f"[{i}] {content}")

            result = "\n\n".join(result_parts)

            logger.info(f"[QueryGraphTool] 检索到 {len(documents)} 个相关结果")
            return result

        except Exception as e:
            logger.error(f"[QueryGraphTool] 图谱查询失败: {e}", exc_info=True)

            # 友好的错误提示
            if "Neo4j" in str(e) or "connection" in str(e).lower():
                return (
                    f"图谱查询失败（Neo4j 连接错误）。\n"
                    f"请确认 Neo4j 服务运行正常。\n"
                    f"错误详情: {str(e)[:200]}"
                )
            else:
                return f"图谱查询执行失败: {str(e)[:200]}"

    def close(self):
        """关闭图谱连接"""
        if self._graph_retriever:
            try:
                self._graph_retriever.close()
                logger.info("[QueryGraphTool] 图谱连接已关闭")
            except Exception as e:
                logger.warning(f"[QueryGraphTool] 关闭图谱连接失败: {e}")


# 创建全局单例（延迟初始化）
_graph_tool_instance: Optional[QueryGraphTool] = None


def get_query_graph_tool(graph_retriever=None) -> QueryGraphTool:
    """
    获取图谱查询工具单例

    Args:
        graph_retriever: 可选的图谱检索器实例

    Returns:
        QueryGraphTool 实例
    """
    global _graph_tool_instance

    if _graph_tool_instance is None:
        _graph_tool_instance = QueryGraphTool(graph_retriever=graph_retriever)

    return _graph_tool_instance
