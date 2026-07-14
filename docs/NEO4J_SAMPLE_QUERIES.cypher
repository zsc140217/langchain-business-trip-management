"""
Neo4j知识图谱示例查询
展示组织架构、差旅分析、项目管理等场景
"""

# 访问 Neo4j Browser: http://localhost:7474
# 用户名: neo4j
# 密码: neo4j123

# ==================== 1. 基础查询 ====================

# 查看所有员工（前25个）
MATCH (e:Employee)
RETURN e
LIMIT 25

# 查看所有部门及其人数
MATCH (d:Department)<-[:BELONGS_TO]-(e:Employee)
RETURN d.name AS 部门, count(e) AS 员工数
ORDER BY 员工数 DESC

# 查看高管列表
MATCH (e:Employee)
WHERE e.is_executive = true
RETURN e.name AS 姓名, e.role AS 职位, e.email AS 邮箱

# ==================== 2. 组织架构查询 ====================

# 查看组织架构树（员工和直属上级）
MATCH (e:Employee)-[:REPORTS_TO]->(m:Employee)
RETURN e, m
LIMIT 50

# 查看总经理的直接下属
MATCH (ceo:Employee {role: '总经理'})<-[:REPORTS_TO]-(direct:Employee)
RETURN ceo.name AS 总经理, collect(direct.name) AS 直接下属

# 查看某个部门的组织架构
MATCH (d:Department {name: '销售部'})<-[:BELONGS_TO]-(e:Employee)
OPTIONAL MATCH (e)-[:REPORTS_TO]->(m:Employee)
RETURN e.name AS 员工, e.role AS 职位, m.name AS 上级

# 查看某员工的管理链（向上追溯到总经理）
MATCH path = (e:Employee {name: '张伟'})-[:REPORTS_TO*]->(ceo:Employee {role: '总经理'})
RETURN path

# ==================== 3. 差旅分析查询 ====================

# 查看出差次数最多的员工（Top 10）
MATCH (e:Employee)-[:TRAVELED_ON]->(t:BusinessTrip)
RETURN e.name AS 姓名, e.department AS 部门, count(t) AS 出差次数
ORDER BY 出差次数 DESC
LIMIT 10

# 查看各部门的出差统计
MATCH (d:Department)<-[:BELONGS_TO]-(e:Employee)-[:TRAVELED_ON]->(t:BusinessTrip)
RETURN d.name AS 部门,
       count(DISTINCT e) AS 出差人数,
       count(t) AS 出差次数,
       sum(t.total_cost) AS 总费用
ORDER BY 总费用 DESC

# 查看最热门的出差目的地（Top 5）
MATCH (t:BusinessTrip)-[:TO_CITY]->(c:City)
RETURN c.name AS 城市, count(t) AS 出差次数, sum(t.total_cost) AS 总费用
ORDER BY 出差次数 DESC
LIMIT 5

# 查看某个城市的所有出差记录
MATCH (e:Employee)-[:TRAVELED_ON]->(t:BusinessTrip)-[:TO_CITY]->(c:City {name: '北京'})
RETURN e.name AS 员工, t.purpose AS 目的, t.start_date AS 开始日期, t.total_cost AS 总费用
ORDER BY t.start_date DESC

# 查看待审批的差旅申请
MATCH (e:Employee)-[:TRAVELED_ON]->(t:BusinessTrip)
WHERE t.status = '待审批'
OPTIONAL MATCH (t)-[:APPROVED_BY]->(a:Employee)
RETURN e.name AS 申请人, t.destination AS 目的地, t.start_date AS 开始日期, a.name AS 审批人

# ==================== 4. 项目管理查询 ====================

# 查看所有项目及其涉及的城市
MATCH (p:Project)-[:INVOLVES_CITY]->(c:City)
RETURN p.name AS 项目名称, collect(c.name) AS 涉及城市

# 查看某个项目的所有差旅记录
MATCH (e:Employee)-[:TRAVELED_ON]->(t:BusinessTrip)-[:FOR_PROJECT]->(p:Project {name: '华北地区客户设备交付项目'})
RETURN e.name AS 员工, t.destination AS 目的地, t.start_date AS 开始日期, t.total_cost AS 费用
ORDER BY t.start_date

# 查看各项目的差旅费用统计
MATCH (t:BusinessTrip)-[:FOR_PROJECT]->(p:Project)
RETURN p.name AS 项目名称,
       count(t) AS 出差次数,
       sum(t.total_cost) AS 总费用
ORDER BY 总费用 DESC

# 查看没有关联项目的差旅（临时性出差）
MATCH (e:Employee)-[:TRAVELED_ON]->(t:BusinessTrip)
WHERE NOT (t)-[:FOR_PROJECT]->()
RETURN e.name AS 员工, t.destination AS 目的地, t.purpose AS 目的, t.total_cost AS 费用
LIMIT 20

# ==================== 5. 差旅标准查询 ====================

