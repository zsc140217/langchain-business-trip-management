#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GraphRAG 概念演示脚本
用实际数据帮助理解知识图谱核心概念
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from langchain_community.graphs import Neo4jGraph

def print_section(title):
    """打印分隔符"""
    print("\n" + "="*60)
    print(f">> {title}")
    print("="*60)

def demo_1_graph_structure():
    """演示1：图谱基本结构"""
    print_section("演示1：图谱基本结构 - 节点和边")

    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD")
    )

    print("\n【概念】知识图谱 = 节点（实体） + 边（关系）")
    print("类比：图 G = (V, E)")

    # 统计节点数量
    query_nodes = """
    MATCH (n)
    RETURN labels(n)[0] as type, count(n) as count
    ORDER BY count DESC
    """

    print("\n📊 节点统计（V - Vertices）：")
    results = graph.query(query_nodes)
    total_nodes = 0
    for row in results:
        if row['type']:
            print(f"  {row['type']:15s}: {row['count']:3d} 个")
            total_nodes += row['count']
    print(f"  {'总计':15s}: {total_nodes:3d} 个")

    # 统计关系数量
    query_rels = """
    MATCH ()-[r]->()
    RETURN type(r) as rel_type, count(r) as count
    ORDER BY count DESC
    """

    print("\n📊 关系统计（E - Edges）：")
    results = graph.query(query_rels)
    total_rels = 0
    for row in results:
        print(f"  {row['rel_type']:15s}: {row['count']:3d} 条")
        total_rels += row['count']
    print(f"  {'总计':15s}: {total_rels:3d} 条")

def demo_2_property_graph():
    """演示2：属性图 - 节点和边都有属性"""
    print_section("演示2：属性图（Property Graph）")

    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD")
    )

    print("\n【概念】属性图 = 普通图 + 属性（Properties）")
    print("类比：面向对象编程中的对象，每个节点/边都有字段")

    # 查询人物节点示例
    query = """
    MATCH (p:Entity)
    WHERE p.type = 'PERSON'
    RETURN p.name as name, p.type as type, p.properties as properties
    LIMIT 5
    """

    print("\n📋 示例：人物节点（带属性）")
    results = graph.query(query)
    for i, row in enumerate(results, 1):
        print(f"\n  节点{i}:")
        print(f"    name: {row['name']}")
        print(f"    type: {row['type']}")
        if row['properties']:
            print(f"    properties: {row['properties'][:100]}...")

def demo_3_relationships():
    """演示3：关系查询 - 图的核心价值"""
    print_section("演示3：关系查询 - 图数据库的核心优势")

    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD")
    )

    print("\n【概念】关系是一等公民（First-class citizen）")
    print("对比：SQL中关系是外键，需要JOIN；Neo4j中关系是直接存储的边")

    # 查询汇报关系
    query = """
    MATCH (p:Entity)-[r:WORKS_FOR]->(boss:Entity)
    WHERE p.type = 'PERSON' AND boss.type = 'PERSON'
    RETURN p.name as employee, boss.name as manager
    LIMIT 5
    """

    print("\n📋 示例：汇报关系（WORKS_FOR）")
    print("  SQL方式: SELECT e.name, m.name FROM employees e JOIN reports_to r ... JOIN employees m ...")
    print("  Cypher方式: MATCH (p)-[:WORKS_FOR]->(boss)")

    print("\n  实际数据：")
    results = graph.query(query)
    if results:
        for row in results:
            print(f"    {row['employee']} ──汇报给──> {row['manager']}")
    else:
        print("    (暂无 WORKS_FOR 关系数据)")

def demo_4_multi_hop():
    """演示4：多跳查询 - 图的强大之处"""
    print_section("演示4：多跳查询 - 关系的递归遍历")

    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD")
    )

    print("\n【概念】多跳查询（Multi-hop）")
    print("类比：图的DFS/BFS遍历，但是声明式的")

    # 查询文档提及关系（1跳）
    query_1hop = """
    MATCH (e:Entity)-[:MENTIONS]->(d:Document)
    WHERE e.type = 'PERSON'
    RETURN e.name as entity, d.id as doc_id
    LIMIT 3
    """

    print("\n📋 示例1：1跳查询")
    print("  问题：哪些人物出现在哪些文档中？")
    print("  Cypher: MATCH (person)-[:MENTIONS]->(doc)")

    results = graph.query(query_1hop)
    if results:
        print("\n  结果：")
        for row in results:
            print(f"    {row['entity']} 出现在 {row['doc_id']}")

    # 查询相关关系（2跳）
    query_2hop = """
    MATCH path = (e1:Entity)-[*2]-(e2:Entity)
    WHERE e1.type = 'PERSON' AND e2.type = 'PERSON' AND e1 <> e2
    RETURN e1.name as person1, e2.name as person2
    LIMIT 3
    """

    print("\n📋 示例2：2跳查询")
    print("  问题：通过2个关系连接的人物对？")
    print("  Cypher: MATCH (p1)-[*2]-(p2)")
    print("  说明：*2 表示「走2步」，这在SQL中需要复杂的递归CTE")

    results = graph.query(query_2hop)
    if results:
        print("\n  结果：")
        for row in results:
            print(f"    {row['person1']} <--2跳--> {row['person2']}")

