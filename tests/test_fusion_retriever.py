"""
融合检索器测试

测试FusionRetriever的核心功能：
1. 基本融合检索
2. 向量+BM25融合
3. RRF分数计算
4. 融合后排序
5. Top-K结果
6. 来源标记
7. 边界情况（空结果、单一来源、去重）
"""
import pytest
from langchain_core.documents import Document
from unittest.mock import Mock, MagicMock
from src.rag.fusion_retriever import FusionRetriever, RRFFusion


class TestRRFFusion:
    """测试RRF融合算法"""

    def test_rrf_score_calculation(self):
        """测试RRF分数计算正确性"""
        fusion = RRFFusion(k=60)

        # 创建测试文档
        doc1 = Document(page_content="上海住宿标准500元", metadata={"id": "doc1"})
        doc2 = Document(page_content="北京住宿标准500元", metadata={"id": "doc2"})
        doc3 = Document(page_content="杭州住宿标准400元", metadata={"id": "doc3"})

        # 模拟两路检索结果
        # doc1在两路都排第1，应该得分最高
        # doc2只在第一路排第2
        # doc3只在第二路排第2
        results_list = [
            [doc1, doc2],  # 第一路：权重1.0
            [doc1, doc3]   # 第二路：权重1.0
        ]
        weights = [1.0, 1.0]

        fused = fusion.fuse(results_list, weights)

        # 验证：doc1应该排第一（两路都是rank1）
        assert fused[0].page_content == "上海住宿标准500元"

        # 验证RRF分数计算
        # doc1: 1.0/(60+1) + 1.0/(60+1) = 2/61 ≈ 0.0328
        # doc2: 1.0/(60+2) = 1/62 ≈ 0.0161
        # doc3: 1.0/(60+2) = 1/62 ≈ 0.0161
        doc1_score = fused[0].metadata.get('fusion_score')
        assert doc1_score is not None
        assert abs(doc1_score - 2/61) < 0.0001

    def test_rrf_weighted_fusion(self):
        """测试加权RRF融合"""
        fusion = RRFFusion(k=60)

        doc1 = Document(page_content="文档1", metadata={"id": "doc1"})
        doc2 = Document(page_content="文档2", metadata={"id": "doc2"})

        # 第一路权重更高
        results_list = [
            [doc1, doc2],  # 权重2.0
            [doc2, doc1]   # 权重1.0
        ]
        weights = [2.0, 1.0]

        fused = fusion.fuse(results_list, weights)

        # doc1: 2.0/(60+1) + 1.0/(60+2) ≈ 0.0328 + 0.0161 = 0.0489
        # doc2: 2.0/(60+2) + 1.0/(60+1) ≈ 0.0323 + 0.0164 = 0.0487
        # doc1应该略高
        assert fused[0].page_content == "文档1"

    def test_rrf_with_empty_results(self):
        """测试空结果处理"""
        fusion = RRFFusion(k=60)

        # 空列表
        fused = fusion.fuse([], [])
        assert fused == []

        # 所有路径都为空
        fused = fusion.fuse([[], []], [1.0, 1.0])
        assert fused == []

    def test_rrf_duplicate_removal(self):
        """测试文档去重"""
        fusion = RRFFusion(k=60)

        doc1 = Document(page_content="相同内容", metadata={"id": "doc1"})
        doc1_dup = Document(page_content="相同内容", metadata={"id": "doc1"})
        doc2 = Document(page_content="不同内容", metadata={"id": "doc2"})

        results_list = [
            [doc1, doc2],
            [doc1_dup, doc2]
        ]
        weights = [1.0, 1.0]

        fused = fusion.fuse(results_list, weights)

        # 应该只有2个文档（去重）
        assert len(fused) == 2

    def test_source_tracking(self):
        """测试来源标记"""
        fusion = RRFFusion(k=60)

        doc1 = Document(page_content="文档1", metadata={"id": "doc1"})

        results_list = [
            [doc1],  # 第一路
            [doc1]   # 第二路
        ]
        weights = [1.0, 1.0]

        fused = fusion.fuse(results_list, weights)

        # 验证来源信息
        sources = fused[0].metadata.get('fusion_sources')
        assert sources is not None
        assert len(sources) == 2  # 两个来源


