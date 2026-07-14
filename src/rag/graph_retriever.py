"""
知识图谱检索器

基于 Neo4j 的图谱查询和检索，支持：
- 自然语言生成 Cypher 查询
- 多跳推理
- 图谱检索结果转换为文档
- 失败时降级到向量检索
"""
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, CypherSyntaxError
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from src.models.llm import get_llm
import json
import re


class GraphRetriever:
    """
    知识图谱检索器

    将自然语言查询转换为 Cypher 查询，检索相关文档和实体
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "neo4j123",
        llm=None,
        fallback_retriever=None
    ):
        """
        初始化图谱检索器

        Args:
            uri: Neo4j 连接 URI
            username: 用户名
            password: 密码
            llm: 语言模型实例，用于生成 Cypher 查询
            fallback_retriever: 降级检索器（如向量检索器）
        """
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            self.driver.verify_connectivity()
            print(f"[GraphRetriever] 已连接到 Neo4j: {uri}")
        except ServiceUnavailable as e:
            raise ServiceUnavailable(f"无法连接到 Neo4j: {e}")

        self.llm = llm if llm else get_llm(temperature=0.1)
        self.fallback_retriever = fallback_retriever

        # Cypher 生成提示词
        self.cypher_prompt = """你是一个 Neo4j Cypher 查询专家。根据用户的自然语言查询，生成对应的 Cypher 查询语句。

图谱结构：
- 节点类型：
  - Document: 文档节点 (属性: id, content, metadata)
  - Entity: 实体节点 (属性: name, type, properties)
- 关系类型：
  - MENTIONS: 文档提及实体 (Document)-[MENTIONS]->(Entity)
  - APPLIES_TO: 适用于 (Entity)-[APPLIES_TO]->(Entity)
  - WORKS_FOR: 工作于 (Entity)-[WORKS_FOR]->(Entity)
  - LOCATED_IN: 位于 (Entity)-[LOCATED_IN]->(Entity)
  - REQUIRES: 需要 (Entity)-[REQUIRES]->(Entity)
  - RELATES_TO: 相关 (Entity)-[RELATES_TO]->(Entity)

查询规则：
1. 只返回 Cypher 查询语句，不要解释
2. 使用 MATCH 查找模式
3. 使用 WHERE 过滤条件
4. 最终返回 Document 节点（通过 MENTIONS 关系）
5. 限制返回数量（LIMIT 5-10）
6. 对中文实体使用 toLower() 进行不区分大小写匹配

查询模板：
- 查找实体："北京" → MATCH (e:Entity) WHERE toLower(e.name) CONTAINS toLower('北京') ...
- 查找关系："副总的住宿标准" → MATCH (e1:Entity {{name: '副总'}})-[r:APPLIES_TO]->(e2) ...
- 多跳查询："A 和 B 的关系" → MATCH path = (a:Entity)-[*1..3]-(b:Entity) WHERE ...

用户查询：{query}

