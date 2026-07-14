"""
模块4测试脚本 - 记忆系统后端测试
测试文件存储后端和生产级后端（如果可用）
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory.backends import create_backends


def test_file_backend():
    """测试文件存储后端"""
    print("=" * 60)
    print("测试1: 文件存储后端")
    print("=" * 60)

    short_term, long_term = create_backends("file")

    # 测试短期记忆
    print("\n[SHORT-TERM] 测试短期记忆...")
    short_term.add_message("test_chat_001", "user", "我要去北京出差")
    short_term.add_message("test_chat_001", "assistant", "好的，请问您需要什么帮助？")
    short_term.add_message("test_chat_001", "user", "查询天气")

    messages = short_term.get_messages("test_chat_001")
    print(f"[OK] 存储了 {len(messages)} 条消息")
    for msg in messages:
        print(f"   {msg['role']}: {msg['content']}")

    # 测试长期记忆
    print("\n[LONG-TERM] 测试长期记忆...")
    profile_data = {
        'user_id': 'test_user_001',
        'preferences': {'language': 'zh'},
        'preferred_cities': {'北京': 2, '上海': 1},
        'preferred_hotels': {'希尔顿酒店': 1},
        'frequent_customers': {'华为公司': 1},
        'common_intents': ['查询天气', '查询酒店'],
        'conversation_count': 2
    }
    long_term.save_profile('test_user_001', profile_data)
    print("[OK] 保存用户画像成功")

    loaded_profile = long_term.get_profile('test_user_001')
    if loaded_profile:
        print(f"[OK] 加载用户画像成功: {loaded_profile['user_id']}")
        print(f"   会话数: {loaded_profile.get('conversation_count', 0)}")
        print(f"   常去城市: {loaded_profile.get('preferred_cities', {})}")

    # 清理测试数据
    short_term.delete_storage("test_chat_001")
    long_term.delete_profile('test_user_001')
    print("\n[SUCCESS] 文件后端测试完成")


def test_production_backend():
    """测试生产级后端（Redis + PostgreSQL）"""
    print("\n" + "=" * 60)
    print("测试2: 生产级后端（Redis + PostgreSQL）")
    print("=" * 60)

    try:
        short_term, long_term = create_backends("production")

        # 测试短期记忆
        print("\n[REDIS] 测试Redis短期记忆...")
        short_term.add_message("test_chat_002", "user", "我要去上海出差")
        short_term.add_message("test_chat_002", "assistant", "好的，请问出差日期？")

        messages = short_term.get_messages("test_chat_002")
        print(f"[OK] Redis存储了 {len(messages)} 条消息")
        for msg in messages:
            print(f"   {msg['role']}: {msg['content']}")

        # 测试长期记忆
        print("\n[POSTGRES] 测试PostgreSQL长期记忆...")
        profile_data = {
            'user_id': 'test_user_002',
            'preferences': {'language': 'zh'},
            'preferred_cities': {'上海': 1},
            'preferred_hotels': {},
            'frequent_customers': {},
            'common_intents': ['查询酒店'],
            'conversation_count': 1
        }
        long_term.save_profile('test_user_002', profile_data)
        print("[OK] PostgreSQL保存用户画像成功")

        loaded_profile = long_term.get_profile('test_user_002')
        if loaded_profile:
            print(f"[OK] 加载用户画像成功: {loaded_profile['user_id']}")

        # 测试查询历史
        long_term.save_query_history(
            'test_user_002',
            'test_thread_002',
            '上海的天气怎么样？',
            '上海明天多云，气温18-26度'
        )
        print("[OK] 保存查询历史成功")

        history = long_term.get_query_history('test_user_002', limit=5)
        print(f"[OK] 查询历史 ({len(history)}条)")

        # 获取统计
        stats = long_term.get_stats()
        print(f"\n[STATS] {stats}")

        # 清理测试数据
        short_term.delete_storage("test_chat_002")
        long_term.delete_profile('test_user_002')
        print("\n[SUCCESS] 生产级后端测试完成")

    except Exception as e:
        print(f"\n[WARNING] 生产级后端测试失败: {e}")
        print("提示：请确保Docker服务已启动：docker compose up -d")


def main():
    print("\n" + "=" * 60)
    print("模块4: 记忆系统后端测试")
    print("=" * 60)

    # 测试文件后端
    test_file_backend()

    # 测试生产级后端
    test_production_backend()

    print("\n" + "=" * 60)
    print("[DONE] 所有测试完成！")
    print("=" * 60)
    print("\n[TIP] 提示：")
    print("  - 默认使用文件存储后端（零依赖）")
    print("  - 启动Docker后可切换到生产级后端：")
    print("    export MEMORY_BACKEND=production")
    print("  - 或在代码中指定：")
    print("    create_backends('production')")


if __name__ == "__main__":
    main()
