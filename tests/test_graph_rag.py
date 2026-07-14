"""
知识图谱 RAG 测试

测试 GraphExtractor, GraphBuilder, GraphRetriever 的功能
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.rag.graph_extractor import Entity, Relationship, GraphExtractor
from src.rag.graph_builder import GraphBuilder
from src.rag.graph_retriever import GraphRetriever


class TestEntity:
    """测试 Entity 模型"""

    def test_entity_creation(self):
        """测试实体创建"""
        entity = Entity(
            name="北京",
            type="LOCATION",
            properties={"population": "2000万"}
        )

        assert entity.name == "北京"
        assert entity.type == "LOCATION"
        assert entity.properties["population"] == "2000万"

    def test_entity_equality(self):
        """测试实体相等性"""
        entity1 = Entity(name="北京", type="LOCATION", properties={})
        entity2 = Entity(name="北京", type="LOCATION", properties={"key": "value"})
        entity3 = Entity(name="上海", type="LOCATION", properties={})

        assert entity1 == entity2  # 相同名称和类型
        assert entity1 != entity3  # 不同名称

    def test_entity_hash(self):
        """测试实体哈希"""
        entity1 = Entity(name="北京", type="LOCATION", properties={})
        entity2 = Entity(name="北京", type="LOCATION", properties={})

        assert hash(entity1) == hash(entity2)
        assert len({entity1, entity2}) == 1  # 集合去重


class TestRelationship:
    """测试 Relationship 模型"""

    def test_relationship_creation(self):
        """测试关系创建"""
        rel = Relationship(
            source="员工",
            target="公司",
            type="WORKS_FOR",
            properties={"since": "2024"}
        )

        assert rel.source == "员工"
        assert rel.target == "公司"
        assert rel.type == "WORKS_FOR"


class TestGraphExtractor:
    """测试实体提取器"""

    def test_extract_entities_success(self):
        """测试成功提取实体"""
        # Mock LLM 以避免环境变量依赖
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = """
        {
            "entities": [
                {"name": "北京", "type": "LOCATION", "properties": {}},
                {"name": "副总", "type": "CONCEPT", "properties": {"level": "高级"}}
            ]
        }
        """
        mock_llm.invoke.return_value = mock_response

        extractor = GraphExtractor(llm=mock_llm)

        text = "北京市副总住宿标准为800元"
        entities = extractor.extract_entities(text)

        assert len(entities) == 2
        assert entities[0].name == "北京"
        assert entities[0].type == "LOCATION"

    def test_extract_entities_empty_text(self):
        """测试空文本"""
        mock_llm = Mock()
        extractor = GraphExtractor(llm=mock_llm)

        with pytest.raises(ValueError, match="文本不能为空"):
            extractor.extract_entities("")

    def test_extract_entities_llm_failure(self):
        """测试 LLM 调用失败"""
        # Mock LLM 抛出异常
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("LLM error")

        extractor = GraphExtractor(llm=mock_llm)

        text = "测试文本"
        entities = extractor.extract_entities(text)

        assert entities == []  # 失败时返回空列表

    def test_extract_relationships_success(self):
        """测试成功提取关系"""
        # Mock LLM 响应
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = """
        {
            "relationships": [
                {"source": "副总", "target": "北京", "type": "LOCATED_IN", "properties": {}}
            ]
        }
        """
        mock_llm.invoke.return_value = mock_response

        extractor = GraphExtractor(llm=mock_llm)

        entities = [
            Entity(name="副总", type="CONCEPT", properties={}),
            Entity(name="北京", type="LOCATION", properties={})
        ]
        text = "副总在北京工作"

        relationships = extractor.extract_relationships(text, entities)

        assert len(relationships) == 1
        assert relationships[0].source == "副总"
        assert relationships[0].target == "北京"

    def test_extract_full_pipeline(self):
        """测试完整提取流程"""
        # Mock LLM
        mock_llm = Mock()

        # 第一次调用：提取实体
        entity_response = Mock()
        entity_response.content = '{"entities": [{"name": "北京", "type": "LOCATION", "properties": {}}]}'

        # 第二次调用：提取关系
        rel_response = Mock()
        rel_response.content = '{"relationships": []}'

        mock_llm.invoke.side_effect = [entity_response, rel_response]

        extractor = GraphExtractor(llm=mock_llm)

        result = extractor.extract("北京住宿标准")

        assert "entities" in result
        assert "relationships" in result
        assert len(result["entities"]) == 1


class TestGraphBuilder:
    """测试图谱构建器"""

    @patch('src.rag.graph_builder.GraphDatabase')
    def test_init_success(self, mock_db):
        """测试成功初始化"""
        mock_driver = Mock()
        mock_db.driver.return_value = mock_driver

        builder = GraphBuilder()

        mock_db.driver.assert_called_once()
        mock_driver.verify_connectivity.assert_called_once()

    @patch('src.rag.graph_builder.GraphDatabase')
    def test_create_indexes(self, mock_db):
        """测试创建索引"""
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_db.driver.return_value = mock_driver

        builder = GraphBuilder()
        builder.create_indexes()

        # 验证执行了索引创建
        assert mock_session.run.call_count >= 3

    @patch('src.rag.graph_builder.GraphDatabase')
    def test_add_document_node(self, mock_db):
        """测试添加文档节点"""
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: "doc_001"
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_db.driver.return_value = mock_driver

        builder = GraphBuilder()
        doc_id = builder.add_document_node("doc_001", "测试内容", {})

        assert doc_id == "doc_001"
        mock_session.run.assert_called_once()


class TestGraphRetriever:
    """测试图谱检索器"""

    @patch('src.rag.graph_retriever.GraphDatabase')
    def test_init_success(self, mock_db):
        """测试成功初始化"""
        mock_driver = Mock()
        mock_db.driver.return_value = mock_driver
        mock_llm = Mock()

        retriever = GraphRetriever(llm=mock_llm)

        mock_db.driver.assert_called_once()
        mock_driver.verify_connectivity.assert_called_once()

    @patch('src.rag.graph_retriever.GraphDatabase')
    def test_generate_cypher(self, mock_db):
        """测试生成 Cypher 查询"""
        mock_driver = Mock()
        mock_db.driver.return_value = mock_driver

        # Mock LLM
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "MATCH (e:Entity) WHERE e.name = '北京' RETURN e"
        mock_llm.invoke.return_value = mock_response

        retriever = GraphRetriever(llm=mock_llm)

        cypher = retriever.generate_cypher("北京的住宿标准")

        assert "MATCH" in cypher
        assert "北京" in cypher


class TestIntegration:
    """集成测试"""

    @pytest.mark.skipif(True, reason="需要真实 Neo4j 环境")
    def test_full_pipeline(self):
        """测试完整流程：提取 -> 构建 -> 检索"""
        # 此测试需要真实 Neo4j 环境
        # 可以使用 testcontainers-neo4j 进行集成测试
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