class TestFusionRetriever:
    """测试融合检索器"""

    @pytest.fixture
    def mock_vector_retriever(self):
        """模拟向量检索器"""
        retriever = Mock()
        results = [
            Document(page_content="向量检索结果1", metadata={"id": "vec1"}),
            Document(page_content="向量检索结果2", metadata={"id": "vec2"})
        ]
        retriever.get_relevant_documents = Mock(return_value=results)
        retriever.invoke = Mock(return_value=results)
        return retriever

    @pytest.fixture
    def mock_bm25_retriever(self):
        """模拟BM25检索器"""
        retriever = Mock()
        results = [
            Document(page_content="BM25检索结果1", metadata={"id": "bm25_1"}),
            Document(page_content="向量检索结果1", metadata={"id": "vec1"})  # 重复文档
        ]
        retriever.get_relevant_documents = Mock(return_value=results)
        retriever.invoke = Mock(return_value=results)
        return retriever

    def test_fusion_retrieval_basic(self, mock_vector_retriever, mock_bm25_retriever):
        """测试基本融合检索"""
        fusion_retriever = FusionRetriever(
            retrievers=[mock_vector_retriever, mock_bm25_retriever],
            weights=[1.0, 1.0]
        )

        results = fusion_retriever.get_relevant_documents("测试查询", k=5)

        # 验证两个检索器都被调用（使用invoke而不是get_relevant_documents）
        mock_vector_retriever.invoke.assert_called_once()
        mock_bm25_retriever.invoke.assert_called_once()

        # 验证返回结果
        assert len(results) > 0
        assert len(results) <= 5

    def test_vector_bm25_fusion(self, mock_vector_retriever, mock_bm25_retriever):
        """测试向量+BM25融合"""
        fusion_retriever = FusionRetriever(
            retrievers=[mock_vector_retriever, mock_bm25_retriever],
            weights=[1.0, 1.0]
        )

        results = fusion_retriever.get_relevant_documents("上海住宿标准")

        # 验证融合后的文档包含融合元数据
        assert len(results) > 0
        assert 'fusion_score' in results[0].metadata
        assert 'fusion_sources' in results[0].metadata

    def test_fusion_ranking(self):
        """测试融合后排序正确"""
        # 创建模拟检索器
        retriever1 = Mock()
        results1 = [
            Document(page_content="高分文档", metadata={"id": "high"}),
            Document(page_content="低分文档", metadata={"id": "low"})
        ]
        retriever1.get_relevant_documents = Mock(return_value=results1)
        retriever1.invoke = Mock(return_value=results1)

        retriever2 = Mock()
        results2 = [
            Document(page_content="高分文档", metadata={"id": "high"}),
            Document(page_content="中分文档", metadata={"id": "mid"})
        ]
        retriever2.get_relevant_documents = Mock(return_value=results2)
        retriever2.invoke = Mock(return_value=results2)

        fusion_retriever = FusionRetriever(
            retrievers=[retriever1, retriever2],
            weights=[1.0, 1.0]
        )

        results = fusion_retriever.get_relevant_documents("查询")

        # "高分文档"在两个检索器都排第一，应该是融合后的第一名
        assert results[0].page_content == "高分文档"

        # 验证分数递减
        scores = [doc.metadata['fusion_score'] for doc in results]
        assert scores == sorted(scores, reverse=True)

    def test_top_k_results(self, mock_vector_retriever, mock_bm25_retriever):
        """测试返回正确数量的结果"""
        fusion_retriever = FusionRetriever(
            retrievers=[mock_vector_retriever, mock_bm25_retriever],
            weights=[1.0, 1.0]
        )

        # 请求Top-2
        results = fusion_retriever.get_relevant_documents("查询", k=2)
        assert len(results) <= 2

        # 请求Top-10（但总共只有3个不重复文档）
        results = fusion_retriever.get_relevant_documents("查询", k=10)
        assert len(results) <= 10

    def test_empty_results(self):
        """测试处理空结果"""
        retriever1 = Mock()
        retriever1.get_relevant_documents = Mock(return_value=[])
        retriever1.invoke = Mock(return_value=[])

        retriever2 = Mock()
        retriever2.get_relevant_documents = Mock(return_value=[])
        retriever2.invoke = Mock(return_value=[])

        fusion_retriever = FusionRetriever(
            retrievers=[retriever1, retriever2],
            weights=[1.0, 1.0]
        )

        results = fusion_retriever.get_relevant_documents("查询")
        assert results == []

    def test_single_source_results(self):
        """测试单一来源结果"""
        retriever1 = Mock()
        results1 = [Document(page_content="文档1", metadata={"id": "doc1"})]
        retriever1.get_relevant_documents = Mock(return_value=results1)
        retriever1.invoke = Mock(return_value=results1)

        retriever2 = Mock()
        retriever2.get_relevant_documents = Mock(return_value=[])
        retriever2.invoke = Mock(return_value=[])

        fusion_retriever = FusionRetriever(
            retrievers=[retriever1, retriever2],
            weights=[1.0, 1.0]
        )

        results = fusion_retriever.get_relevant_documents("查询")

        # 应该返回结果，即使只有一个检索器有结果
        assert len(results) == 1
        assert results[0].page_content == "文档1"

    def test_duplicate_documents(self):
        """测试去重处理"""
        # 同一文档在多个检索器中出现
        doc_shared = Document(page_content="共享文档", metadata={"id": "shared"})

        retriever1 = Mock()
        results1 = [
            doc_shared,
            Document(page_content="独有1", metadata={"id": "unique1"})
        ]
        retriever1.get_relevant_documents = Mock(return_value=results1)
        retriever1.invoke = Mock(return_value=results1)

        retriever2 = Mock()
        results2 = [
            doc_shared,
            Document(page_content="独有2", metadata={"id": "unique2"})
        ]
        retriever2.get_relevant_documents = Mock(return_value=results2)
        retriever2.invoke = Mock(return_value=results2)

        fusion_retriever = FusionRetriever(
            retrievers=[retriever1, retriever2],
            weights=[1.0, 1.0]
        )

        results = fusion_retriever.get_relevant_documents("查询")

        # 应该只有3个文档（去重后）
        assert len(results) == 3

        # 共享文档应该有更高的分数（因为在两个检索器都出现）
        assert results[0].page_content == "共享文档"

    def test_three_way_fusion(self):
        """测试三路融合（向量+BM25+图谱）"""
        retriever1 = Mock()
        results1 = [Document(page_content="文档1", metadata={"id": "doc1"})]
        retriever1.get_relevant_documents = Mock(return_value=results1)
        retriever1.invoke = Mock(return_value=results1)

        retriever2 = Mock()
        results2 = [Document(page_content="文档2", metadata={"id": "doc2"})]
        retriever2.get_relevant_documents = Mock(return_value=results2)
        retriever2.invoke = Mock(return_value=results2)

        retriever3 = Mock()
        results3 = [
            Document(page_content="文档1", metadata={"id": "doc1"}),
            Document(page_content="文档3", metadata={"id": "doc3"})
        ]
        retriever3.get_relevant_documents = Mock(return_value=results3)
        retriever3.invoke = Mock(return_value=results3)

        fusion_retriever = FusionRetriever(
            retrievers=[retriever1, retriever2, retriever3],
            weights=[1.0, 1.0, 0.8]  # 图谱权重较低
        )

        results = fusion_retriever.get_relevant_documents("查询")

        # 验证三个检索器都被调用（使用invoke）
        retriever1.invoke.assert_called_once()
        retriever2.invoke.assert_called_once()
        retriever3.invoke.assert_called_once()

        # 文档1在两个检索器出现，应该排第一
        assert results[0].page_content == "文档1"

    def test_custom_weights(self):
        """测试自定义权重"""
        doc1 = Document(page_content="文档1", metadata={"id": "doc1"})
        doc2 = Document(page_content="文档2", metadata={"id": "doc2"})

        retriever1 = Mock()
        retriever1.get_relevant_documents = Mock(return_value=[doc1])
        retriever1.invoke = Mock(return_value=[doc1])

        retriever2 = Mock()
        retriever2.get_relevant_documents = Mock(return_value=[doc2])
        retriever2.invoke = Mock(return_value=[doc2])

        # 第一个检索器权重更高
        fusion_retriever = FusionRetriever(
            retrievers=[retriever1, retriever2],
            weights=[2.0, 1.0]
        )

        results = fusion_retriever.get_relevant_documents("查询")

        # doc1应该因为权重更高而排在前面
        assert results[0].page_content == "文档1"

    def test_graph_retriever_optional(self):
        """测试图谱检索器可选"""
        retriever1 = Mock()
        results1 = [Document(page_content="文档1", metadata={"id": "doc1"})]
        retriever1.get_relevant_documents = Mock(return_value=results1)
        retriever1.invoke = Mock(return_value=results1)

        # 不传入第三个检索器
        fusion_retriever = FusionRetriever(
            retrievers=[retriever1],
            weights=[1.0]
        )

        results = fusion_retriever.get_relevant_documents("查询")

        # 应该正常工作
        assert len(results) == 1

    def test_error_handling(self):
        """测试错误处理"""
        retriever1 = Mock()
        retriever1.get_relevant_documents = Mock(side_effect=Exception("检索失败"))
        retriever1.invoke = Mock(side_effect=Exception("检索失败"))

        retriever2 = Mock()
        results2 = [Document(page_content="文档1", metadata={"id": "doc1"})]
        retriever2.get_relevant_documents = Mock(return_value=results2)
        retriever2.invoke = Mock(return_value=results2)

        fusion_retriever = FusionRetriever(
            retrievers=[retriever1, retriever2],
            weights=[1.0, 1.0],
            ignore_errors=True  # 忽略单个检索器的错误
        )

        results = fusion_retriever.get_relevant_documents("查询")

        # 应该返回第二个检索器的结果
        assert len(results) == 1
        assert results[0].page_content == "文档1"


