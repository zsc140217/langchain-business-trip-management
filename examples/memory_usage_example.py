"""
三层记忆系统使用示例
演示如何在实际应用中使用记忆系统
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory import MemoryService


def example_1_basic_conversation():
    """示例1：基本对话流程"""
    print("=" * 60)
    print("示例1：基本对话流程")
    print("=" * 60)

    service = MemoryService()
    user_id = "alice"
    conv_id = "conv_001"

    # 模拟对话
    print("\n[用户] 我要去北京出差")
    service.process_user_message(user_id, conv_id, "我要去北京出差")

    print("[助手] 好的，请问您需要什么帮助？")
    service.process_assistant_message(conv_id, "好的，请问您需要什么帮助？")

    print("[用户] 查询一下天气，还要推荐酒店")
    service.process_user_message(user_id, conv_id, "查询一下天气，还要推荐酒店")

    # 生成增强提示
    print("\n--- 增强提示 ---")
    prompt = service.build_enhanced_prompt(user_id, conv_id, current_city="北京")
    print(prompt)

    # 结束会话
    service.end_conversation(user_id, conv_id)
    print("\n[系统] 会话已结束，已学习用户偏好")


def example_2_personalization():
    """示例2：个性化推荐"""
    print("\n" + "=" * 60)
    print("示例2：个性化推荐")
    print("=" * 60)

    service = MemoryService()
    user_id = "bob"

    # 第一次对话
    print("\n--- 第1次对话 ---")
    conv_id_1 = "conv_001"
    service.process_user_message(user_id, conv_id_1, "我要去上海出差，拜访阿里巴巴")
    service.process_user_message(user_id, conv_id_1, "推荐一下万豪酒店")
    service.end_conversation(user_id, conv_id_1)

    # 第二次对话
    print("\n--- 第2次对话 ---")
    conv_id_2 = "conv_002"
    service.process_user_message(user_id, conv_id_2, "我又要去上海了")
    service.end_conversation(user_id, conv_id_2)

    # 第三次对话（展示个性化）
    print("\n--- 第3次对话（个性化推荐）---")
    conv_id_3 = "conv_003"
    service.process_user_message(user_id, conv_id_3, "查询上海的天气")

    prompt = service.build_enhanced_prompt(user_id, conv_id_3, current_city="上海")
    print(prompt)

    # 查看用户统计
    print("\n--- 用户统计 ---")
    stats = service.get_user_stats(user_id)
    print(f"会话总数: {stats['conversation_count']}")
    print(f"常去城市: {stats['top_cities']}")
    print(f"常订酒店: {stats['top_hotels']}")


def example_3_entity_extraction():
    """示例3：实体提取和意图识别"""
    print("\n" + "=" * 60)
    print("示例3：实体提取和意图识别")
    print("=" * 60)

    service = MemoryService()
    conv_id = "conv_001"

    # 测试各种实体提取
    test_messages = [
        "我要去北京、上海、深圳出差",
        "拜访华为公司和腾讯公司",
        "明天的天气怎么样？",
        "推荐一下希尔顿酒店和万豪酒店",
    ]

    for msg in test_messages:
        print(f"\n[用户] {msg}")
        service.process_user_message("user_001", conv_id, msg)

    # 查看提取结果
    working_memory = service.working_memory_manager.get_or_create(conv_id)
    print("\n--- 提取结果 ---")
    print(f"城市: {working_memory.cities}")
    print(f"客户: {working_memory.customers}")
    print(f"酒店: {working_memory.hotels}")
    print(f"日期: {working_memory.dates}")
    print(f"当前意图: {working_memory.current_intent}")


def example_4_context_window():
    """示例4：滑动窗口机制"""
    print("\n" + "=" * 60)
    print("示例4：滑动窗口机制")
    print("=" * 60)

    # 设置较小的窗口用于演示
    service = MemoryService(chat_memory_max_messages=5)
    conv_id = "conv_001"

    # 添加10条消息
    print("\n添加10条消息...")
    for i in range(10):
        service.process_user_message("user_001", conv_id, f"消息 {i+1}")

    # 查看保留的消息
    chat_memory = service.get_chat_memory(conv_id)
    messages = chat_memory.get_messages()

    print(f"\n窗口大小: 5")
    print(f"实际保留: {len(messages)} 条")
    print(f"最早消息: {messages[0]['content']}")
    print(f"最新消息: {messages[-1]['content']}")


def example_5_multi_user():
    """示例5：多用户场景"""
    print("\n" + "=" * 60)
    print("示例5：多用户场景")
    print("=" * 60)

    service = MemoryService()

    # 用户A的对话
    print("\n--- 用户A ---")
    service.process_user_message("alice", "conv_a1", "我要去北京")
    service.process_user_message("alice", "conv_a1", "推荐希尔顿酒店")
    service.end_conversation("alice", "conv_a1")

    # 用户B的对话
    print("\n--- 用户B ---")
    service.process_user_message("bob", "conv_b1", "我要去上海")
    service.process_user_message("bob", "conv_b1", "推荐万豪酒店")
    service.end_conversation("bob", "conv_b1")

    # 查看各自的统计
    print("\n--- 用户A统计 ---")
    stats_a = service.get_user_stats("alice")
    print(f"常去城市: {stats_a['top_cities']}")
    print(f"常订酒店: {stats_a['top_hotels']}")

    print("\n--- 用户B统计 ---")
    stats_b = service.get_user_stats("bob")
    print(f"常去城市: {stats_b['top_cities']}")
    print(f"常订酒店: {stats_b['top_hotels']}")


def example_6_memory_cleanup():
    """示例6：记忆清理"""
    print("\n" + "=" * 60)
    print("示例6：记忆清理")
    print("=" * 60)

    service = MemoryService(working_memory_ttl_minutes=30)

    # 创建多个会话
    for i in range(5):
        conv_id = f"conv_{i+1}"
        service.process_user_message("user_001", conv_id, f"测试消息 {i+1}")

    # 查看统计
    stats_before = service.get_memory_stats()
    print(f"\n清理前工作记忆数: {stats_before['working_memories']['total_conversations']}")

    # 清理过期记忆（实际场景中会根据TTL自动清理）
    service.cleanup_expired_working_memory()

    stats_after = service.get_memory_stats()
    print(f"清理后工作记忆数: {stats_after['working_memories']['total_conversations']}")


def example_7_gdpr_compliance():
    """示例7：GDPR合规（数据删除）"""
    print("\n" + "=" * 60)
    print("示例7：GDPR合规（数据删除）")
    print("=" * 60)

    service = MemoryService()
    user_id = "charlie"

    # 创建用户数据
    print("\n创建用户数据...")
    service.process_user_message(user_id, "conv_001", "我要去北京")
    service.end_conversation(user_id, "conv_001")

    # 查看数据
    stats_before = service.get_user_stats(user_id)
    print(f"删除前会话数: {stats_before['conversation_count']}")

    # 删除用户数据
    print("\n删除用户数据...")
    service.delete_user_data(user_id)

    # 验证删除
    stats_after = service.get_user_stats(user_id)
    print(f"删除后会话数: {stats_after['conversation_count']}")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("三层记忆系统使用示例")
    print("=" * 60)

    example_1_basic_conversation()
    example_2_personalization()
    example_3_entity_extraction()
    example_4_context_window()
    example_5_multi_user()
    example_6_memory_cleanup()
    example_7_gdpr_compliance()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
