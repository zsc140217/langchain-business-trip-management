"""
智能路由检索器 - Intelligent Retriever with Graph Support

根据查询类型自动路由到最合适的检索策略：
- GRAPH: 使用 GraphRetriever（实体关系、多跳推理）
- FACTUAL: 使用 FusionRetriever（向量 + BM25 + 可选图谱）
- CHITCHAT: 跳过检索，直接返回空列表

架构：
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ QueryClassifier │ ← 判断查询类型
└──────┬──────────┘
       │
   ┌───┴────┬─────────┐
   │        │         │
   ▼        ▼         ▼
 GRAPH   FACTUAL   CHITCHAT
   │        │         │
   ▼        ▼         ▼
GraphR  FusionR    Empty []
"""
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from src.rag.query_classifier import QueryClassifier
from src.rag.graph_retriever import GraphRetriever
from src.rag.fusion_retriever import FusionRetriever
import logging

logger = logging.getLogger(__name__)


class IntelligentRetriever:
    """
    智能路由检索器

    根据查询类型自动选择最佳检索策略：
    - GRAPH 查询 → GraphRetriever（知识图谱检索）
    - FACTUAL 查询 → FusionRetriever（向量 + BM25 融合）
    - CHITCHAT 查询 → 跳过检索（返回空列表）
    """

    def __init__(
        self,
        vector_retriever,
        bm25_retriever=None,
        graph_retriever: Optional[GraphRetriever] = None,
        classifier: Optional[QueryClassifier] = None,
        fusion_weights: Optional[List[float]] = None,
        enable_graph: bool = True
    ):
        """
        初始化智能路由检索器

        Args:
            vector_retriever: 向量检索器（FAISS/Chroma）
            bm25_retriever: BM25 检索器（可选）
            graph_retriever: 图谱检索器（可选）
            classifier: 查询分类器（可选，默认创建）
            fusion_weights: 融合权重 [vector, bm25, graph]（默认 [1.0, 1.0, 0.5]）
            enable_graph: 是否启用图谱检索（默认 True）
        """
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.graph_retriever = graph_retriever
        self.classifier = classifier if classifier else QueryClassifier()
        self.enable_graph = enable_graph and graph_retriever is not None

        # 设置融合权重
        self.fusion_weights = fusion_weights or [1.0, 1.0, 0.5]

        # 创建 FusionRetriever（用于 FACTUAL 查询）
        retrievers = [vector_retriever]
        weights = [self.fusion_weights[0]]

        if bm25_retriever:
            retrievers.append(bm25_retriever)
            weights.append(self.fusion_weights[1])

        self.fusion_retriever = FusionRetriever(
            retrievers=retrievers,
            weights=weights,
            k=60
        )

        # 统计信息
        self.stats = {
            'total_queries': 0,
            'graph_queries': 0,
            'factual_queries': 0,
            'chitchat_queries': 0
        }

    def get_relevant_documents(self, query: str, top_k: int = 5) -> List[Document]:
        """
        检索相关文档（智能路由）

        Args:
            query: 用户查询
            top_k: 返回文档数量

        Returns:
            相关文档列表
        """
        # 统计
        self.stats['total_queries'] += 1

        # Step 1: 分类查询
        classification = self.classifier.classify(query)
        query_type = classification['type']
        confidence = classification['confidence']

        logger.info(f"[IntelligentRetriever] 查询分类: {query_type} (置信度: {confidence:.2f})")
        logger.info(f"[IntelligentRetriever] 分类原因: {classification['reason']}")

        # Step 2: 根据类型路由
        if query_type == "GRAPH" and self.enable_graph:
            # 图谱检索
            self.stats['graph_queries'] += 1
            logger.info("[IntelligentRetriever] 使用 GraphRetriever")
            return self._graph_retrieve(query, top_k)

        elif query_type == "FACTUAL":
            # 融合检索（向量 + BM25）
            self.stats['factual_queries'] += 1
            logger.info("[IntelligentRetriever] 使用 FusionRetriever")
            return self._fusion_retrieve(query, top_k)

        elif query_type == "CHITCHAT":
            # 跳过检索
            self.stats['chitchat_queries'] += 1
            logger.info("[IntelligentRetriever] CHITCHAT 查询，跳过检索")
            return []

        else:
            # 默认使用融合检索
            logger.warning(f"[IntelligentRetriever] 未知查询类型: {query_type}，使用融合检索")
            return self._fusion_retrieve(query, top_k)

    def _graph_retrieve(self, query: str, top_k: int) -> List[Document]:
        """
        图谱检索

        Args:
            query: 用户查询
            top_k: 返回文档数量

        Returns:
            相关文档列表
        """
        try:
            documents = self.graph_retriever.retrieve(query, top_k=top_k)

            if documents:
                logger.info(f"[GraphRetriever] 成功检索到 {len(documents)} 个文档")
                return documents
            else:
                # 降级到融合检索
                logger.warning("[GraphRetriever] 未找到结果，降级到融合检索")
                return self._fusion_retrieve(query, top_k)

        except Exception as e:
            logger.error(f"[GraphRetriever] 检索失败: {e}，降级到融合检索")
            return self._fusion_retrieve(query, top_k)

    def _fusion_retrieve(self, query: str, top_k: int) -> List[Document]:
        """
        融合检索（向量 + BM25）

        Args:
            query: 用户查询
            top_k: 返回文档数量

        Returns:
            相关文档列表
        """
        try:
            documents = self.fusion_retriever.retrieve(query, top_k=top_k)
            logger.info(f"[FusionRetriever] 检索到 {len(documents)} 个文档")
            return documents

        except Exception as e:
            logger.error(f"[FusionRetriever] 检索失败: {e}，降级到向量检索")
            return self._vector_retrieve(query, top_k)

    def _vector_retrieve(self, query: str, top_k: int) -> List[Document]:
        """
        向量检索（最后的降级方案）

        Args:
            query: 用户查询
            top_k: 返回文档数量

        Returns:
            相关文档列表
        """
        try:
            documents = self.vector_retriever.get_relevant_documents(query)[:top_k]
            logger.info(f"[VectorRetriever] 检索到 {len(documents)} 个文档")
            return documents

        except Exception as e:
            logger.error(f"[VectorRetriever] 检索失败: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        total = self.stats['total_queries']
        if total == 0:
            return self.stats

        return {
            **self.stats,
            'graph_rate': self.stats['graph_queries'] / total,
            'factual_rate': self.stats['factual_queries'] / total,
            'chitchat_rate': self.stats['chitchat_queries'] / total
        }

    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            'total_queries': 0,
            'graph_queries': 0,
            'factual_queries': 0,
            'chitchat_queries': 0
        }


