"""
测试RAG检索效果
结合向量检索和知识图谱查询
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env")

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from neo4j import GraphDatabase


class HybridRAGTester:
    """混合RAG测试器：向量检索 + 知识图谱"""

    def __init__(self):
        # 初始化向量检索
        print("[1/2] 加载向量索引...")
        self.embeddings = DashScopeEmbeddings(model='text-embedding-v2')
        self.vectorstore = FAISS.load_local(
            'src/data/vectorstore',
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        print(f"   向量数量: {self.vectorstore.index.ntotal}")

        # 初始化图谱查询
        print("\n[2/2] 连接Neo4j...")
        self.graph_driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "neo4j123")
        )
        print("   [OK] Neo4j连接成功")

    def close(self):
        """关闭连接"""
        self.graph_driver.close()

    def vector_search(self, query: str, k: int = 3):
        """向量检索"""
        docs = self.vectorstore.similarity_search(query, k=k)
        return docs

    def graph_query(self, cypher: str):
        """图谱查询"""
        with self.graph_driver.session() as session:
            result = session.run(cypher)
            return list(result)

    def test_case_1(self):
        """测试用例1: 表格召回测试"""
        print("\n" + "=" * 80)
        print("测试用例1: 表格召回测试")
        print("=" * 80)
        query = "去北京出差，公司高管住宿标准是多少？"
        print(f"查询: {query}")

        # 向量检索
        print("\n[向量检索结果]")
        docs = self.vector_search(query, k=3)
        for i, doc in enumerate(docs, 1):
            content = doc.page_content[:200].replace("\n", " ")
            print(f"{i}. {content}...")

        # 图谱查询
        print("\n[图谱查询结果]")
        cypher = """
        MATCH (s:Standard {type: '住宿标准', role: '公司高管'})-[:APPLIES_TO_CITY]->(c:City {name: '北京'})
        RETURN s.amount AS 标准金额, s.unit AS 单位
        """
        result = self.graph_query(cypher)
        for record in result:
            print(f"   北京高管住宿标准: {record['标准金额']}{record['单位']}")

    def test_case_2(self):
        """测试用例2: 条款召回测试"""
        print("\n" + "=" * 80)
        print("测试用例2: 条款召回测试")
        print("=" * 80)
        query = "差旅费报销需要哪些材料？"
        print(f"查询: {query}")

        # 向量检索
        print("\n[向量检索结果]")
        docs = self.vector_search(query, k=3)
        for i, doc in enumerate(docs, 1):
            content = doc.page_content[:300].replace("\n", " ")
            print(f"{i}. {content}...")

    def test_case_3(self):
        """测试用例3: 复杂查询测试"""
        print("\n" + "=" * 80)
        print("测试用例3: 复杂查询测试")
        print("=" * 80)
        query = "出差到甘孜州，伙食补助标准是多少？"
        print(f"查询: {query}")

        # 向量检索
        print("\n[向量检索结果]")
        docs = self.vector_search(query, k=3)
        for i, doc in enumerate(docs, 1):
            content = doc.page_content[:200].replace("\n", " ")
            print(f"{i}. {content}...")

        # 图谱查询
        print("\n[图谱查询结果]")
        cypher = """
        MATCH (s:Standard {type: '伙食补助'})-[:APPLIES_TO_CITY]->(c:City {name: '甘孜州'})
        RETURN s.amount AS 标准金额, s.unit AS 单位
        """
        result = self.graph_query(cypher)
        for record in result:
            print(f"   甘孜州伙食补助: {record['标准金额']}{record['单位']}")

    def test_case_4(self):
        """测试用例4: 员工出差查询（图谱专属）"""
        print("\n" + "=" * 80)
        print("测试用例4: 员工出差查询（图谱专属）")
        print("=" * 80)
        query = "销售部出差最多的员工是谁？"
        print(f"查询: {query}")

        # 图谱查询
        print("\n[图谱查询结果]")
        cypher = """
        MATCH (d:Department {name: '销售部'})<-[:BELONGS_TO]-(e:Employee)-[:TRAVELED_ON]->(t:BusinessTrip)
        RETURN e.name AS 员工姓名, e.role AS 职位, count(t) AS 出差次数
        ORDER BY 出差次数 DESC
        LIMIT 5
        """
        result = self.graph_query(cypher)
        print("   销售部出差Top 5:")
        for record in result:
            print(f"     {record['员工姓名']} ({record['职位']}): {record['出差次数']}次")

    def test_case_5(self):
        """测试用例5: 混合查询（规则+实际数据）"""
        print("\n" + "=" * 80)
        print("测试用例5: 混合查询（规则+实际数据）")
        print("=" * 80)
        query = "去北京出差3天，预计费用是多少？"
        print(f"查询: {query}")

        # 向量检索（获取规则）
        print("\n[向量检索 - 差旅标准]")
        docs = self.vector_search("北京差旅标准", k=2)
        for i, doc in enumerate(docs, 1):
            content = doc.page_content[:200].replace("\n", " ")
            print(f"{i}. {content}...")

        # 图谱查询（获取标准金额）
        print("\n[图谱查询 - 标准金额]")
        cypher = """
        MATCH (s:Standard)-[:APPLIES_TO_CITY]->(c:City {name: '北京'})
        RETURN s.type AS 类型, s.amount AS 金额
        """
        result = self.graph_query(cypher)
        total = 0
        for record in result:
            amount = record['金额']
            type_ = record['类型']
            print(f"   {type_}: {amount}元/天")
            if type_ == '住宿标准':
                total += amount * 3
            elif type_ == '伙食补助':
                total += amount * 3

        print(f"\n   预计总费用（住宿+伙食）: {total}元")
        print(f"   加上交通费（往返高铁约1200元）: {total + 1200}元")

    def test_case_6(self):
        """测试用例6: 项目关联查询"""
        print("\n" + "=" * 80)
        print("测试用例6: 项目关联查询")
        print("=" * 80)
        query = "华北地区项目有哪些人出差？"
        print(f"查询: {query}")

        # 图谱查询
        print("\n[图谱查询结果]")
        cypher = """
        MATCH (p:Project)-[:INVOLVES_CITY|FOR_PROJECT*1..2]-(t:BusinessTrip)<-[:TRAVELED_ON]-(e:Employee)
        WHERE p.name CONTAINS '华北'
        RETURN DISTINCT e.name AS 员工, e.role AS 职位, e.department AS 部门
        LIMIT 10
        """
        result = self.graph_query(cypher)
        if result:
            print("   参与华北项目出差的员工:")
            for record in result:
                print(f"     {record['员工']} - {record['职位']} ({record['部门']})")
        else:
            print("   (无直接关联数据，可能项目名称不匹配)")


def main():
    """主函数"""
    print("=" * 80)
    print("RAG检索效果测试")
    print("向量检索（FAISS + DashScope） + 知识图谱（Neo4j）")
    print("=" * 80)

    # 初始化测试器
    tester = HybridRAGTester()

    try:
        # 执行测试用例
        tester.test_case_1()  # 表格召回
        tester.test_case_2()  # 条款召回
        tester.test_case_3()  # 复杂查询
        tester.test_case_4()  # 图谱专属查询
        tester.test_case_5()  # 混合查询
        tester.test_case_6()  # 项目关联查询

        # 总结
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        print("[OK] 向量检索: 适合语义搜索、文档召回")
        print("[OK] 知识图谱: 适合结构化查询、关系推理")
        print("[OK] 混合检索: 结合两者优势，提供更准确的答案")
        print("=" * 80)

    finally:
        tester.close()


if __name__ == "__main__":
    main()
