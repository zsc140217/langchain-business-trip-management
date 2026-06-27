"""
融合检索器 - Fusion Retrieval

整合多路检索方式，通过RRF算法融合结果：
1. 向量检索（FAISS）
2. BM25关键词检索
3. 图谱检索（可选）

核心算法：加权RRF（Reciprocal Rank Fusion）
score(doc) = w1/(k+rank_vector) + w2/(k+rank_bm25) + w3/(k+rank_graph)

优势：
- 多路召回提升覆盖率
- RRF融合平衡不同检索方式
- 去重保证结果质量
- 来源追踪方便调试
"""
from langchain_core.documents import Document
from typing import List, Optional, Dict, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class RRFFusion:
    """
    RRF融合算法实现

    RRF（Reciprocal Rank Fusion）是一种无参数的融合算法，
    通过倒数排名来融合多个检索结果。

    公式：score(doc) = Σ weight_i / (k + rank_i)

    参数：
    - k: 平滑因子，避免分母为0，通常取60
    - weights: 各路检索的权重
    """

    def __init__(self, k: int = 60):
        """
        初始化RRF融合器

        Args:
            k: 平滑因子（默认60）
        """
        self.k = k

    def fuse(
        self,
        results_list: List[List[Document]],
        weights: List[float]
    ) -> List[Document]:
        """
        融合多路检索结果

        Args:
            results_list: 多路检索结果列表
            weights: 各路检索的权重

        Returns:
            融合后的文档列表（按分数降序）
        """
        if not results_list or all(len(results) == 0 for results in results_list):
            return []

        if len(results_list) != len(weights):
            raise ValueError(
                f"结果列表数量({len(results_list)})与权重数量({len(weights)})不匹配"
            )

        # 使用字典存储每个文档的融合信息
        doc_scores: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'doc': None,
            'score': 0.0,
            'sources': []
        })

        # 遍历每一路检索结果
        for retriever_idx, (results, weight) in enumerate(zip(results_list, weights)):
            for rank, doc in enumerate(results, start=1):
                # 获取文档唯一标识
                doc_id = self._get_document_id(doc)

                # 计算RRF贡献分数
                contribution = weight / (self.k + rank)

                # 累加分数
                if doc_scores[doc_id]['doc'] is None:
                    doc_scores[doc_id]['doc'] = doc

                doc_scores[doc_id]['score'] += contribution
                doc_scores[doc_id]['sources'].append({
                    'retriever': retriever_idx,
                    'rank': rank,
                    'contribution': contribution
                })

        # 按分数排序
        sorted_items = sorted(
            doc_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )

        # 构建结果文档，添加融合元数据
        fused_docs = []
        for item in sorted_items:
            doc = item['doc']

            # 添加融合元数据
            if not hasattr(doc, 'metadata'):
                doc.metadata = {}

            doc.metadata['fusion_score'] = item['score']
            doc.metadata['fusion_sources'] = item['sources']

            fused_docs.append(doc)

        return fused_docs

    def _get_document_id(self, doc: Document) -> str:
        """
        获取文档唯一标识

        优先使用metadata中的id，否则使用内容哈希

        Args:
            doc: 文档

        Returns:
            文档ID
        """
        if hasattr(doc, 'metadata') and 'id' in doc.metadata:
            return str(doc.metadata['id'])

        # 使用内容哈希作为ID
        return str(hash(doc.page_content))


