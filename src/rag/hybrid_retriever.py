"""
混合检索器
三路召回（BM25 + Dense原始 + Dense改写）+ RRF融合 + 重排序

对应Spring AI的：
src/main/java/com/jblmj/aiagent/rag/EnterpriseHybridRetriever.java
"""
from langchain.retrievers import BM25Retriever
from langchain.schema import Document
from langchain_community.embeddings import DashScopeEmbeddings
from typing import List, Dict
import jieba
import os


class ChineseBM25Retriever(BM25Retriever):
    """
    支持中文分词的BM25检索器

    问题：LangChain的BM25Retriever默认使用英文分词
    解决：使用jieba进行中文分词

    BM25原理：
    - 基于词频和逆文档频率的稀疏检索
    - 精确关键词匹配
    - 适合处理专业术语和精确查询
    """

    @classmethod
    def from_documents(cls, documents: List[Document], **kwargs):
        """
        从文档创建BM25检索器

        Args:
            documents: 文档列表
            **kwargs: 其他参数

        Returns:
            BM25检索器实例
        """
        # 使用jieba分词
        texts = [doc.page_content for doc in documents]

        # 创建检索器
        retriever = cls.from_texts(
            texts=[" ".join(jieba.cut(text)) for text in texts],
            metadatas=[doc.metadata for doc in documents],
            **kwargs
        )

        return retriever