class TestFusionRetrieverIntegration:
    """集成测试 - 使用真实组件"""

    @pytest.fixture
    def sample_documents(self):
        """样本文档"""
        return [
            Document(
                page_content="一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚",
                metadata={"id": "doc1", "source": "policy"}
            ),
            Document(
                page_content="二线城市（杭州、成都、武汉等）：标准间不超过400元/晚",
                metadata={"id": "doc2", "source": "policy"}
            ),
            Document(
                page_content="三线及以下城市：标准间不超过300元/晚",
                metadata={"id": "doc3", "source": "policy"}
            ),
            Document(
                page_content="市内交通：实报实销，需提供发票",
                metadata={"id": "doc4", "source": "policy"}
            ),
            Document(
                page_content="城际交通：距离<500公里高铁二等座，距离≥500公里飞机经济舱",
                metadata={"id": "doc5", "source": "policy"}
            )
        ]

    def test_create_from_components(self, sample_documents):
        """测试从组件创建融合检索器"""
        # 创建模拟检索器
        vector_retriever = Mock()
        results1 = sample_documents[:2]
        vector_retriever.get_relevant_documents = Mock(return_value=results1)
        vector_retriever.invoke = Mock(return_value=results1)

        bm25_retriever = Mock()
        results2 = sample_documents[1:3]
        bm25_retriever.get_relevant_documents = Mock(return_value=results2)
        bm25_retriever.invoke = Mock(return_value=results2)

        # 使用类方法创建
        fusion_retriever = FusionRetriever.create_from_components(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            vector_weight=1.5,
            bm25_weight=1.0,
            k=60
        )

        # 验证创建成功
        assert len(fusion_retriever.retrievers) == 2
        assert fusion_retriever.weights == [1.5, 1.0]

        # 测试检索
        results = fusion_retriever.get_relevant_documents("住宿标准")
        assert len(results) > 0

    def test_create_from_components_with_graph(self, sample_documents):
        """测试包含图谱检索器的创建"""
        vector_retriever = Mock()
        results1 = sample_documents[:2]
        vector_retriever.get_relevant_documents = Mock(return_value=results1)
        vector_retriever.invoke = Mock(return_value=results1)

        bm25_retriever = Mock()
        results2 = sample_documents[1:3]
        bm25_retriever.get_relevant_documents = Mock(return_value=results2)
        bm25_retriever.invoke = Mock(return_value=results2)

        graph_retriever = Mock()
        results3 = sample_documents[2:4]
        graph_retriever.get_relevant_documents = Mock(return_value=results3)
        graph_retriever.invoke = Mock(return_value=results3)

        # 包含图谱检索器
        fusion_retriever = FusionRetriever.create_from_components(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            graph_retriever=graph_retriever,
            vector_weight=1.0,
            bm25_weight=1.0,
            graph_weight=0.8
        )

        # 验证三路检索
        assert len(fusion_retriever.retrievers) == 3
        assert fusion_retriever.weights == [1.0, 1.0, 0.8]

        results = fusion_retriever.get_relevant_documents("查询")
        assert len(results) > 0

    def test_create_fusion_retriever_factory(self, sample_documents):
        """测试工厂方法创建融合检索器"""
        from src.rag.fusion_retriever import create_fusion_retriever
        from src.rag.retriever import create_vectorstore

        # 创建向量存储
        vectorstore = create_vectorstore(sample_documents)

        # 使用工厂方法创建
        fusion_retriever = create_fusion_retriever(
            vectorstore=vectorstore,
            documents=sample_documents,
            vector_weight=1.5,
            bm25_weight=1.0,
            k_rrf=60,
            k_retrieve=5
        )

        # 验证创建成功
        assert fusion_retriever is not None
        assert len(fusion_retriever.retrievers) == 2  # vector + bm25

        # 测试检索
        results = fusion_retriever.get_relevant_documents("上海住宿标准", k=3)
        assert len(results) > 0
        assert len(results) <= 3

        # 验证融合元数据
        assert 'fusion_score' in results[0].metadata
        assert 'fusion_sources' in results[0].metadata

    def test_create_fusion_retriever_with_graph(self, sample_documents):
        """测试工厂方法创建包含图谱检索的融合检索器"""
        from src.rag.fusion_retriever import create_fusion_retriever
        from src.rag.retriever import create_vectorstore

        # 创建向量存储
        vectorstore = create_vectorstore(sample_documents)

        # 创建模拟图谱检索器
        graph_retriever = Mock()
        results3 = sample_documents[2:4]
        graph_retriever.get_relevant_documents = Mock(return_value=results3)
        graph_retriever.invoke = Mock(return_value=results3)

        # 包含图谱检索器
        fusion_retriever = create_fusion_retriever(
            vectorstore=vectorstore,
            documents=sample_documents,
            graph_retriever=graph_retriever,
            vector_weight=1.0,
            bm25_weight=1.0,
            graph_weight=0.8
        )

        # 验证三路检索
        assert len(fusion_retriever.retrievers) == 3

        results = fusion_retriever.get_relevant_documents("交通标准", k=3)
        assert len(results) > 0

    def test_real_world_scenario(self, sample_documents):
        """测试真实场景：语义查询与关键词查询的融合"""
        from src.rag.fusion_retriever import create_fusion_retriever
        from src.rag.retriever import create_vectorstore

        # 创建向量存储
        vectorstore = create_vectorstore(sample_documents)

        # 创建融合检索器
        fusion_retriever = create_fusion_retriever(
            vectorstore=vectorstore,
            documents=sample_documents,
            k_retrieve=10
        )

        # 测试查询1：语义查询（应该匹配"北京"相关文档）
        results = fusion_retriever.get_relevant_documents("去北京出差能住多少钱的酒店", k=3)
        assert len(results) > 0

        # 验证返回结果包含住宿或价格相关内容
        all_content = " ".join([doc.page_content for doc in results])
        assert "住宿" in all_content or "标准间" in all_content or "元" in all_content or "城市" in all_content

        # 测试查询2：关键词查询（精确匹配）
        results = fusion_retriever.get_relevant_documents("市内交通实报实销", k=2)
        assert len(results) > 0

        # 应该检索到"市内交通"相关文档
        contents = [doc.page_content for doc in results]
        assert any("市内交通" in content or "交通" in content for content in contents)

    def test_fusion_improves_recall(self, sample_documents):
        """测试融合检索提升召回率"""
        from src.rag.fusion_retriever import create_fusion_retriever
        from src.rag.retriever import create_vectorstore, get_retriever
        from src.rag.hybrid_retriever import ChineseBM25Retriever

        # 创建向量存储
        vectorstore = create_vectorstore(sample_documents)

        # 单独测试向量检索（使用invoke）
        vector_retriever = get_retriever(vectorstore, k=5)
        vector_results = vector_retriever.invoke("上海住宿标准")
        vector_ids = {doc.metadata.get('id') for doc in vector_results}

        # 单独测试BM25检索（使用invoke）
        bm25_retriever = ChineseBM25Retriever.from_documents(sample_documents, k=5)
        bm25_results = bm25_retriever.invoke("上海住宿标准")
        bm25_ids = {doc.metadata.get('id') for doc in bm25_results}

        # 融合检索
        fusion_retriever = create_fusion_retriever(
            vectorstore=vectorstore,
            documents=sample_documents,
            k_retrieve=5
        )
        fusion_results = fusion_retriever.get_relevant_documents("上海住宿标准", k=5)
        fusion_ids = {doc.metadata.get('id') for doc in fusion_results}

        # 融合检索应该覆盖更多文档（召回率提升）
        # 至少应该包含向量检索和BM25检索的并集的一部分
        assert len(fusion_ids) >= len(vector_ids) or len(fusion_ids) >= len(bm25_ids)

    def test_metadata_preservation(self, sample_documents):
        """测试元数据保留"""
        from src.rag.fusion_retriever import create_fusion_retriever
        from src.rag.retriever import create_vectorstore

        vectorstore = create_vectorstore(sample_documents)
        fusion_retriever = create_fusion_retriever(
            vectorstore=vectorstore,
            documents=sample_documents
        )

        results = fusion_retriever.get_relevant_documents("住宿", k=3)

        # 验证原始元数据保留
        for doc in results:
            assert 'id' in doc.metadata or 'source' in doc.metadata

            # 验证添加了融合元数据
            assert 'fusion_score' in doc.metadata
            assert 'fusion_sources' in doc.metadata
            assert isinstance(doc.metadata['fusion_score'], float)
            assert isinstance(doc.metadata['fusion_sources'], list)


