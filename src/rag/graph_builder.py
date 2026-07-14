"""
知识图谱构建器

将提取的实体和关系构建为 Neo4j 知识图谱

功能：
- 连接 Neo4j 数据库
- 创建索引优化查询性能
- 添加文档、实体、关系节点
- 支持增量更新和去重
"""
import json
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
from src.rag.graph_extractor import Entity, Relationship, GraphExtractor


class GraphBuilder:
    """
    知识图谱构建器

    负责将实体和关系写入 Neo4j 数据库
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "neo4j123"
    ):
        """
        初始化图谱构建器

        Args:
            uri: Neo4j 连接 URI
            username: 用户名
            password: 密码

        Raises:
            ServiceUnavailable: 如果无法连接到 Neo4j
            AuthError: 如果认证失败
        """
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            # 测试连接
            self.driver.verify_connectivity()
            print(f"[成功] 已连接到 Neo4j: {uri}")
        except ServiceUnavailable as e:
            raise ServiceUnavailable(f"无法连接到 Neo4j ({uri})，请确保 Neo4j 服务正在运行: {e}")
        except AuthError as e:
            raise AuthError(f"Neo4j 认证失败，请检查用户名和密码: {e}")

    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            print("[关闭] Neo4j 连接已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()

    def create_indexes(self):
        """
        创建索引以优化查询性能

        索引：
        - Entity.name: 实体名称索引
        - Entity.type: 实体类型索引
        - Document.id: 文档 ID 索引
        """
        with self.driver.session() as session:
            # 创建实体名称索引
            session.run("""
                CREATE INDEX entity_name_idx IF NOT EXISTS
                FOR (e:Entity) ON (e.name)
            """)

            # 创建实体类型索引
            session.run("""
                CREATE INDEX entity_type_idx IF NOT EXISTS
                FOR (e:Entity) ON (e.type)
            """)

            # 创建文档 ID 索引
            session.run("""
                CREATE INDEX document_id_idx IF NOT EXISTS
                FOR (d:Document) ON (d.id)
            """)

            # 创建全文搜索索引（实体名称）
            try:
                session.run("""
                    CREATE FULLTEXT INDEX entity_fulltext_idx IF NOT EXISTS
                    FOR (e:Entity) ON EACH [e.name, e.normalized_name]
                """)
            except Exception as e:
                # 旧版本 Neo4j 可能不支持全文索引
                print(f"[警告] 创建全文索引失败（可能不支持）: {e}")

            print("[成功] 索引创建完成")

    def clear_graph(self):
        """
        清空图谱数据

        警告：此操作将删除所有节点和关系
        """
        with self.driver.session() as session:
            # 删除所有节点和关系
            session.run("MATCH (n) DETACH DELETE n")
            print("[警告] 图谱已清空")

    def add_document_node(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        添加文档节点

        Args:
            doc_id: 文档唯一标识
            content: 文档内容
            metadata: 文档元数据

        Returns:
            str: 文档 ID
        """
        metadata = metadata or {}

        # 将 metadata 转换为 JSON 字符串（Neo4j 不支持嵌套 Map）
        metadata_json = json.dumps(metadata, ensure_ascii=False)

        with self.driver.session() as session:
            result = session.run("""
                MERGE (d:Document {id: $doc_id})
                SET d.content = $content,
                    d.metadata = $metadata_json,
                    d.updated_at = datetime()
                RETURN d.id AS doc_id
            """, doc_id=doc_id, content=content, metadata_json=metadata_json)

            record = result.single()
            return record["doc_id"] if record else doc_id

    def add_entities(self, entities: List[Entity], doc_id: str):
        """
        添加实体节点并关联到文档

        Args:
            entities: 实体列表
            doc_id: 关联的文档 ID
        """
        with self.driver.session() as session:
            for entity in entities:
                # 将 properties 转换为 JSON 字符串（Neo4j 不支持嵌套 Map）
                properties_json = json.dumps(entity.properties, ensure_ascii=False)

                # 创建或更新实体节点
                session.run("""
                    MERGE (e:Entity {name: $name, type: $type})
                    SET e.properties = $properties_json,
                        e.normalized_name = toLower($name),
                        e.updated_at = datetime()
                """, name=entity.name, type=entity.type, properties_json=properties_json)

                # 创建 MENTIONS 关系（文档提及实体）
                session.run("""
                    MATCH (d:Document {id: $doc_id})
                    MATCH (e:Entity {name: $name, type: $type})
                    MERGE (d)-[r:MENTIONS]->(e)
                    SET r.updated_at = datetime()
                """, doc_id=doc_id, name=entity.name, type=entity.type)

        print(f"[添加] {len(entities)} 个实体已添加并关联到文档 {doc_id}")

    def add_relationships(self, relationships: List[Relationship]):
        """
        添加实体之间的关系

        Args:
            relationships: 关系列表
        """
        with self.driver.session() as session:
            for rel in relationships:
                # 将 properties 转换为 JSON 字符串
                properties_json = json.dumps(rel.properties, ensure_ascii=False)

                # 动态创建关系类型
                query = f"""
                    MATCH (source:Entity {{name: $source}})
                    MATCH (target:Entity {{name: $target}})
                    MERGE (source)-[r:{rel.type}]->(target)
                    SET r.properties = $properties_json,
                        r.updated_at = datetime()
                """
                session.run(
                    query,
                    source=rel.source,
                    target=rel.target,
                    properties_json=properties_json
                )

        print(f"[添加] {len(relationships)} 个关系已添加")

    def build_from_documents(
        self,
        documents: List[Dict],
        extractor: Optional[GraphExtractor] = None
    ):
        """
        从文档列表构建知识图谱

        Args:
            documents: 文档列表，每个文档为 {"id": str, "content": str, "metadata": dict}
            extractor: 实体提取器实例，如果为 None 则自动创建
        """
        if not extractor:
            extractor = GraphExtractor()

        print(f"\n开始构建知识图谱，共 {len(documents)} 个文档...")

        for i, doc in enumerate(documents, 1):
            doc_id = doc.get("id", f"doc_{i}")
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            if not content:
                print(f"[跳过] 文档 {doc_id} 内容为空")
                continue

            print(f"\n[{i}/{len(documents)}] 处理文档: {doc_id}")

            # 添加文档节点
            self.add_document_node(doc_id, content, metadata)

            # 提取实体和关系
            try:
                extraction_result = extractor.extract(content)
                entities = extraction_result["entities"]
                relationships = extraction_result["relationships"]

                # 添加实体
                if entities:
                    self.add_entities(entities, doc_id)
                else:
                    print(f"[警告] 文档 {doc_id} 未提取到实体")

                # 添加关系
                if relationships:
                    self.add_relationships(relationships)
                else:
                    print(f"[信息] 文档 {doc_id} 未提取到关系")

            except Exception as e:
                print(f"[错误] 处理文档 {doc_id} 时出错: {e}")
                import traceback
                traceback.print_exc()
                continue

        print(f"\n[完成] 知识图谱构建完成！")

    def get_statistics(self) -> Dict:
        """
        获取图谱统计信息

        Returns:
            Dict: 包含节点数、关系数等统计信息
        """
        with self.driver.session() as session:
            # 统计节点数
            result = session.run("""
                MATCH (d:Document)
                RETURN count(d) AS doc_count
            """)
            doc_count = result.single()["doc_count"]

            result = session.run("""
                MATCH (e:Entity)
                RETURN count(e) AS entity_count
            """)
            entity_count = result.single()["entity_count"]

            # 统计关系数
            result = session.run("""
                MATCH ()-[r]->()
                RETURN count(r) AS rel_count
            """)
            rel_count = result.single()["rel_count"]

            # 按类型统计实体
            result = session.run("""
                MATCH (e:Entity)
                RETURN e.type AS type, count(e) AS count
                ORDER BY count DESC
            """)
            entity_types = {record["type"]: record["count"] for record in result}

            return {
                "documents": doc_count,
                "entities": entity_count,
                "relationships": rel_count,
                "entity_types": entity_types
            }


