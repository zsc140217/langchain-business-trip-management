"""
生成100人小公司的模拟数据
用于构建知识图谱：组织架构、员工、项目、差旅记录
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict

# ==================== 基础数据 ====================

# 姓氏和名字
SURNAMES = ["张", "李", "王", "刘", "陈", "杨", "黄", "赵", "周", "吴", "徐", "孙", "马", "朱", "胡", "郭", "林", "何", "高", "罗"]
GIVEN_NAMES = ["伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "军", "洋", "勇", "艳", "杰", "娟", "涛", "明", "超", "秀兰", "霞"]

# 部门配置
DEPARTMENTS = {
    "管理层": {"count": 2, "roles": ["总经理", "副总经理"]},
    "人事部": {"count": 3, "roles": ["人事经理", "人事专员"]},
    "财务部": {"count": 4, "roles": ["财务经理", "会计", "出纳"]},
    "采购部": {"count": 6, "roles": ["采购经理", "采购员"]},
    "销售部": {"count": 17, "roles": ["销售总监", "大区经理", "销售经理", "销售代表"]},
    "生产部": {"count": 43, "roles": ["生产经理", "车间主任", "生产工人"]},
    "质检部": {"count": 5, "roles": ["质检经理", "质检员"]},
    "研发部": {"count": 9, "roles": ["研发经理", "研发工程师"]},
    "后勤部": {"count": 7, "roles": ["后勤经理", "司机", "保安", "清洁工"]},
    "仓储部": {"count": 4, "roles": ["仓储经理", "仓管员"]}
}

# 城市和出差原因
CITIES = {
    "北京": ["客户拜访", "展会参加", "总部会议"],
    "上海": ["客户拜访", "展会参加", "技术交流"],
    "深圳": ["供应商考察", "电子元件采购", "技术交流"],
    "广州": ["供应商考察", "市场调研", "客户拜访"],
    "成都": ["区域客户拜访", "设备安装", "售后服务"],
    "西安": ["区域客户拜访", "项目验收", "技术支持"],
    "杭州": ["客户拜访", "技术交流", "展会参加"],
    "武汉": ["区域客户拜访", "设备安装"],
    "重庆": ["区域客户拜访", "市场调研"],
    "甘孜州": ["偏远项目支持", "设备安装"],
    "阿坝州": ["偏远项目支持", "现场勘查"],
    "凉山州": ["偏远项目支持", "技术支持"]
}

# 项目列表
PROJECTS = [
    {"name": "华北地区客户设备交付项目", "department": "销售部", "cities": ["北京", "天津"]},
    {"name": "西南市场拓展项目", "department": "销售部", "cities": ["成都", "重庆", "甘孜州"]},
    {"name": "供应链优化项目", "department": "采购部", "cities": ["深圳", "广州", "东莞"]},
    {"name": "智能设备研发项目", "department": "研发部", "cities": ["上海", "杭州"]},
    {"name": "华东区域客户维护项目", "department": "销售部", "cities": ["上海", "杭州", "南京"]}
]

# 差旅频率（按部门）
TRAVEL_FREQUENCY = {
    "销售部": 0.8,  # 80%的人会出差
    "采购部": 0.6,
    "研发部": 0.3,
    "生产部": 0.1,
    "质检部": 0.4,
    "管理层": 0.5,
    "人事部": 0.1,
    "财务部": 0.2,
    "后勤部": 0.05,
    "仓储部": 0.05
}

# ==================== 数据生成函数 ====================

def generate_name(used_names: set) -> str:
    """生成不重复的姓名"""
    while True:
        name = random.choice(SURNAMES) + random.choice(GIVEN_NAMES)
        if len(GIVEN_NAMES) > 10:
            name += random.choice(["", random.choice(GIVEN_NAMES[:10])])
        if name not in used_names:
            used_names.add(name)
            return name

def generate_employees() -> List[Dict]:
    """生成员工数据"""
    employees = []
    used_names = set()
    employee_id = 1

    for dept_name, config in DEPARTMENTS.items():
        count = config["count"]
        roles = config["roles"]

        for i in range(count):
            # 分配角色
            if dept_name == "管理层":
                role = roles[i]
                is_executive = True
            elif "经理" in roles[0] or "总监" in roles[0]:
                if i == 0:
                    role = roles[0]  # 第一个是经理/总监
                    is_executive = "总监" in role or dept_name == "管理层"
                else:
                    role = roles[1] if len(roles) > 1 else roles[0]
                    is_executive = False
            else:
                role = random.choice(roles)
                is_executive = False

            employee = {
                "id": employee_id,
                "name": generate_name(used_names),
                "department": dept_name,
                "role": role,
                "is_executive": is_executive,
                "phone": f"138{random.randint(10000000, 99999999)}",
                "email": f"emp{employee_id:03d}@company.com"
            }
            employees.append(employee)
            employee_id += 1

    return employees

def assign_managers(employees: List[Dict]) -> List[Dict]:
    """分配上下级关系"""
    dept_managers = {}

    # 找出各部门经理
    for emp in employees:
        if "经理" in emp["role"] or "总监" in emp["role"]:
            dept_managers[emp["department"]] = emp["id"]

    # 找出总经理
    ceo_id = None
    for emp in employees:
        if emp["role"] == "总经理":
            ceo_id = emp["id"]
            emp["manager_id"] = None
            break

    # 分配上级
    for emp in employees:
        if emp["id"] == ceo_id:
            continue

        # 副总经理和部门经理/总监向总经理汇报
        if emp["role"] == "副总经理" or ("经理" in emp["role"] and emp["department"] != "管理层") or "总监" in emp["role"]:
            emp["manager_id"] = ceo_id
        else:
            # 其他员工向本部门经理汇报
            emp["manager_id"] = dept_managers.get(emp["department"], ceo_id)

    return employees

def generate_business_trips(employees: List[Dict]) -> List[Dict]:
    """生成差旅记录"""
    trips = []
    trip_id = 1

    # 过去3个月的差旅记录
    start_date = datetime.now() - timedelta(days=90)

    for emp in employees:
        dept = emp["department"]
        travel_prob = TRAVEL_FREQUENCY.get(dept, 0.1)

        # 判断是否出差
        if random.random() > travel_prob:
            continue

        # 生成1-5次出差记录
        num_trips = random.randint(1, 5)

        for _ in range(num_trips):
            # 随机城市
            city = random.choice(list(CITIES.keys()))
            purpose = random.choice(CITIES[city])

            # 随机项目（有50%概率关联项目）
            project = None
            if random.random() > 0.5:
                matching_projects = [p for p in PROJECTS if city in p["cities"]]
                if matching_projects:
                    project = random.choice(matching_projects)["name"]

            # 出差时间
            trip_start = start_date + timedelta(days=random.randint(0, 80))
            duration = random.randint(1, 5)  # 1-5天
            trip_end = trip_start + timedelta(days=duration)

            # 费用计算（基于差旅管理办法）
            accommodation = get_standard_amount(city, emp["is_executive"], "住宿") * duration
            meal = get_standard_amount(city, emp["is_executive"], "伙食") * duration
            transport = random.randint(500, 2000)  # 交通费

            trip = {
                "id": trip_id,
                "employee_id": emp["id"],
                "employee_name": emp["name"],
                "destination": city,
                "purpose": purpose,
                "project": project,
                "start_date": trip_start.strftime("%Y-%m-%d"),
                "end_date": trip_end.strftime("%Y-%m-%d"),
                "duration": duration,
                "accommodation_cost": accommodation,
                "meal_allowance": meal,
                "transport_cost": transport,
                "total_cost": accommodation + meal + transport,
                "approver_id": emp["manager_id"],
                "status": random.choice(["已批准", "已批准", "已批准", "待审批"])
            }
            trips.append(trip)
            trip_id += 1

    return trips

def get_standard_amount(city: str, is_executive: bool, expense_type: str) -> int:
    """根据差旅管理办法获取标准金额"""
    # 住宿标准
    accommodation_standards = {
        "北京": 500, "上海": 500, "深圳": 500, "广州": 500,
        "杭州": 450, "成都": 400, "西安": 400, "武汉": 400, "重庆": 400,
        "甘孜州": 300, "阿坝州": 300, "凉山州": 300
    }

    # 伙食标准
    meal_standards = {
        "北京": 100, "上海": 100, "深圳": 100, "广州": 100,
        "杭州": 100, "成都": 100, "西安": 100, "武汉": 100, "重庆": 100,
        "甘孜州": 120, "阿坝州": 120, "凉山州": 120  # 三州地区
    }

    if expense_type == "住宿":
        return accommodation_standards.get(city, 350)
    elif expense_type == "伙食":
        return meal_standards.get(city, 100)

    return 0

# ==================== 主函数 ====================

def main():
    print("=" * 60)
    print("生成100人小公司模拟数据")
    print("=" * 60)

    # 生成员工
    print("\n[1/3] 生成员工数据...")
    employees = generate_employees()
    employees = assign_managers(employees)
    print(f"   [OK] 生成 {len(employees)} 名员工")

    # 统计部门
    dept_count = {}
    for emp in employees:
        dept_count[emp["department"]] = dept_count.get(emp["department"], 0) + 1
    print("\n   部门人数分布：")
    for dept, count in sorted(dept_count.items(), key=lambda x: -x[1]):
        print(f"     {dept}: {count}人")

    # 生成差旅记录
    print("\n[2/3] 生成差旅记录...")
    trips = generate_business_trips(employees)
    print(f"   [OK] 生成 {len(trips)} 条差旅记录")

    # 统计出差次数最多的部门
    dept_trips = {}
    for trip in trips:
        emp = next(e for e in employees if e["id"] == trip["employee_id"])
        dept_trips[emp["department"]] = dept_trips.get(emp["department"], 0) + 1
    print("\n   部门出差次数：")
    for dept, count in sorted(dept_trips.items(), key=lambda x: -x[1])[:5]:
        print(f"     {dept}: {count}次")

    # 保存数据
    print("\n[3/3] 保存数据...")
    data = {
        "employees": employees,
        "projects": PROJECTS,
        "business_trips": trips,
        "cities": list(CITIES.keys())
    }

    output_file = "data/mock_company_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"   [OK] 数据已保存到: {output_file}")

    # 统计信息
    print("\n" + "=" * 60)
    print("数据统计")
    print("=" * 60)
    print(f"员工总数: {len(employees)}")
    print(f"部门数量: {len(DEPARTMENTS)}")
    print(f"项目数量: {len(PROJECTS)}")
    print(f"差旅记录: {len(trips)}")
    print(f"涉及城市: {len(CITIES)}")
    print(f"高管人数: {sum(1 for e in employees if e['is_executive'])}")
    print(f"总出差费用: RMB {sum(t['total_cost'] for t in trips):,.2f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
