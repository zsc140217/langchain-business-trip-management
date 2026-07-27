# -*- coding: utf-8 -*-
"""
创建测试用户脚本
P0-1: 用户认证系统测试数据
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from src.services.user_service import UserService
from src.models.user import UserCreate
from src.database.db_config import get_db_connection, return_db_connection

def create_test_users():
    """创建3种测试用户"""
    try:
        user_service = UserService()

        # 1. 普通员工
        employee = UserCreate(
            username="employee",
            email="employee@company.com",
            password="test123456",
            full_name="张三",
            department="销售部",
            position="销售专员",
            is_executive=False,
            is_admin=False,
            phone="13800138001"
        )

        # 2. 高管
        executive = UserCreate(
            username="executive",
            email="executive@company.com",
            password="test123456",
            full_name="李总",
            department="管理层",
            position="销售总监",
            is_executive=True,
            is_admin=False,
            phone="13800138002"
        )

        # 3. 管理员
        admin = UserCreate(
            username="admin",
            email="admin@company.com",
            password="test123456",
            full_name="系统管理员",
            department="IT部",
            position="系统管理员",
            is_executive=False,
            is_admin=True,
            phone="13800138003"
        )

        users = [
            ("employee", employee, "普通员工"),
            ("executive", executive, "高管"),
            ("admin", admin, "管理员")
        ]

        print("=" * 60)
        print("创建测试用户")
        print("=" * 60)

        for username, user_data, role_name in users:
            try:
                token = user_service.register_user(user_data)
                user = token.user
                print(f"[OK] {role_name} '{username}' 创建成功")
                print(f"   - user_id: {user.user_id}")
                print(f"   - 姓名: {user.full_name}")
                print(f"   - 部门: {user.department}")
                print(f"   - 职位: {user.position}")
                print(f"   - 高管: {'是' if user.is_executive else '否'}")
                print(f"   - 管理员: {'是' if user.is_admin else '否'}")
                print()
            except Exception as e:
                if "duplicate key" in str(e).lower() or "已存在" in str(e):
                    print(f"[SKIP] {role_name} '{username}' 已存在")
                else:
                    print(f"[FAIL] {role_name} '{username}' 创建失败: {e}")
                print()

        print("=" * 60)
        print("用户列表")
        print("=" * 60)

        # 查询所有用户
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, username, full_name, department, position,
                       is_executive, is_admin, created_at
                FROM users
                ORDER BY created_at DESC
            """)

            users_list = cursor.fetchall()
            for user in users_list:
                print(f"用户ID: {user[0]}")
                print(f"  用户名: {user[1]}")
                print(f"  姓名: {user[2]}")
                print(f"  部门: {user[3]}")
                print(f"  职位: {user[4]}")
                print(f"  高管: {'是' if user[5] else '否'}")
                print(f"  管理员: {'是' if user[6] else '否'}")
                print(f"  创建时间: {user[7]}")
                print()

            cursor.close()
        finally:
            return_db_connection(conn)

        print("=" * 60)
        print("审批阈值说明")
        print("=" * 60)
        print("普通员工 (employee):")
        print("  - 日均限额: 550元/天")
        print("  - 交通标准: 硬席/高铁二等座")
        print("  - 住宿标准: ≤300元/天（成都）")
        print("  - 审批阈值: 550 × 天数 × 城市系数")
        print()
        print("高管 (executive):")
        print("  - 日均限额: 670元/天")
        print("  - 交通标准: 软席/高铁一等座")
        print("  - 住宿标准: ≤370元/天（成都）")
        print("  - 审批阈值: 670 × 天数 × 城市系数")
        print()
        print("管理员 (admin):")
        print("  - 拥有系统管理权限")
        print("  - 可查看所有审批记录")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"[ERROR] 创建用户失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = create_test_users()
    sys.exit(0 if success else 1)