# 使用示例
if __name__ == "__main__":
    """测试知识图谱构建器"""
    print("测试知识图谱构建器...\n")

    # 测试文档
    test_documents = [
        {
            "id": "doc_001",
            "content": """
            北京市差旅住宿标准规定：
            - 副总及以上职级，住宿标准为每晚800元
            - 经理职级，住宿标准为每晚500元
            - 普通员工，住宿标准为每晚300元
            """,
            "metadata": {"source": "policy_doc", "date": "2024-01-01"}
        },
        {
            "id": "doc_002",
            "content": """
            差旅申请流程：
            1. 员工提交差旅申请
            2. 部门经理审批
            3. 财务部审核预算
            4. 批准后可以出差
            """,
            "metadata": {"source": "process_doc", "date": "2024-01-01"}
        }
    ]

    try:
        # 创建图谱构建器
        with GraphBuilder() as builder:
            # 创建索引
            print("创建索引...")
            builder.create_indexes()

            # 清空现有图谱（测试用）
            print("\n清空现有图谱...")
            builder.clear_graph()

            # 构建图谱
            print("\n构建知识图谱...")
            builder.build_from_documents(test_documents)

            # 获取统计信息
            print("\n获取图谱统计...")
            stats = builder.get_statistics()
            print("\n图谱统计信息：")
            print(f"  - 文档数: {stats['documents']}")
            print(f"  - 实体数: {stats['entities']}")
            print(f"  - 关系数: {stats['relationships']}")
            print(f"  - 实体类型分布: {stats['entity_types']}")

    except Exception as e:
        print(f"\n[错误] {e}")

    print("\n测试完成！")
