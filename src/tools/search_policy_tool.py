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

    def __init__(self, retriever=None, **kwargs):
        """
        初始化政策检索工具

        Args:
            retriever: 检索器实例（FusionRetriever 或其他）
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        # 使用私有属性避免 Pydantic 验证
        self._retriever = retriever
        self._initialized = False

    def _lazy_init(self):
        """延迟初始化检索器（避免循环依赖）"""
        if self._initialized:
            return

        if self._retriever is None:
            logger.info("[SearchPolicyTool] 延迟初始化检索器")
            try:
                from src.rag.fusion_retriever import FusionRetriever
                from src.rag.loader import load_documents
                from src.rag.retriever import create_vectorstore, get_retriever
                from pathlib import Path

                # 加载知识库文档
                kb_path = Path("data/knowledge_base")
                if kb_path.exists():
                    documents = load_documents(str(kb_path))
                    logger.info(f"[SearchPolicyTool] 加载文档: {len(documents)}个")

                    # 创建向量检索器（暂时只用向量，保证能跑通）
                    vectorstore = create_vectorstore(documents, embedding_type="cloud")
                    self._retriever = get_retriever(vectorstore, k=5)

                    logger.info("[SearchPolicyTool] 检索器初始化完成（Vector-only）")
                else:
                    logger.warning(f"[SearchPolicyTool] 知识库路径不存在: {kb_path}")
                    raise FileNotFoundError(f"知识库路径不存在: {kb_path}")

            except Exception as e:
                logger.error(f"[SearchPolicyTool] 检索器初始化失败: {e}")
                raise RuntimeError(f"检索器初始化失败: {e}")

        self._initialized = True

    def _run(self, query: str, **kwargs) -> str:
        """
        执行政策检索

        Args:
            query: 查询问题
            **kwargs: 其他参数（如 top_k）

        Returns:
            检索结果文本
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

            # 格式化检索结果
            result_parts = []
            for i, doc in enumerate(documents, 1):
                content = doc.page_content.strip()
                source = doc.metadata.get("source", "未知来源")
                result_parts.append(f"[{i}] {content}\n来源: {source}")

            result = "\n\n".join(result_parts)

            logger.info(f"[SearchPolicyTool] 检索到 {len(documents)} 个相关文档")
            return result

        except Exception as e:
            logger.error(f"[SearchPolicyTool] 检索失败: {e}")
            raise RuntimeError(f"政策检索失败: {e}")


# 创建全局单例（延迟初始化）
_policy_tool_instance: Optional[SearchPolicyTool] = None


def get_search_policy_tool(retriever=None) -> SearchPolicyTool:
    """
    获取政策检索工具单例

    Args:
        retriever: 可选的检索器实例

    Returns:
        SearchPolicyTool 实例
    """
    global _policy_tool_instance

    if _policy_tool_instance is None:
        _policy_tool_instance = SearchPolicyTool(retriever=retriever)

    return _policy_tool_instance
