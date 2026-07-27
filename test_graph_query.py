# -*- coding: utf-8 -*-
"""测试知识图谱能否回答业务查询"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from neo4j import GraphDatabase

# 测试查询
test_queries = [
    {
        "query": "销售部出差最多的员工是谁？",
        "cypher": """
        MATCH (e:Employee)-[:BELONGS_TO]->(d:Department {name: '销售部'})
        MATCH (e)-[:TRAVELED_ON]->(bt:BusinessTrip)
        RETURN e.name as employee, count(bt) as trip_count
        ORDER BY trip_count DESC
        LIMIT 1
        """
    },
    {
        "query": "人事部有哪些员工？",
        "cypher": """
        MATCH (e:Employee)-[:BELONGS_TO]->(d:Department {name: '人事部'})
        RETURN e.name as employee
        """
    },
    {
        "query": "过去3个月有多少次出差到北京？",
        "cypher": """
        MATCH (bt:BusinessTrip)-[:TO_CITY]->(c:City {name: '北京'})
        RETURN count(bt) as trip_count
        """
    },
    {
        "query": "总经理是谁？",
        "cypher": """
        MATCH (e:Employee)
        WHERE e.position = '总经理'
        RETURN e.name as employee
        """
    },
    {
        "query": "采购部有多少人？",
        "cypher": """
        MATCH (e:Employee)-[:BELONGS_TO]->(d:Department {name: '采购部'})
        RETURN count(e) as employee_count
        """
    }
]

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neo4j123'))

print("=" * 70)
print("测试知识图谱业务查询能力")
print("=" * 70)

for i, test in enumerate(test_queries, 1):
    print(f"\n[测试 {i}] {test['query']}")
    print(f"Cypher: {test['cypher'].strip()}")

    try:
        with driver.session() as session:
            result = session.run(test['cypher'])
            records = list(result)

            if records:
                print(f"[OK] 查询成功，返回 {len(records)} 条结果:")
                for record in records[:5]:  # 只显示前5条
                    print(f"  {dict(record)}")
            else:
                print("[FAIL] 查询无结果")
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")

driver.close()
print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
