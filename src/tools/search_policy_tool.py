# -*- coding: utf-8 -*-
"""
政策检索工具 - 封装 RAG 检索能力

使用 FusionRetriever 进行多路召回检索
"""
from src.tools.base_tool import BaseTool
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SearchPolicyTool(BaseTool):
    """
    政策检索工具

    使用融合检索（Vector + BM25）查询企业差旅政策
    """

    name: str = "search_policy"
    description: str = """查询企业差旅政策和规章制度。

适用场景：
- 查询住宿标准（如"北京住宿标准"）
- 查询报销额度（如"伙食补助标准"）
- 查询流程规定（如"如何申请出差"）
- 查询政策定义（如"差旅费包括哪些"）

输入参数：
- query: 查询问题（字符串）

返回：相关政策内容的文本描述
"""

    cache_enabled: bool = True
    cache_ttl_seconds: int = 600  # 政策内容变化较少，缓存10分钟

    def __init__(self, retriever=None, llm=None, **kwargs):
        """
        初始化政策检索工具

        Args:
            retriever: 检索器实例（FusionRetriever 或其他）
            llm: 语言模型实例（用于总结检索结果）
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        # 使用私有属性避免 Pydantic 验证
        self._retriever = retriever
        self._llm = llm
        self._initialized = False

    def _lazy_init(self):
        """延迟初始化检索器和LLM（避免循环依赖）"""
        if self._initialized:
            return

        # 使用全局缓存的检索器（避免重复初始化）
        global _cached_retriever, _cached_llm

        if self._retriever is None:
            if _cached_retriever is not None:
                logger.info("[SearchPolicyTool] 使用缓存的检索器")
                self._retriever = _cached_retriever
            else:
                logger.info("[SearchPolicyTool] 首次初始化检索器")
                try:
                    from src.rag.retriever import load_vectorstore, get_retriever
                    from pathlib import Path
                    import time

                    init_start = time.time()

                    # 优先加载持久化的向量库（避免重新创建，节省30秒）
                    vectorstore_path = Path("src/data/vectorstore")
                    if vectorstore_path.exists():
                        logger.info(f"[SearchPolicyTool] 加载持久化向量库: {vectorstore_path}")
                        vectorstore = load_vectorstore(str(vectorstore_path))
                        self._retriever = get_retriever(vectorstore, k=5)
                        _cached_retriever = self._retriever

                        init_elapsed = time.time() - init_start
                        logger.info(f"[SearchPolicyTool] 检索器初始化完成，耗时 {init_elapsed:.2f}s")
                    else:
                        # 降级：如果向量库不存在，从原始文档创建（仅开发环境）
                        logger.warning(f"[SearchPolicyTool] 向量库不存在: {vectorstore_path}，从文档创建")
                        from src.rag.loader import load_documents
                        from src.rag.retriever import create_vectorstore

                        kb_path = Path("data/knowledge_base")
                        if kb_path.exists():
                            documents = load_documents(str(kb_path))
                            logger.info(f"[SearchPolicyTool] 加载文档: {len(documents)}个")
                            vectorstore = create_vectorstore(documents, embedding_type="cloud")
                            self._retriever = get_retriever(vectorstore, k=5)
                            _cached_retriever = self._retriever

                            init_elapsed = time.time() - init_start
                            logger.info(f"[SearchPolicyTool] 检索器初始化完成（从文档创建），耗时 {init_elapsed:.2f}s")
                        else:
                            raise FileNotFoundError(f"知识库路径不存在: {kb_path}")

                except Exception as e:
                    logger.error(f"[SearchPolicyTool] 检索器初始化失败: {e}")
                    raise RuntimeError(f"检索器初始化失败: {e}")

        # 初始化 LLM（如果未提供）
        if self._llm is None:
            if _cached_llm is not None:
                logger.info("[SearchPolicyTool] 使用缓存的 LLM")
                self._llm = _cached_llm
            else:
                logger.info("[SearchPolicyTool] 首次初始化 LLM")
                try:
                    from src.models.llm import get_llm
                    self._llm = get_llm()
                    _cached_llm = self._llm
                    logger.info("[SearchPolicyTool] LLM 初始化完成")
                except Exception as e:
                    logger.error(f"[SearchPolicyTool] LLM 初始化失败: {e}")
                    raise RuntimeError(f"LLM 初始化失败: {e}")

        self._initialized = True

    def _run(self, query: str, **kwargs) -> str:
        """
        执行政策检索

        Args:
            query: 查询问题
            **kwargs: 其他参数（如 top_k）

        Returns:
            LLM总结后的回答
        """
        # 延迟初始化
        self._lazy_init()

        if not query or not query.strip():
            raise ValueError("查询不能为空")

        logger.info(f"[SearchPolicyTool] 查询: {query}")

        try:
            # 使用检索器查询（支持 invoke 和 get_relevant_documents）
            top_k = kwargs.get("top_k", 5)

            if hasattr(self._retriever, 'invoke'):
                documents = self._retriever.invoke(query)
            elif hasattr(self._retriever, 'get_relevant_documents'):
                documents = self._retriever.get_relevant_documents(query)
            else:
                raise AttributeError("检索器不支持 invoke 或 get_relevant_documents 方法")

            if not documents:
                return f"未找到与 '{query}' 相关的政策信息。"

            logger.info(f"[SearchPolicyTool] 检索到 {len(documents)} 个相关文档")

            # 拼接检索结果作为上下文
            context_parts = []
            for i, doc in enumerate(documents, 1):
                content = doc.page_content.strip()
                source = doc.metadata.get("source", "未知来源")
                context_parts.append(f"[文档{i}]\n{content}\n来源: {source}")

            context = "\n\n".join(context_parts)

            # 使用 LLM 总结检索结果
            prompt = f"""请根据以下检索到的政策文档，回答用户的问题。

用户问题：{query}

检索到的政策文档：
{context}

要求：
1. 直接回答用户问题，提取关键信息
2. 如果文档中有具体数字或标准，请明确列出
3. 保持回答简洁清晰
4. 如果文档中没有直接答案，说明最相关的信息

回答："""

            logger.info("[SearchPolicyTool] 调用 LLM 生成回答")

            # 调用 LLM
            from langchain_core.messages import HumanMessage
            response = self._llm.invoke([HumanMessage(content=prompt)])

            # 提取回答内容
            if hasattr(response, 'content'):
                answer = response.content
            else:
                answer = str(response)

            logger.info(f"[SearchPolicyTool] LLM 回答长度: {len(answer)} 字符")
            return answer

        except Exception as e:
            logger.error(f"[SearchPolicyTool] 检索失败: {e}", exc_info=True)
            raise RuntimeError(f"政策检索失败: {e}")


# 创建全局单例（延迟初始化）
_policy_tool_instance: Optional[SearchPolicyTool] = None

# 全局缓存（避免重复初始化检索器和LLM）
_cached_retriever = None
_cached_llm = None


def get_search_policy_tool(retriever=None, llm=None) -> SearchPolicyTool:
    """
    获取政策检索工具单例

    Args:
        retriever: 可选的检索器实例
        llm: 可选的语言模型实例

    Returns:
        SearchPolicyTool 实例
    """
    global _policy_tool_instance

    if _policy_tool_instance is None:
        _policy_tool_instance = SearchPolicyTool(retriever=retriever, llm=llm)

    return _policy_tool_instance