class FusionRetriever:
    """
    融合检索器

    整合多个检索器（向量、BM25、图谱等），
    使用RRF算法融合结果。

    使用示例：
        # 创建融合检索器
        fusion_retriever = FusionRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            weights=[1.0, 1.0]
        )

        # 检索
        results = fusion_retriever.get_relevant_documents("上海住宿标准", k=5)
    """

    def __init__(
        self,
        retrievers: List[Any],
        weights: Optional[List[float]] = None,
        k: int = 60,
        ignore_errors: bool = False,
        max_docs_per_retriever: int = 100
    ):
        """
        初始化融合检索器

        Args:
            retrievers: 检索器列表
            weights: 权重列表（默认全为1.0）
            k: RRF平滑因子（默认60，基于TREC实验最佳实践）
            ignore_errors: 是否忽略单个检索器的错误
            max_docs_per_retriever: 每个检索器最多返回的文档数（防止内存溢出，默认100）
        """
        if not retrievers:
            raise ValueError("至少需要一个检索器")

        # 验证每个检索器有必需的方法
        for idx, retriever in enumerate(retrievers):
            if not (hasattr(retriever, 'invoke') or
                    hasattr(retriever, 'get_relevant_documents')):
                raise TypeError(
                    f"检索器{idx}必须实现invoke()或get_relevant_documents()方法"
                )

        self.retrievers = retrievers
        self.max_docs_per_retriever = max_docs_per_retriever
        self.weights = weights or [1.0] * len(retrievers)
        self.ignore_errors = ignore_errors

        if len(self.retrievers) != len(self.weights):
            raise ValueError(
                f"检索器数量({len(self.retrievers)})与权重数量({len(self.weights)})不匹配"
            )

        self.fusion = RRFFusion(k=k)

        logger.info(
            f"初始化融合检索器: {len(self.retrievers)}路检索, "
            f"权重={self.weights}, k={k}, max_docs={max_docs_per_retriever}"
        )

    def get_relevant_documents(
        self,
        query: str,
        k: int = 5
    ) -> List[Document]:
        """
        执行融合检索

        流程：
        1. 并行调用各路检索器
        2. RRF融合结果
        3. 返回Top-K

        Args:
            query: 查询文本
            k: 返回文档数量

        Returns:
            融合后的Top-K文档
        """
        logger.info(f"融合检索开始: query='{query}', k={k}")

        # Step 1: 多路召回
        results_list = []
        valid_weights = []

        for idx, (retriever, weight) in enumerate(zip(self.retrievers, self.weights)):
            try:
                # 调用检索器 - 支持新旧API
                if hasattr(retriever, 'invoke'):
                    results = retriever.invoke(query)
                elif hasattr(retriever, 'get_relevant_documents'):
                    results = retriever.get_relevant_documents(query)
                else:
                    raise AttributeError(f"检索器{idx}不支持invoke或get_relevant_documents方法")

                # 限制每个检索器返回的文档数量
                results = results[:self.max_docs_per_retriever]

                results_list.append(results)
                valid_weights.append(weight)

                logger.info(f"  检索器{idx}: 召回{len(results)}个文档")

            except Exception as e:
                logger.error(f"  检索器{idx}失败: {e}")

                if not self.ignore_errors:
                    raise

                # 忽略错误，使用空结果
                results_list.append([])
                valid_weights.append(weight)

        # Step 2: RRF融合
        if not results_list or all(len(r) == 0 for r in results_list):
            logger.warning("所有检索器都未返回结果")
            return []

        fused_docs = self.fusion.fuse(results_list, valid_weights)

        logger.info(f"融合后: {len(fused_docs)}个唯一文档")

        # Step 3: 返回Top-K
        top_k_docs = fused_docs[:k]

        # 打印融合详情（Top-3）
        if top_k_docs:
            logger.info("Top-3融合结果:")
            for i, doc in enumerate(top_k_docs[:3], 1):
                score = doc.metadata.get('fusion_score', 0.0)
                sources = doc.metadata.get('fusion_sources', [])
                preview = doc.page_content[:50].replace('\n', ' ')

                logger.info(f"  {i}. [分数:{score:.4f}] {preview}...")
                logger.info(f"     来源: {len(sources)}个检索器")

        return top_k_docs

    @classmethod
    def create_from_components(
        cls,
        vector_retriever: Any,
        bm25_retriever: Any,
        graph_retriever: Optional[Any] = None,
        vector_weight: float = 1.0,
        bm25_weight: float = 1.0,
        graph_weight: float = 0.8,
        k: int = 60
    ) -> "FusionRetriever":
        """
        从组件创建融合检索器（便捷方法）

        Args:
            vector_retriever: 向量检索器
            bm25_retriever: BM25检索器
            graph_retriever: 图谱检索器（可选）
            vector_weight: 向量权重
            bm25_weight: BM25权重
            graph_weight: 图谱权重
            k: RRF平滑因子

        Returns:
            融合检索器实例
        """
        retrievers = [vector_retriever, bm25_retriever]
        weights = [vector_weight, bm25_weight]

        if graph_retriever is not None:
            retrievers.append(graph_retriever)
            weights.append(graph_weight)

        return cls(
            retrievers=retrievers,
            weights=weights,
            k=k
        )