# 查看各城市的住宿标准
MATCH (s:Standard {type: '住宿标准'})-[:APPLIES_TO_CITY]->(c:City)
RETURN c.name AS 城市, s.amount AS 标准金额, s.unit AS 单位
ORDER BY s.amount DESC

# 查看三州地区（特殊地区）的标准
MATCH (s:Standard)-[:APPLIES_TO_CITY]->(c:City)
WHERE c.name IN ['甘孜州', '阿坝州', '凉山州']
RETURN c.name AS 城市, s.type AS 标准类型, s.amount AS 金额, s.unit AS 单位

# ==================== 6. 复杂业务查询 ====================

# 查看某员工的完整出差网络（员工-差旅-城市-项目）
MATCH (e:Employee {name: '张伟'})-[:TRAVELED_ON]->(t:BusinessTrip)-[:TO_CITY]->(c:City)
OPTIONAL MATCH (t)-[:FOR_PROJECT]->(p:Project)
RETURN e, t, c, p

# 查看跨部门协作的项目（多个部门的员工都出差支持）
MATCH (p:Project)<-[:FOR_PROJECT]-(t:BusinessTrip)<-[:TRAVELED_ON]-(e:Employee)-[:BELONGS_TO]->(d:Department)
RETURN p.name AS 项目名称, collect(DISTINCT d.name) AS 参与部门
ORDER BY size(collect(DISTINCT d.name)) DESC

# 查看经常出差到同一城市的员工（可能需要协作）
MATCH (c:City)<-[:TO_CITY]-(t:BusinessTrip)<-[:TRAVELED_ON]-(e:Employee)
WITH c, e, count(t) AS 次数
WHERE 次数 >= 2
RETURN c.name AS 城市, collect(e.name) AS 常去员工
ORDER BY size(collect(e.name)) DESC

# 查看某经理审批的所有差旅及总费用
MATCH (manager:Employee {role: '销售经理'})<-[:APPROVED_BY]-(t:BusinessTrip)<-[:TRAVELED_ON]-(e:Employee)
RETURN manager.name AS 审批人,
       count(t) AS 审批次数,
       sum(t.total_cost) AS 审批总金额,
       collect(DISTINCT e.name) AS 下属列表

# 查看超标费用的差旅（住宿费超过标准）
MATCH (e:Employee)-[:TRAVELED_ON]->(t:BusinessTrip)-[:TO_CITY]->(c:City)
MATCH (s:Standard {type: '住宿标准'})-[:APPLIES_TO_CITY]->(c)
WHERE t.accommodation_cost > s.amount * t.duration
RETURN e.name AS 员工,
       t.destination AS 目的地,
       t.accommodation_cost AS 实际住宿费,
       s.amount * t.duration AS 标准住宿费,
       t.accommodation_cost - s.amount * t.duration AS 超标金额
ORDER BY 超标金额 DESC

# ==================== 7. 路径查询 ====================

# 查看两个员工之间的最短路径（组织关系）
MATCH path = shortestPath((e1:Employee {name: '张伟'})-[*]-(e2:Employee {name: '李强'}))
RETURN path

# 查看从员工到审批人的完整链路
MATCH path = (e:Employee {name: '张伟'})-[:TRAVELED_ON]->(t:BusinessTrip)-[:APPROVED_BY]->(a:Employee)
RETURN path

# ==================== 8. 聚合分析 ====================

# 按月统计出差次数和费用
MATCH (t:BusinessTrip)
RETURN substring(t.start_date, 0, 7) AS 月份,
       count(t) AS 出差次数,
       sum(t.total_cost) AS 总费用
ORDER BY 月份

# 按出差天数分组统计
MATCH (t:BusinessTrip)
RETURN t.duration AS 出差天数, count(t) AS 次数
ORDER BY 出差天数

# 查看费用最高的10次出差
MATCH (e:Employee)-[:TRAVELED_ON]->(t:BusinessTrip)-[:TO_CITY]->(c:City)
RETURN e.name AS 员工, c.name AS 目的地, t.purpose AS 目的, t.total_cost AS 总费用
ORDER BY t.total_cost DESC
LIMIT 10

# ==================== 9. 可视化查询（推荐在Neo4j Browser中执行） ====================

# 查看完整的差旅网络（限制50个节点）
MATCH (e:Employee)-[:TRAVELED_ON]->(t:BusinessTrip)-[:TO_CITY]->(c:City)
RETURN e, t, c
LIMIT 50

# 查看组织架构全景图
MATCH (e:Employee)-[:BELONGS_TO]->(d:Department)
OPTIONAL MATCH (e)-[:REPORTS_TO]->(m:Employee)
RETURN e, d, m
LIMIT 100

# 查看项目-城市-差旅的关系网络
MATCH (p:Project)-[:INVOLVES_CITY]->(c:City)
OPTIONAL MATCH (c)<-[:TO_CITY]-(t:BusinessTrip)
RETURN p, c, t
LIMIT 50
