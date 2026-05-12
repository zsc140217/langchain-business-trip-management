"""
三层记忆系统测试
测试短期记忆、工作记忆、长期记忆的集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory import MemoryService


def test_basic_flow():
    """测试基本流程"""
    print("=== 测试1: 基本流程 ===")

    service = MemoryService()
    user_id = "user_001"
    conv_id = "conv_001"

    # 模拟对话
    messages = [
        ("user", "我要去北京出差"),
        ("assistant", "好的，请问您需要什么帮助？"),
        ("user", "查询一下天气，还要推荐希尔顿酒店"),
        ("assistant", "北京明天晴天，推荐您入住希尔顿酒店"),
    ]

    for role, content in messages:
        if role == "user":
            service.process_user_message(user_id, conv_id, content)
        else:
            service.process_assistant_message(conv_id, content)

    # 生成增强提示
    prompt = service.build_enhanced_prompt(user_id, conv_id, current_city="北京")
    print("\n增强提示:")
    print(prompt)

    # 结束会话
    service.end_conversation(user_id, conv_id)

    print("[OK] 测试1通过\n")


def test_personalization():
    """测试个性化推荐"""
    print("=== 测试2: 个性化推荐 ===")

    service = MemoryService()
    user_id = "user_002"

    # 第一次对话
    conv_id_1 = "conv_001"
    service.process_user_message(user_id, conv_id_1, "我要去上海出差，拜访阿里巴巴")
    service.process_user_message(user_id, conv_id_1, "推荐一下万豪酒店")
    service.end_conversation(user_id, conv_id_1)

    # 第二次对话
    conv_id_2 = "conv_002"
    service.process_user_message(user_id, conv_id_2, "我又要去上海了")
    service.end_conversation(user_id, conv_id_2)

    # 第三次对话（测试个性化）
    conv_id_3 = "conv_003"
    service.process_user_message(user_id, conv_id_3, "查询上海的天气")

    prompt = service.build_enhanced_prompt(user_id, conv_id_3, current_city="上海")
    print("\n个性化提示:")
    print(prompt)

    # 检查是否包含个性化信息
    assert "第3次" in prompt or "阿里巴巴" in prompt or "万豪酒店" in prompt

    print("[OK] 测试2通过\n")


def test_working_memory_extraction():
    """测试工作记忆实体提取"""
    print("=== 测试3: 工作记忆实体提取 ===")

    service = MemoryService()
    conv_id = "conv_001"

    # 测试实体提取
    service.process_user_message("user_003", conv_id, "我要去北京、上海、深圳出差")
    service.process_user_message("user_003", conv_id, "拜访华为公司和腾讯公司")
    service.process_user_message("user_003", conv_id, "明天的天气怎么样？")

    # 获取工作记忆
    working_memory = service.working_memory_manager.get_or_create(conv_id)

    print(f"提取的城市: {working_memory.cities}")
    print(f"提取的客户: {working_memory.customers}")
    print(f"当前意图: {working_memory.current_intent}")

    # 验证提取结果
    assert "北京" in working_memory.cities
    assert "上海" in working_memory.cities
    assert "深圳" in working_memory.cities
    assert working_memory.current_intent == "查询天气"

    print("[OK] 测试3通过\n")


def test_sliding_window():
    """测试短期记忆滑动窗口"""
    print("=== 测试4: 滑动窗口 ===")

    service = MemoryService(chat_memory_max_messages=5)
    conv_id = "conv_001"

    # 添加10条消息
    for i in range(10):
        service.process_user_message("user_004", conv_id, f"消息 {i+1}")

    # 获取短期记忆
    chat_memory = service.get_chat_memory(conv_id)
    messages = chat_memory.get_messages()

    print(f"消息总数: {len(messages)}")
    print(f"最早消息: {messages[0]['content']}")
    print(f"最新消息: {messages[-1]['content']}")

    # 验证滑动窗口
    assert len(messages) == 5
    assert "消息 6" in messages[0]['content']
    assert "消息 10" in messages[-1]['content']

    print("[OK] 测试4通过\n")


def test_memory_stats():
    """测试统计信息"""
    print("=== 测试5: 统计信息 ===")

    service = MemoryService()
    user_id = "user_005"

    # 创建多个会话
    for i in range(3):
        conv_id = f"conv_{i+1}"
        service.process_user_message(user_id, conv_id, f"去北京出差 {i+1}")
        service.process_user_message(user_id, conv_id, "推荐希尔顿酒店")
        service.end_conversation(user_id, conv_id)

    # 获取统计信息
    user_stats = service.get_user_stats(user_id)
    memory_stats = service.get_memory_stats()

    print(f"用户会话数: {user_stats['conversation_count']}")
    print(f"常去城市: {user_stats['top_cities']}")
    print(f"活跃会话数: {memory_stats['chat_memories']}")
    print(f"工作记忆数: {memory_stats['working_memories']['total_conversations']}")

    # 验证统计
    assert user_stats['conversation_count'] == 3
    assert len(user_stats['top_cities']) > 0

    print("[OK] 测试5通过\n")


def test_gdpr_compliance():
    """测试GDPR合规（数据删除）"""
    print("=== 测试6: GDPR合规 ===")

    service = MemoryService()
    user_id = "user_006"
    conv_id = "conv_001"

    # 创建用户数据
    service.process_user_message(user_id, conv_id, "测试消息")
    service.end_conversation(user_id, conv_id)

    # 验证数据存在
    stats_before = service.get_user_stats(user_id)
    print(f"删除前会话数: {stats_before['conversation_count']}")

    # 删除用户数据
    service.delete_user_data(user_id)

    # 验证数据已删除
    stats_after = service.get_user_stats(user_id)
    print(f"删除后会话数: {stats_after['conversation_count']}")

    assert stats_after['conversation_count'] == 0

    print("[OK] 测试6通过\n")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("三层记忆系统测试套件")
    print("=" * 60)

    try:
        test_basic_flow()
        test_personalization()
        test_working_memory_extraction()
        test_sliding_window()
        test_memory_stats()
        test_gdpr_compliance()

        print("=" * 60)
        print("[SUCCESS] 所有测试通过！")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
