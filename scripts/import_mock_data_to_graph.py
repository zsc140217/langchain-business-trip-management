"""
将模拟数据导入Neo4j知识图谱
构建组织架构、员工关系、差旅记录等图谱
"""

import json
import sys
from pathlib import Path
from neo4j import GraphDatabase
from typing import List, Dict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class GraphImporter:
    """知识图谱导入器"""

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "neo4j123"):
        """初始化Neo4j连接"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"[OK] 连接到 Neo4j: {uri}")

    def close(self):
        """关闭连接"""
        self.driver.close()

    def clear_database(self):
        """清空数据库"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("[OK] 数据库已清空")

    def create_constraints(self):
        """创建约束和索引"""
        with self.driver.session() as session:
            # 员工ID唯一
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Employee) REQUIRE e.id IS UNIQUE")
            # 部门名称唯一
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Department) REQUIRE d.name IS UNIQUE")
            # 项目名称唯一
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.name IS UNIQUE")
            # 城市名称唯一
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE")
            # 差旅记录ID唯一
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:BusinessTrip) REQUIRE t.id IS UNIQUE")
            print("[OK] 约束和索引创建完成")

    def import_employees(self, employees: List[Dict]):
        """导入员工数据"""
        with self.driver.session() as session:
            for emp in employees:
                # 创建员工节点
                session.run("""
                    MERGE (e:Employee {id: $id})
                    SET e.name = $name,
                        e.role = $role,
                        e.is_executive = $is_executive,
                        e.phone = $phone,
                        e.email = $email
                """, **emp)

                # 关联部门
                session.run("""
                    MATCH (e:Employee {id: $emp_id})
                    MERGE (d:Department {name: $dept_name})
                    MERGE (e)-[:BELONGS_TO]->(d)
                """, emp_id=emp["id"], dept_name=emp["department"])

                # 关联上级
                if emp.get("manager_id"):
                    session.run("""
                        MATCH (e:Employee {id: $emp_id})
                        MATCH (m:Employee {id: $manager_id})
                        MERGE (e)-[:REPORTS_TO]->(m)
                    """, emp_id=emp["id"], manager_id=emp["manager_id"])

        print(f"[OK] 导入 {len(employees)} 名员工")

    def import_projects(self, projects: List[Dict]):
        """导入项目数据"""
        with self.driver.session() as session:
            for proj in projects:
                # 创建项目节点
                session.run("""
                    MERGE (p:Project {name: $name})
                    SET p.department = $department
                """, name=proj["name"], department=proj["department"])

                # 关联城市
                for city in proj["cities"]:
                    session.run("""
                        MATCH (p:Project {name: $proj_name})
                        MERGE (c:City {name: $city_name})
                        MERGE (p)-[:INVOLVES_CITY]->(c)
                    """, proj_name=proj["name"], city_name=city)

        print(f"[OK] 导入 {len(projects)} 个项目")

    def import_business_trips(self, trips: List[Dict]):
        """导入差旅记录"""
        with self.driver.session() as session:
            for trip in trips:
                # 创建差旅记录节点
                session.run("""
                    MERGE (t:BusinessTrip {id: $id})
                    SET t.destination = $destination,
                        t.purpose = $purpose,
                        t.start_date = $start_date,
                        t.end_date = $end_date,
                        t.duration = $duration,
                        t.accommodation_cost = $accommodation_cost,
                        t.meal_allowance = $meal_allowance,
                        t.transport_cost = $transport_cost,
                        t.total_cost = $total_cost,
                        t.status = $status
                """, **trip)

                # 关联出差人
                session.run("""
                    MATCH (t:BusinessTrip {id: $trip_id})
                    MATCH (e:Employee {id: $emp_id})
                    MERGE (e)-[:TRAVELED_ON]->(t)
                """, trip_id=trip["id"], emp_id=trip["employee_id"])

                # 关联目的地城市
                session.run("""
                    MATCH (t:BusinessTrip {id: $trip_id})
                    MERGE (c:City {name: $city_name})
                    MERGE (t)-[:TO_CITY]->(c)
                """, trip_id=trip["id"], city_name=trip["destination"])

                # 关联项目（如果有）
                if trip.get("project"):
                    session.run("""
                        MATCH (t:BusinessTrip {id: $trip_id})
                        MATCH (p:Project {name: $proj_name})
                        MERGE (t)-[:FOR_PROJECT]->(p)
                    """, trip_id=trip["id"], proj_name=trip["project"])

                # 关联审批人
                if trip.get("approver_id"):
                    session.run("""
                        MATCH (t:BusinessTrip {id: $trip_id})
                        MATCH (a:Employee {id: $approver_id})
                        MERGE (t)-[:APPROVED_BY]->(a)
                    """, trip_id=trip["id"], approver_id=trip["approver_id"])

        print(f"[OK] 导入 {len(trips)} 条差旅记录")

    def import_travel_standards(self):
        """导入差旅标准（从差旅管理办法文档提取）"""
        with self.driver.session() as session:
            # 住宿标准
            accommodation_standards = {
                "北京": 500, "上海": 500, "深圳": 500, "广州": 500,
                "杭州": 450, "成都": 400, "西安": 400, "武汉": 400, "重庆": 400,
                "甘孜州": 300, "阿坝州": 300, "凉山州": 300
            }

            for city, amount in accommodation_standards.items():
                session.run("""
                    MERGE (c:City {name: $city_name})
                    MERGE (s:Standard {type: '住宿标准', role: '公司高管'})
                    SET s.amount = $amount, s.unit = '元/天'
                    MERGE (s)-[:APPLIES_TO_CITY]->(c)
                """, city_name=city, amount=amount)

            # 伙食标准
            meal_standards = {
                "北京": 100, "上海": 100, "深圳": 100, "广州": 100,
                "杭州": 100, "成都": 100, "西安": 100, "武汉": 100, "重庆": 100,
                "甘孜州": 120, "阿坝州": 120, "凉山州": 120  # 三州地区
            }

            for city, amount in meal_standards.items():
                session.run("""
                    MERGE (c:City {name: $city_name})
                    MERGE (s:Standard {type: '伙食补助', role: '所有人员'})
                    SET s.amount = $amount, s.unit = '元/天'
                    MERGE (s)-[:APPLIES_TO_CITY]->(c)
                """, city_name=city, amount=amount)

        print("[OK] 导入差旅标准")

    def print_statistics(self):
        """打印图谱统计信息"""
        with self.driver.session() as session:
            # 节点统计
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            print("\n" + "=" * 60)
            print("图谱节点统计")
            print("=" * 60)
            for record in result:
                print(f"{record['label']}: {record['count']}个")

            # 关系统计
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)
            print("\n关系统计：")
            for record in result:
                print(f"{record['type']}: {record['count']}条")

            print("=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("导入模拟数据到Neo4j知识图谱")
    print("=" * 60)

    # 加载模拟数据
    data_file = project_root / "data" / "mock_company_data.json"
    print(f"\n[1/6] 加载数据: {data_file}")

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"   员工: {len(data['employees'])}人")
    print(f"   项目: {len(data['projects'])}个")
    print(f"   差旅记录: {len(data['business_trips'])}条")

    # 初始化导入器
    print("\n[2/6] 连接Neo4j...")
    importer = GraphImporter()

    # 清空数据库
    print("\n[3/6] 清空现有数据...")
    importer.clear_database()

    # 创建约束
    print("\n[4/6] 创建约束和索引...")
    importer.create_constraints()

    # 导入数据
    print("\n[5/6] 导入数据...")
    importer.import_employees(data["employees"])
    importer.import_projects(data["projects"])
    importer.import_business_trips(data["business_trips"])
    importer.import_travel_standards()

    # 统计信息
    print("\n[6/6] 生成统计信息...")
    importer.print_statistics()

    # 关闭连接
    importer.close()

    print("\n" + "=" * 60)
    print("[SUCCESS] 知识图谱构建完成！")
    print("=" * 60)
    print("\n访问 Neo4j Browser: http://localhost:7474")
    print("用户名: neo4j")
    print("密码: neo4j123")
    print("\n示例查询：")
    print("  1. 查看所有员工: MATCH (e:Employee) RETURN e LIMIT 25")
    print("  2. 查看组织架构: MATCH (e:Employee)-[:REPORTS_TO]->(m) RETURN e, m")
    print("  3. 查看差旅网络: MATCH (e:Employee)-[:TRAVELED_ON]->(t:BusinessTrip)-[:TO_CITY]->(c) RETURN e, t, c LIMIT 50")
    print("  4. 查看项目关联: MATCH (p:Project)-[:INVOLVES_CITY]->(c) RETURN p, c")


if __name__ == "__main__":
    main()