# 使用示例
if __name__ == "__main__":
    """测试智能路由检索器"""
    print("测试智能路由检索器...\n")

    try:
        from src.rag.retriever import create_vectorstore, get_retriever
        from src.rag.loader import load_documents_from_text
        from src.rag.hybrid_retriever import ChineseBM25Retriever

        # 1. 准备测试文档
        test_text = """
        企业差旅管理规章

        第一章 住宿标准
        1. 副总级别：一线城市不超过800元/晚，二线城市不超过600元/晚
        2. 总监级别：一线城市不超过600元/晚，二线城市不超过500元/晚
        3. 经理级别：一线城市不超过500元/晚，二线城市不超过400元/晚

        第二章 组织架构
        1. 副总向CEO汇报
        2. 总监向副总汇报
        3. 经理向总监汇报

        第三章 办公室分布
        公司在北京、上海、广州、深圳、杭州设有办公室
        """

        docs = load_documents_from_text(test_text, chunk_size=200)

        # 2. 创建检索器
        vectorstore = create_vectorstore(docs)
        vector_retriever = get_retriever(vectorstore, k=5)
        bm25_retriever = ChineseBM25Retriever.from_documents(docs)

        # 3. 创建智能检索器（暂不启用图谱）
        intelligent_retriever = IntelligentRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            graph_retriever=None,  # 暂不启用
            enable_graph=False
        )

        # 4. 测试查询
        test_queries = [
            "你好",  # CHITCHAT
            "副总的住宿标准是多少",  # FACTUAL
            "副总和总监的汇报关系",  # GRAPH（会降级到 FACTUAL）
            "公司在哪些城市有办公室"  # GRAPH（会降级到 FACTUAL）
        ]

        for query in test_queries:
            print("\n" + "=" * 60)
            print(f"查询: {query}")
            print("=" * 60)

            documents = intelligent_retriever.get_relevant_documents(query, top_k=3)

            if documents:
                print(f"\n检索到 {len(documents)} 个文档：")
                for i, doc in enumerate(documents, 1):
                    print(f"\n文档 {i}:")
                    print(doc.page_content[:150])
            else:
                print("\n跳过检索（CHITCHAT 查询）")

        # 5. 打印统计信息
        print("\n" + "=" * 60)
        print("统计信息:")
        print("=" * 60)
        stats = intelligent_retriever.get_statistics()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2%}")
            else:
                print(f"{key}: {value}")

        print("\n✅ 测试完成！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