只返回 Cypher 查询语句："""

    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def generate_cypher(self, query: str) -> str:
        """
        根据自然语言生成 Cypher 查询

        Args:
            query: 用户查询

        Returns:
            str: Cypher 查询语句
        """
        prompt = self.cypher_prompt.format(query=query)
        messages = [
            SystemMessage(content="你是 Cypher 查询生成专家。"),
            HumanMessage(content=prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            cypher = response.content.strip()

            # 清理 Cypher（移除代码块标记）
            cypher = re.sub(r'```cypher\n?', '', cypher)
            cypher = re.sub(r'```\n?', '', cypher)
            cypher = cypher.strip()

            return cypher
        except Exception as e:
            print(f"[警告] Cypher 生成失败: {e}")
            return ""

    def execute_cypher(self, cypher: str) -> List[Dict]:
        """
        执行 Cypher 查询

        Args:
            cypher: Cypher 查询语句

        Returns:
            List[Dict]: 查询结果
        """
        with self.driver.session() as session:
            try:
                result = session.run(cypher)
                records = [record.data() for record in result]
                return records
            except CypherSyntaxError as e:
                print(f"[错误] Cypher 语法错误: {e}")
                return []
            except Exception as e:
                print(f"[错误] Cypher 执行失败: {e}")
                return []

    def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        """
        检索相关文档

        Args:
            query: 用户查询
            top_k: 返回文档数量

        Returns:
            List[Document]: 相关文档列表
        """
        print(f"\n[GraphRetriever] 查询: {query}")

        # 生成 Cypher 查询
        cypher = self.generate_cypher(query)
        if not cypher:
            print("[GraphRetriever] Cypher 生成失败，使用降级检索")
            return self._fallback_retrieve(query, top_k)

        print(f"[GraphRetriever] 生成 Cypher:\n{cypher}")

        # 执行查询
        results = self.execute_cypher(cypher)
        if not results:
            print("[GraphRetriever] 查询无结果，使用降级检索")
            return self._fallback_retrieve(query, top_k)

        # 转换为 Document 对象
        documents = []
        for record in results[:top_k]:
            # 查找 Document 节点数据
            doc_data = None
            for key, value in record.items():
                if isinstance(value, dict) and 'content' in value:
                    doc_data = value
                    break

            if doc_data:
                doc = Document(
                    page_content=doc_data.get('content', ''),
                    metadata=doc_data.get('metadata', {})
                )
                documents.append(doc)

        print(f"[GraphRetriever] 返回 {len(documents)} 个文档")
        return documents

    def multi_hop_retrieve(
        self,
        query: str,
        max_hops: int = 2,
        top_k: int = 5
    ) -> List[Document]:
        """
        多跳检索（遍历关系图）

        Args:
            query: 用户查询
            max_hops: 最大跳数
            top_k: 返回文档数量

        Returns:
            List[Document]: 相关文档列表
        """
        print(f"\n[GraphRetriever] 多跳检索 (max_hops={max_hops}): {query}")

        # 构建多跳 Cypher 查询
        cypher = f"""
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($query_term)
        WITH e
        MATCH path = (e)-[*1..{max_hops}]-(related:Entity)
        WITH related
        MATCH (d:Document)-[MENTIONS]->(related)
        RETURN DISTINCT d
        LIMIT {top_k}
        """

        # 从查询中提取关键词（简化版）
        query_term = query.split()[0] if query.split() else query

        with self.driver.session() as session:
            try:
                result = session.run(cypher, query_term=query_term)
                records = [record.data() for record in result]

                documents = []
                for record in records:
                    doc_data = record.get('d')
                    if doc_data:
                        doc = Document(
                            page_content=doc_data.get('content', ''),
                            metadata=doc_data.get('metadata', {})
                        )
                        documents.append(doc)

                print(f"[GraphRetriever] 多跳检索返回 {len(documents)} 个文档")
                return documents

            except Exception as e:
                print(f"[错误] 多跳检索失败: {e}")
                return self._fallback_retrieve(query, top_k)

    def _fallback_retrieve(self, query: str, top_k: int) -> List[Document]:
        """
        降级检索（使用向量检索器）

        Args:
            query: 用户查询
            top_k: 返回文档数量

        Returns:
            List[Document]: 相关文档列表
        """
        if self.fallback_retriever:
            print("[GraphRetriever] 使用降级检索器")
            return self.fallback_retriever.get_relevant_documents(query)[:top_k]
        else:
            print("[GraphRetriever] 无降级检索器，返回空列表")
            return []


# 使用示例
if __name__ == "__main__":
    """测试知识图谱检索器"""
    print("测试知识图谱检索器...\n")

    try:
        with GraphRetriever() as retriever:
            # 测试查询
            test_queries = [
                "北京的住宿标准是多少",
                "副总的差旅政策",
                "差旅申请流程"
            ]

            for query in test_queries:
                print("\n" + "=" * 60)
                documents = retriever.retrieve(query, top_k=3)

                if documents:
                    print(f"\n查询成功，找到 {len(documents)} 个文档：")
                    for i, doc in enumerate(documents, 1):
                        print(f"\n文档 {i}:")
                        print(doc.page_content[:200])
                else:
                    print("\n未找到相关文档")

    except Exception as e:
        print(f"\n[错误] {e}")

    print("\n测试完成！")