class EnterpriseHybridRetriever:
    """
    企业级混合检索器

    核心功能：
    1. 三路召回：BM25 + Dense原始 + Dense改写
    2. RRF融合：加权倒数排名融合
    3. 重排序：Cross-Encoder重新打分（可选）

    设计思路：
    - BM25：精确关键词匹配（适合专业术语）
    - Dense原始：语义理解（适合口语化查询）
    - Dense改写：标准化查询（提升召回率）
    - RRF融合：综合三路结果，平衡精确性和召回率

    性能数据（Spring AI项目）：
    - 单路BM25：准确率50%
    - 单路Dense：准确率60%
    - 三路召回+重排：准确率80%
    """

    def __init__(
        self,
        vector_store,
        documents: List[Document],
        query_rewriter=None,
        reranker=None
    ):
        """
        初始化混合检索器

        Args:
            vector_store: 向量存储（FAISS/Chroma）
            documents: 文档列表（用于创建BM25索引）
            query_rewriter: 查询改写器（可选）
            reranker: 重排序器（可选）
        """
        self.vector_store = vector_store
        self.bm25_retriever = ChineseBM25Retriever.from_documents(documents)
        self.query_rewriter = query_rewriter
        self.reranker = reranker

        # RRF参数
        self.RRF_K = 60  # 平滑因子
        self.BM25_WEIGHT = 1.0
        self.DENSE_ORIGINAL_WEIGHT = 1.0
        self.DENSE_REWRITTEN_WEIGHT = 1.0

    def retrieve(self, original_query: str, top_k: int = 5) -> List[Document]:
        """
        三路召回 + RRF融合 + 重排序

        流程：
        1. 查询改写（可选）
        2. 三路召回（并行）
        3. RRF融合
        4. 重排序（可选）

        Args:
            original_query: 原始查询
            top_k: 返回文档数量

        Returns:
            检索到的文档列表
        """
        print(f"\n{'='*60}")
        print(f"混合检索开始")
        print(f"原始查询：{original_query}")
        print(f"{'='*60}")

        # Step 1: 查询改写
        rewritten_query = original_query
        if self.query_rewriter:
            rewritten_query = self.query_rewriter.rewrite(original_query)
            print(f"改写后：{rewritten_query}")

        # Step 2: 三路召回
        retrieve_size = top_k * 10  # 召回10倍数量用于重排

        print(f"\n【三路召回】召回{retrieve_size}个候选文档")

        # 路径1：BM25检索（稀疏检索）
        bm25_results = self.bm25_retriever.get_relevant_documents(original_query)[:retrieve_size]
        print(f"  BM25召回：{len(bm25_results)}个")

        # 路径2：Dense检索-原始查询（稠密检索）
        dense_original_results = self.vector_store.similarity_search(
            original_query,
            k=min(retrieve_size, 10)  # FAISS限制
        )
        print(f"  Dense-Original召回：{len(dense_original_results)}个")

        # 路径3：Dense检索-改写查询（稠密检索）
        dense_rewritten_results = []
        if rewritten_query != original_query:
            dense_rewritten_results = self.vector_store.similarity_search(
                rewritten_query,
                k=min(retrieve_size, 10)
            )
            print(f"  Dense-Rewritten召回：{len(dense_rewritten_results)}个")

        # Step 3: RRF融合
        print(f"\n【RRF融合】加权倒数排名融合")
        fused_results = self._fuse_with_weighted_rrf(
            bm25_results,
            dense_original_results,
            dense_rewritten_results,
            retrieve_size
        )

        # Step 4: 重排序（可选）
        if self.reranker:
            print(f"\n【重排序】Cross-Encoder重新打分")
            reranked_results = self.reranker.rerank(original_query, fused_results, top_k)
            print(f"{'='*60}\n")
            return reranked_results
        else:
            print(f"{'='*60}\n")
            return fused_results[:top_k]

    def _fuse_with_weighted_rrf(
        self,
        bm25_results: List[Document],
        dense_original_results: List[Document],
        dense_rewritten_results: List[Document],
        top_k: int
    ) -> List[Document]:
        """
        加权RRF融合

        RRF公式：
        score(doc) = Σ weight_i / (k + rank_i)

        其中：
        - weight_i: 第i路召回的权重
        - rank_i: 文档在第i路召回中的排名
        - k: 平滑因子（60）

        Args:
            bm25_results: BM25召回结果
            dense_original_results: Dense原始查询结果
            dense_rewritten_results: Dense改写查询结果
            top_k: 返回文档数量

        Returns:
            融合后的文档列表
        """
        score_map: Dict[str, Dict] = {}

        # 处理BM25结果
        for rank, doc in enumerate(bm25_results, start=1):
            doc_id = self._get_document_id(doc)
            if doc_id not in score_map:
                score_map[doc_id] = {
                    'doc': doc,
                    'score': 0.0,
                    'sources': []
                }

            contribution = self.BM25_WEIGHT / (self.RRF_K + rank)
            score_map[doc_id]['score'] += contribution
            score_map[doc_id]['sources'].append(f"BM25:rank{rank}({contribution:.4f})")

        # 处理Dense-Original结果
        for rank, doc in enumerate(dense_original_results, start=1):
            doc_id = self._get_document_id(doc)
            if doc_id not in score_map:
                score_map[doc_id] = {
                    'doc': doc,
                    'score': 0.0,
                    'sources': []
                }

            contribution = self.DENSE_ORIGINAL_WEIGHT / (self.RRF_K + rank)
            score_map[doc_id]['score'] += contribution
            score_map[doc_id]['sources'].append(f"Dense-Original:rank{rank}({contribution:.4f})")

        # 处理Dense-Rewritten结果
        for rank, doc in enumerate(dense_rewritten_results, start=1):
            doc_id = self._get_document_id(doc)
            if doc_id not in score_map:
                score_map[doc_id] = {
                    'doc': doc,
                    'score': 0.0,
                    'sources': []
                }

            contribution = self.DENSE_REWRITTEN_WEIGHT / (self.RRF_K + rank)
            score_map[doc_id]['score'] += contribution
            score_map[doc_id]['sources'].append(f"Dense-Rewritten:rank{rank}({contribution:.4f})")

        # 按RRF分数排序
        sorted_items = sorted(
            score_map.values(),
            key=lambda x: x['score'],
            reverse=True
        )

        # 打印融合详情（Top-5）
        print(f"  融合结果（Top-5）：")
        for i, item in enumerate(sorted_items[:5], 1):
            preview = item['doc'].page_content[:50].replace('\n', ' ')
            sources = ', '.join(item['sources'])
            print(f"    {i}. [分数:{item['score']:.4f}] {preview}...")
            print(f"       来源: {sources}")

        return [item['doc'] for item in sorted_items[:top_k]]

    def _get_document_id(self, doc: Document) -> str:
        """
        获取文档唯一标识

        Args:
            doc: 文档

        Returns:
            文档ID
        """
        if hasattr(doc, 'metadata') and 'id' in doc.metadata:
            return doc.metadata['id']
        # 使用内容哈希作为ID
        return str(hash(doc.page_content))