def demo_5_sql_vs_cypher():
    """演示5：SQL vs Cypher 对比"""
    print_section("演示5：SQL vs Cypher 语法对比")

    print("\n【场景】查询：陈浩向谁汇报？")

    print("\n🔹 SQL方式（关系数据库）：")
    print("""
    -- 需要定义表结构
    CREATE TABLE employees (id INT, name VARCHAR, title VARCHAR);
    CREATE TABLE reports_to (employee_id INT, manager_id INT);

    -- 查询需要JOIN
    SELECT m.name
    FROM employees e
    JOIN reports_to r ON e.id = r.employee_id
    JOIN employees m ON r.manager_id = m.id
    WHERE e.name = '陈浩';
    """)

    print("\n🔹 Cypher方式（图数据库）：")
    print("""
    -- 数据直接存储为图
    (陈浩:PERSON) -[:WORKS_FOR]-> (李明:PERSON)

    -- 查询直接沿着关系走
    MATCH (p {name:"陈浩"})-[:WORKS_FOR]->(boss)
    RETURN boss.name
    """)

    print("\n【性能对比】")
    print("  1跳查询: SQL vs Cypher ≈ 差不多")
    print("  2跳查询: SQL慢 vs Cypher快")
    print("  3跳查询: SQL很慢 vs Cypher仍然快")
    print("  原因：Neo4j 使用指针直接连接节点，O(1) 遍历边")

def demo_6_graph_vs_table():
    """演示6：图思维 vs 表思维"""
    print_section("演示6：图思维 vs 表思维")

    print("\n【思维模式对比】")

    print("\n🔹 表思维（关系数据库）：")
    print("  1. 先设计Schema（表结构）")
    print("  2. 数据填入表")
    print("  3. 查询时 JOIN 表")
    print("  特点：结构化、固定Schema、擅长聚合")

    print("\n🔹 图思维（图数据库）：")
    print("  1. 识别实体（节点）")
    print("  2. 识别关系（边）")
    print("  3. 查询时沿着关系走")
    print("  特点：灵活、关系为核心、擅长遍历")

    print("\n【何时用图数据库？】")
    print("  ✅ 推荐关系（朋友的朋友）")
    print("  ✅ 知识图谱（实体关系网络）")
    print("  ✅ 路径查找（最短路径）")
    print("  ✅ 网络分析（影响力分析）")

    print("\n【何时用关系数据库？】")
    print("  ✅ 事务处理（银行转账）")
    print("  ✅ 数据聚合（统计报表）")
    print("  ✅ 固定Schema（ERP系统）")

def main():
    """主函数"""
    import sys
    import io
    # 设置 UTF-8 输出
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("\n" + "=" * 60)
    print("GraphRAG 核心概念实战演示".center(50))
    print("通过实际数据理解知识图谱".center(50))
    print("=" * 60)

    try:
        # 演示1：图谱结构
        demo_1_graph_structure()

        # 演示2：属性图
        demo_2_property_graph()

        # 演示3：关系查询
        demo_3_relationships()

        # 演示4：多跳查询
        demo_4_multi_hop()

        # 演示5：SQL vs Cypher
        demo_5_sql_vs_cypher()

        # 演示6：图思维 vs 表思维
        demo_6_graph_vs_table()

        print("\n" + "="*60)
        print("演示完成！".center(50))
        print("="*60)

        print("\n下一步：")
        print("  1. 访问 http://localhost:7474 可视化查看图谱")
        print("  2. 阅读 docs/GRAPHRAG_LEARNING_GUIDE.md 深入学习")
        print("  3. 尝试编写自己的 Cypher 查询")

    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
