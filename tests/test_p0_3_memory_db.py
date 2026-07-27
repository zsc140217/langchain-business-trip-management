"""
P0-3: 记忆系统数据库集成验证脚本
测试长期记忆从文件系统到PostgreSQL的迁移
"""

import sys
import os
import io

# 修复Windows终端编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_imports():
    """测试1: 验证模块导入"""
    print("=" * 60)
    print("测试1: 验证模块导入")
    print("=" * 60)

    try:
        from src.database.user_profile_repository import UserProfileRepository
        print("✅ UserProfileRepository 导入成功")

        from src.memory.long_term_memory import LongTermMemoryManager, UserProfile
        print("✅ LongTermMemoryManager 导入成功")

        from src.memory.memory_service import MemoryService
        print("✅ MemoryService 导入成功")

        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_repository():
    """测试2: 验证UserProfileRepository数据访问"""
    print("\n" + "=" * 60)
    print("测试2: 验证UserProfileRepository数据访问")
    print("=" * 60)

    try:
        from src.database.user_profile_repository import UserProfileRepository

        repo = UserProfileRepository()
        print("✅ UserProfileRepository 实例化成功")

        # 测试方法签名
        methods = [
            'find_by_user_id',
            'create',
            'update',
            'delete',
            'increment_city_count',
            'increment_hotel_count',
            'increment_customer_count',
            'add_intent',
            'increment_conversation_count',
            'get_top_cities',
            'get_top_hotels',
            'set_preference',
            'get_preference',
        ]

        for method in methods:
            if hasattr(repo, method):
                print(f"✅ 方法存在: {method}")
            else:
                print(f"❌ 方法缺失: {method}")
                return False

        return True
    except Exception as e:
        print(f"❌ Repository测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_long_term_memory():
    """测试3: 验证LongTermMemoryManager集成"""
    print("\n" + "=" * 60)
    print("测试3: 验证LongTermMemoryManager集成")
    print("=" * 60)

    try:
        from src.memory.long_term_memory import LongTermMemoryManager

        manager = LongTermMemoryManager()
        print("✅ LongTermMemoryManager 实例化成功")

        # 验证不再使用文件系统
        if hasattr(manager, 'storage_dir'):
            print("⚠️ 警告: storage_dir 属性仍然存在（应该已移除）")
        else:
            print("✅ 已移除文件系统依赖（storage_dir）")

        # 验证使用数据库repository
        if hasattr(manager, 'repository'):
            print("✅ 使用数据库 repository")
        else:
            print("❌ 缺少 repository 属性")
            return False

        return True
    except Exception as e:
        print(f"❌ LongTermMemoryManager测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_service():
    """测试4: 验证MemoryService适配"""
    print("\n" + "=" * 60)
    print("测试4: 验证MemoryService适配")
    print("=" * 60)

    try:
        from src.memory.memory_service import MemoryService

        # 测试不带profile_storage_dir参数实例化
        service = MemoryService()
        print("✅ MemoryService 实例化成功（无profile_storage_dir参数）")

        # 验证长期记忆管理器
        if hasattr(service, 'long_term_memory_manager'):
            print("✅ long_term_memory_manager 存在")

            ltm = service.long_term_memory_manager
            if hasattr(ltm, 'repository'):
                print("✅ 长期记忆使用数据库存储")
            else:
                print("❌ 长期记忆未使用数据库")
                return False
        else:
            print("❌ 缺少 long_term_memory_manager")
            return False

        return True
    except Exception as e:
        print(f"❌ MemoryService测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_connection():
    """测试5: 验证数据库连接（可选）"""
    print("\n" + "=" * 60)
    print("测试5: 验证数据库连接（可选）")
    print("=" * 60)

    try:
        from src.database.db_config import get_db_connection

        conn = get_db_connection()
        print("✅ 数据库连接成功")

        with conn.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'user_profiles'")
            if cursor.fetchone():
                print("✅ user_profiles 表存在")
            else:
                print("⚠️ user_profiles 表不存在（需要运行 init_db.sql）")

        conn.close()
        return True

    except Exception as e:
        print(f"⚠️ 数据库连接失败（需要配置数据库）: {e}")
        print("提示: 运行以下命令初始化数据库:")
        print("  createdb -U postgres business_trip")
        print("  psql -U postgres -d business_trip -f scripts/init_db.sql")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("P0-3: 记忆系统数据库集成验证")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("Repository接口", test_repository()))
    results.append(("LongTermMemory集成", test_long_term_memory()))
    results.append(("MemoryService适配", test_memory_service()))
    results.append(("数据库连接", test_database_connection()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:20} {status}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print("\n" + "=" * 60)
    print(f"总计: {passed_count}/{total_count} 通过")
    print("=" * 60)

    if passed_count == total_count:
        print("\n🎉 所有测试通过！P0-3任务完成。")
    elif passed_count >= total_count - 1:
        print("\n⚠️ 代码集成完成，需要配置数据库后才能完全运行。")
    else:
        print("\n❌ 部分测试失败，请检查错误信息。")


if __name__ == "__main__":
    main()