def create_fusion_retriever(
    vectorstore,
    documents: List[Document],
    graph_retriever: Optional[Any] = None,
    vector_weight: float = 1.0,
    bm25_weight: float = 1.0,
    graph_weight: float = 0.8,
    k_rrf: int = 60,
    k_retrieve: int = 10
) -> FusionRetriever:
    """
    创建融合检索器（工厂方法）

    自动创建向量检索器和BM25检索器，然后融合

    Args:
        vectorstore: 向量存储（FAISS/Chroma）
        documents: 文档列表（用于创建BM25索引）
        graph_retriever: 图谱检索器（可选）
        vector_weight: 向量权重
        bm25_weight: BM25权重
        graph_weight: 图谱权重
        k_rrf: RRF平滑因子
        k_retrieve: 每路检索数量

    Returns:
        融合检索器实例
    """
    from src.rag.retriever import get_retriever
    from src.rag.hybrid_retriever import ChineseBM25Retriever

    # 创建向量检索器
    vector_retriever = get_retriever(vectorstore, k=k_retrieve)

    # 创建BM25检索器
    bm25_retriever = ChineseBM25Retriever.from_documents(documents, k=k_retrieve)

    # 创建融合检索器
    fusion_retriever = FusionRetriever.create_from_components(
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever,
        graph_retriever=graph_retriever,
        vector_weight=vector_weight,
        bm25_weight=bm25_weight,
        graph_weight=graph_weight,
        k=k_rrf
    )

    logger.info("✅ 融合检索器创建成功")

    return fusion_retriever


# 测试代码
if __name__ == "__main__":
    """
    测试融合检索器
    """
    print("测试融合检索器...\n")

    from src.rag.loader import load_documents_from_text
    from src.rag.retriever import create_vectorstore

    # 准备测试文档
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

第三章 伙食补助
1. 国内出差：50元/天
2. 国际出差：100元/天
    """

    try:
        # 1. 加载文档
        print("📄 加载文档...")
        docs = load_documents_from_text(test_text, chunk_size=200)
        print(f"   文档数量: {len(docs)}")

        # 2. 创建融合检索器
        print("\n🔧 创建融合检索器...")
        vectorstore = create_vectorstore(docs)
        fusion_retriever = create_fusion_retriever(
            vectorstore=vectorstore,
            documents=docs,
            k_retrieve=5
        )

        # 3. 测试检索
        test_queries = [
            "上海出差住宿标准",
            "去北京出差能住多少钱的酒店",
            "出差伙食补助"
        ]

        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"查询: {query}")
            print(f"{'='*60}")

            results = fusion_retriever.get_relevant_documents(query, k=3)

            print(f"\n返回Top-3结果:")
            for i, doc in enumerate(results, 1):
                score = doc.metadata.get('fusion_score', 0.0)
                sources = doc.metadata.get('fusion_sources', [])
                preview = doc.page_content[:80].replace('\n', ' ')

                print(f"\n{i}. [分数: {score:.4f}]")
                print(f"   内容: {preview}...")
                print(f"   来源: {len(sources)}个检索器")

        print(f"\n{'='*60}")
        print("✅ 融合检索器测试成功！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
