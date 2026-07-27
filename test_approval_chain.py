# -*- coding: utf-8 -*-
"""
审批链引擎测试脚本
验证不同金额的审批流程是否正确
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.reimbursement.approval_chain_engine import ApprovalChainEngine

def print_separator(title):
    """打印分隔线"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_approval_chain():
    """测试审批链引擎"""

    # 初始化引擎
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/business_trip")
    engine = ApprovalChainEngine(db_connection_string=db_url)

    # 测试用户ID（使用真实的user_id）
    test_users = {
        "张三": "user_03d1a143-7ae3-4233-a1cf-d5fb56141e17",  # employee
        "测试工程师": "test_user_001",  # testuser
        "系统管理员": "user_6c8e192d-e44e-4a80-8094-58c8e5894a6b",  # admin
    }

    # 测试场景
    test_cases = [
        ("小额报销", 800, "应该只需要直属经理审批"),
        ("中额报销", 3000, "需要直属经理和部门经理审批"),
        ("大额报销", 8000, "需要直属经理、部门经理和财务审批"),
        ("特大额报销", 25000, "需要全部四级审批"),
    ]

    print_separator("开始测试审批链引擎")

    for user_name, user_id in test_users.items():
        print(f"\n\n{'='*60}")
        print(f"测试用户: {user_name} ({user_id})")
        print('='*60)

        for case_name, amount, expected in test_cases:
            print(f"\n[场景] {case_name} - {amount}元")
            print(f"[预期] {expected}")

            try:
                # 步骤1: 匹配审批链配置
                chain_config = engine.match_approval_chain(
                    amount=amount,
                    department=None
                )

                if not chain_config:
                    print(f"[结果] ❌ 未找到匹配的审批链配置")
                    continue

                print(f"[配置] 规则名称: {chain_config['rule_name']}")

                # 步骤2: 解析具体审批人
                approval_chain = chain_config['approval_chain']
                print(f"[结果] ✅ 审批链配置匹配成功")
                print(f"  - 审批级别数: {len(approval_chain)}")
                print(f"  - 审批流程:")

                conn = engine._get_connection()
                from psycopg2.extras import RealDictCursor
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    for node in approval_chain:
                        role = node['role']
                        level = node['level']

                        # 解析审批人
                        approver_id = engine._resolve_approver(user_id, role, cursor)

                        if approver_id:
                            # 查询审批人信息
                            cursor.execute(
                                "SELECT full_name, position FROM users WHERE user_id = %s",
                                (approver_id,)
                            )
                            approver_info = cursor.fetchone()

                            if approver_info:
                                print(f"    Level {level}: {approver_info['full_name']} ({approver_info['position']}) - 角色: {role}")
                            else:
                                print(f"    Level {level}: {approver_id} - 角色: {role}")
                        else:
                            print(f"    Level {level}: ❌ 未找到审批人 - 角色: {role}")

            except Exception as e:
                print(f"[结果] ❌ 失败: {str(e)}")
                import traceback
                traceback.print_exc()

    print_separator("测试完成")

if __name__ == "__main__":
    # 设置编码
    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

    test_approval_chain()
