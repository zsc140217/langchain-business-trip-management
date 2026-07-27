# -*- coding: utf-8 -*-
"""
P0-2 会话管理系统验证脚本
创建日期: 2026-07-15
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_imports():
    """测试所有模块导入"""
    print("=" * 50)
    print("测试模块导入...")
    print("=" * 50)

    try:
        from src.database.db_config import db_config
        print("[OK] db_config 导入成功")
    except Exception as e:
        print(f"[FAIL] db_config 导入失败: {e}")
        return False

    try:
        from src.models.conversation import (
            Conversation,
            Message,
            ConversationCreate,
            MessageCreate
        )
        print("[OK] conversation 模型导入成功")
    except Exception as e:
        print(f"[FAIL] conversation 模型导入失败: {e}")
        return False

    try:
        from src.database.conversation_repository import conversation_repository
        print("[OK] conversation_repository 导入成功")
    except Exception as e:
        print(f"[FAIL] conversation_repository 导入失败: {e}")
        return False

    try:
        from src.services.conversation_service import conversation_service
        print("[OK] conversation_service 导入成功")
    except Exception as e:
        print(f"[FAIL] conversation_service 导入失败: {e}")
        return False

    try:
        from src.api.conversation_api import router
        print("[OK] conversation_api 导入成功")
    except Exception as e:
        print(f"[FAIL] conversation_api 导入失败: {e}")
        return False

    return True


def test_models():
    """测试 Pydantic 模型"""
    print("\n" + "=" * 50)
    print("测试 Pydantic 模型...")
    print("=" * 50)

    try:
        from src.models.conversation import ConversationCreate, MessageCreate

        # 测试会话创建模型
        conv_create = ConversationCreate(title="测试会话")
        print(f"[OK] ConversationCreate: {conv_create.model_dump()}")

        # 测试消息创建模型
        msg_create = MessageCreate(
            role="user",
            content="测试消息",
            metadata={"test": True}
        )
        print(f"[OK] MessageCreate: {msg_create.model_dump()}")

        return True
    except Exception as e:
        print(f"[FAIL] 模型测试失败: {e}")
        return False


def test_database_connection():
    """测试数据库连接（需要先配置环境变量）"""
    print("\n" + "=" * 50)
    print("测试数据库连接...")
    print("=" * 50)

    try:
        from src.database.db_config import db_config

        # 检查配置
        print(f"数据库配置:")
        print(f"  Host: {db_config.config['host']}")
        print(f"  Port: {db_config.config['port']}")
        print(f"  Database: {db_config.config['database']}")
        print(f"  User: {db_config.config['user']}")

        # 尝试连接（可能失败，因为数据库可能未初始化）
        try:
            with db_config.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    if result:
                        print("[OK] 数据库连接成功")
                        return True
        except Exception as e:
            print(f"[WARN] 数据库连接失败（可能未初始化）: {e}")
            print("   请先执行: psql -U postgres -d business_trip -f scripts/init_db.sql")
            return False
    except Exception as e:
        print(f"[FAIL] 数据库配置测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n[P0-2] 会话管理系统验证")
    print("=" * 50)

    results = {
        "imports": test_imports(),
        "models": test_models(),
        "database": test_database_connection()
    }

    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)

    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{test_name.ljust(20)}: {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n[SUCCESS] 所有测试通过!")
    else:
        print("\n[WARNING] 部分测试失败，请检查错误信息")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