class EnterpriseQueryRewriter:
    """
    企业级查询重写器

    功能：
    - 口语化 → 标准化
    - 保留否定词
    - 补充关键信息

    Few-shot示例：
    1. "去魔都出差住宿能报多少" → "上海一类城市出差住宿费用报销标准"
    2. "北京出差不能住五星级酒店吗" → "北京出差住宿标准 不能住五星级酒店"
    """

    def __init__(self, llm):
        self.llm = llm
        self.negation_keywords = ["不能", "不可以", "不是", "没有", "不要", "禁止"]

        # Few-shot示例
        self.few_shot_examples = """
示例1：口语化 → 标准化
原始："去魔都出差住宿能报多少"
改写："上海一类城市出差住宿费用报销标准"

示例2：否定疑问 → 保留否定词
原始："北京出差不能住五星级酒店吗"
改写："北京出差住宿标准 不能住五星级酒店"

示例3：多意图 → 拆分关键词
原始："去杭州拜访客户，住宿标准和客户地址"
改写："杭州出差住宿标准 杭州客户信息地址"
"""

    def rewrite(self, original_query: str) -> str:
        """
        执行查询重写

        Args:
            original_query: 原始查询

        Returns:
            改写后的查询
        """
        # 1. 检测否定查询
        if self._is_negation_query(original_query):
            return self._handle_negation_query(original_query)

        # 2. 构建改写Prompt
        prompt = f"""你是企业差旅政策查询系统的查询重写专家。
将用户的口语化查询改写为更适合向量检索的标准化表达。

{self.few_shot_examples}

【改写规则】
1. 替换口语词为标准术语（魔都→上海）
2. 补充关键信息（城市分类、费用类型）
3. 保留原始语义
4. 保留否定词、数值、时间
5. 改写后应该是陈述句

【用户查询】
{original_query}

改写后的查询："""

        try:
            # 3. 调用LLM改写（Temperature=0.1，稳定性优先）
            rewritten_query = self.llm.predict(prompt, temperature=0.1)

            # 4. 清理结果
            rewritten_query = self._clean_result(rewritten_query)

            # 5. 验证质量
            if self._is_valid_rewrite(original_query, rewritten_query):
                return rewritten_query
            else:
                return original_query

        except Exception as e:
            print(f"查询重写失败：{e}")
            return original_query

    def _is_negation_query(self, query: str) -> bool:
        """检测是否为否定查询"""
        return any(keyword in query for keyword in self.negation_keywords)

    def _handle_negation_query(self, query: str) -> str:
        """处理否定查询，保留否定词"""
        for keyword in self.negation_keywords:
            if keyword in query:
                parts = query.split(keyword)
                if len(parts) >= 2:
                    before = parts[0].strip()
                    after = parts[1].replace("吗", "").replace("？", "").strip()
                    return f"{before} {keyword} {after}"
        return query

    def _clean_result(self, rewritten: str) -> str:
        """清理改写结果"""
        rewritten = rewritten.replace("改写后的查询：", "")
        rewritten = rewritten.replace("改写：", "")
        rewritten = rewritten.strip('"\'')
        return rewritten.strip()

    def _is_valid_rewrite(self, original: str, rewritten: str) -> bool:
        """验证改写质量"""
        if not rewritten or len(rewritten) < 5 or len(rewritten) > 100:
            return False
        return True


# 测试代码
if __name__ == "__main__":
    """
    测试混合检索器
    """
    print("测试混合检索器...\n")

    from src.models.llm import get_llm
    from src.rag.loader import load_documents
    from src.rag.retriever import create_vectorstore

    try:
        # 1. 初始化LLM
        llm = get_llm(temperature=0.1)

        # 2. 加载文档
        print("加载文档...")
        documents = load_documents("data/travel_policy.txt")

        # 3. 创建向量存储
        print("创建向量存储...")
        vectorstore = create_vectorstore(documents)

        # 4. 创建查询改写器
        query_rewriter = EnterpriseQueryRewriter(llm)

        # 5. 创建混合检索器
        hybrid_retriever = EnterpriseHybridRetriever(
            vector_store=vectorstore,
            documents=documents,
            query_rewriter=query_rewriter
        )

        # 6. 测试查询
        test_queries = [
            "去上海出差住宿能报多少",
            "北京出差不能住五星级酒店吗",
            "出差期间的伙食补助标准"
        ]

        for query in test_queries:
            results = hybrid_retriever.retrieve(query, top_k=3)

            print(f"\n最终返回Top-3文档：")
            for i, doc in enumerate(results, 1):
                preview = doc.page_content[:100].replace('\n', ' ')
                print(f"  {i}. {preview}...")

            print(f"\n{'-'*60}\n")

        print("✅ 混合检索器测试完成！")

    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