class TestFusionRetrieverEdgeCases:
    """边界情况和错误处理测试"""

    def test_empty_retrievers_list(self):
        """测试空检索器列表"""
        with pytest.raises(ValueError, match="至少需要一个检索器"):
            FusionRetriever(retrievers=[], weights=[])

    def test_mismatched_weights(self):
        """测试权重数量不匹配"""
        retriever = Mock()
        retriever.invoke = Mock(return_value=[])

        with pytest.raises(ValueError, match="检索器数量.*与权重数量.*不匹配"):
            FusionRetriever(retrievers=[retriever], weights=[1.0, 2.0])

    def test_rrf_mismatched_inputs(self):
        """测试RRF输入不匹配"""
        fusion = RRFFusion(k=60)

        doc = Document(page_content="test", metadata={"id": "1"})
        results_list = [[doc], [doc]]
        weights = [1.0]  # 只有1个权重，但有2个结果列表

        with pytest.raises(ValueError, match="结果列表数量.*与权重数量.*不匹配"):
            fusion.fuse(results_list, weights)

    def test_get_document_id_with_hash(self):
        """测试文档ID获取（使用内容哈希）"""
        fusion = RRFFusion()

        # 没有id的文档
        doc = Document(page_content="test content")
        doc_id = fusion._get_document_id(doc)

        # 应该返回哈希值
        assert isinstance(doc_id, str)
        assert doc_id == str(hash("test content"))

    def test_get_document_id_with_metadata(self):
        """测试文档ID获取（使用metadata）"""
        fusion = RRFFusion()

        # 有id的文档
        doc = Document(page_content="test", metadata={"id": "doc123"})
        doc_id = fusion._get_document_id(doc)

        assert doc_id == "doc123"

    def test_all_retrievers_fail_with_ignore_errors(self):
        """测试所有检索器都失败（忽略错误）"""
        retriever1 = Mock()
        retriever1.invoke = Mock(side_effect=Exception("失败1"))

        retriever2 = Mock()
        retriever2.invoke = Mock(side_effect=Exception("失败2"))

        fusion_retriever = FusionRetriever(
            retrievers=[retriever1, retriever2],
            weights=[1.0, 1.0],
            ignore_errors=True
        )

        results = fusion_retriever.get_relevant_documents("查询")
        assert results == []

    def test_partial_retriever_failure(self):
        """测试部分检索器失败"""
        retriever1 = Mock()
        retriever1.invoke = Mock(side_effect=Exception("失败"))

        retriever2 = Mock()
        results = [Document(page_content="成功", metadata={"id": "1"})]
        retriever2.invoke = Mock(return_value=results)

        fusion_retriever = FusionRetriever(
            retrievers=[retriever1, retriever2],
            weights=[1.0, 1.0],
            ignore_errors=True
        )

        results = fusion_retriever.get_relevant_documents("查询")
        assert len(results) == 1
        assert results[0].page_content == "成功"

    def test_retriever_without_invoke_or_get_relevant_documents(self):
        """测试检索器没有invoke或get_relevant_documents方法"""
        retriever = Mock(spec=[])  # 空spec，没有任何方法

        # 应该在构造时就抛出TypeError（提前验证，这是HIGH级别修复的结果）
        with pytest.raises(TypeError, match="必须实现invoke\\(\\)或get_relevant_documents\\(\\)方法"):
            FusionRetriever(
                retrievers=[retriever],
                weights=[1.0],
                ignore_errors=True
            )

    def test_custom_rrf_k_parameter(self):
        """测试自定义RRF k参数"""
        fusion = RRFFusion(k=30)  # 非默认值

        doc1 = Document(page_content="doc1", metadata={"id": "1"})
        doc2 = Document(page_content="doc2", metadata={"id": "2"})

        results_list = [[doc1, doc2]]
        weights = [1.0]

        fused = fusion.fuse(results_list, weights)

        # 验证使用了k=30
        # doc1: 1.0/(30+1) = 1/31 ≈ 0.0323
        # doc2: 1.0/(30+2) = 1/32 ≈ 0.0313
        assert abs(fused[0].metadata['fusion_score'] - 1/31) < 0.0001
        assert abs(fused[1].metadata['fusion_score'] - 1/32) < 0.0001

    def test_large_number_of_retrievers(self):
        """测试大量检索器"""
        retrievers = []
        weights = []

        for i in range(10):
            retriever = Mock()
            doc = Document(page_content=f"doc{i}", metadata={"id": f"doc{i}"})
            retriever.invoke = Mock(return_value=[doc])
            retrievers.append(retriever)
            weights.append(1.0)

        fusion_retriever = FusionRetriever(
            retrievers=retrievers,
            weights=weights
        )

        results = fusion_retriever.get_relevant_documents("查询", k=10)
        assert len(results) == 10

    def test_zero_weight(self):
        """测试权重为0"""
        retriever1 = Mock()
        doc1 = Document(page_content="doc1", metadata={"id": "1"})
        retriever1.invoke = Mock(return_value=[doc1])

        retriever2 = Mock()
        doc2 = Document(page_content="doc2", metadata={"id": "2"})
        retriever2.invoke = Mock(return_value=[doc2])

        fusion_retriever = FusionRetriever(
            retrievers=[retriever1, retriever2],
            weights=[1.0, 0.0]  # 第二个检索器权重为0
        )

        results = fusion_retriever.get_relevant_documents("查询")

        # doc1应该有更高的分数（权重更高）
        if len(results) >= 2:
            assert results[0].metadata['fusion_score'] > results[1].metadata['fusion_score']

    def test_top_k_with_fewer_results(self):
        """测试请求的k大于实际结果数"""
        retriever = Mock()
        doc = Document(page_content="唯一的文档", metadata={"id": "1"})
        retriever.invoke = Mock(return_value=[doc])

        fusion_retriever = FusionRetriever(
            retrievers=[retriever],
            weights=[1.0]
        )

        # 请求10个，但只有1个
        results = fusion_retriever.get_relevant_documents("查询", k=10)
        assert len(results) == 1

    def test_rrf_score_ordering(self):
        """测试RRF分数正确排序"""
        fusion = RRFFusion(k=60)

        # 创建多个文档
        docs = [
            Document(page_content=f"doc{i}", metadata={"id": f"doc{i}"})
            for i in range(5)
        ]

        # 模拟两路检索，不同的排序
        results_list = [
            [docs[0], docs[1], docs[2]],  # 第一路
            [docs[2], docs[0], docs[3]]   # 第二路：doc0和doc2位置不同
        ]
        weights = [1.0, 1.0]

        fused = fusion.fuse(results_list, weights)

        # 验证doc0和doc2应该排在前面（因为在两路都出现）
        top_ids = {fused[0].metadata['id'], fused[1].metadata['id']}
        assert 'doc0' in top_ids or 'doc2' in top_ids

    def test_create_from_components_without_graph(self):
        """测试不使用图谱检索器创建"""
        vector_ret = Mock()
        vector_ret.invoke = Mock(return_value=[Document(page_content="v", metadata={"id": "1"})])

        bm25_ret = Mock()
        bm25_ret.invoke = Mock(return_value=[Document(page_content="b", metadata={"id": "2"})])

        # 不传graph_retriever（None）
        fusion_retriever = FusionRetriever.create_from_components(
            vector_retriever=vector_ret,
            bm25_retriever=bm25_ret,
            graph_retriever=None,
            k=60
        )

        assert len(fusion_retriever.retrievers) == 2
        results = fusion_retriever.get_relevant_documents("test")
        assert len(results) >= 1

    def test_document_without_metadata(self):
        """测试没有metadata的文档"""
        fusion = RRFFusion(k=60)

        # 创建没有metadata属性的文档（极端情况）
        doc = Document(page_content="test content")
        # 确保没有metadata
        if hasattr(doc, 'metadata'):
            delattr(doc, 'metadata')

        results_list = [[doc]]
        weights = [1.0]

        fused = fusion.fuse(results_list, weights)

        # 应该自动添加metadata
        assert len(fused) == 1
        assert hasattr(fused[0], 'metadata')
        assert 'fusion_score' in fused[0].metadata

    def test_retriever_with_old_api(self):
        """测试使用旧API的检索器（get_relevant_documents）"""
        # 模拟只有get_relevant_documents方法的旧检索器
        retriever = Mock()
        doc = Document(page_content="old api", metadata={"id": "1"})
        retriever.get_relevant_documents = Mock(return_value=[doc])
        # 移除invoke方法
        del retriever.invoke

        fusion_retriever = FusionRetriever(
            retrievers=[retriever],
            weights=[1.0]
        )

        results = fusion_retriever.get_relevant_documents("查询")
        assert len(results) == 1
        assert results[0].page_content == "old api"

    def test_retriever_failure_without_ignore_errors(self):
        """测试检索器失败且不忽略错误"""
        retriever = Mock()
        retriever.invoke = Mock(side_effect=ValueError("检索失败"))

        fusion_retriever = FusionRetriever(
            retrievers=[retriever],
            weights=[1.0],
            ignore_errors=False  # 不忽略错误
        )

        # 应该抛出异常
        with pytest.raises(ValueError, match="检索失败"):
            fusion_retriever.get_relevant_documents("查询")
