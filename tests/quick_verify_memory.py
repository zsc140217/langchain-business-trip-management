"""
三层记忆系统快速验证脚本
验证所有核心功能是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory import MemoryService


def quick_test():
    """快速功能验证"""
    print("=" * 60)
    print("三层记忆系统快速验证")
    print("=" * 60)

    service = MemoryService()
    user_id = "test_user"
    conv_id = "test_conv"

    # 1. 测试消息处理
    print("\n[1/7] 测试消息处理...")
    service.process_user_message(user_id, conv_id, "我要去北京出差，拜访华为公司")
    service.process_assistant_message(conv_id, "好的，请问您需要什么帮助？")
    print("[OK] 消息处理正常")

    # 2. 测试实体提取
    print("\n[2/7] 测试实体提取...")
    working_memory = service.working_memory_manager.get_or_create(conv_id)
    assert "北京" in working_memory.cities
    assert len(working_memory.customers) > 0
    print(f"[OK] 实体提取正常 (城市: {working_memory.cities})")

    # 3. 测试增强提示
    print("\n[3/7] 测试增强提示生成...")
    prompt = service.build_enhanced_prompt(user_id, conv_id, current_city="北京")
    assert len(prompt) > 0
    print("[OK] 增强提示生成正常")

    # 4. 测试会话学习
    print("\n[4/7] 测试会话学习...")
    service.end_conversation(user_id, conv_id)
    stats = service.get_user_stats(user_id)
    assert stats['conversation_count'] == 1
    print(f"[OK] 会话学习正常 (会话数: {stats['conversation_count']})")

    # 5. 测试个性化推荐
    print("\n[5/7] 测试个性化推荐...")
    conv_id_2 = "test_conv_2"
    service.process_user_message(user_id, conv_id_2, "又要去北京了")
    service.end_conversation(user_id, conv_id_2)
    hint = service.long_term_memory_manager.get_personalized_hint(user_id, "北京")
    assert "第2次" in hint or "北京" in hint
    print("[OK] 个性化推荐正常")

    # 6. 测试统计信息
    print("\n[6/7] 测试统计信息...")
    memory_stats = service.get_memory_stats()
    assert memory_stats['chat_memories'] > 0
    print(f"[OK] 统计信息正常 (活跃会话: {memory_stats['chat_memories']})")

    # 7. 测试数据删除
    print("\n[7/7] 测试GDPR合规...")
    service.delete_user_data(user_id)
    stats_after = service.get_user_stats(user_id)
    assert stats_after['conversation_count'] == 0
    print("[OK] 数据删除正常")

    print("\n" + "=" * 60)
    print("[SUCCESS] 所有功能验证通过！")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = quick_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
