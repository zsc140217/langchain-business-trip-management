"""
MemoryService统一门面
整合三层记忆系统，提供统一的API接口
"""

from typing import Optional
from .chat_memory import ChatMemory
from .working_memory import WorkingMemoryManager
from .long_term_memory import LongTermMemoryManager


class MemoryService:
    """记忆服务统一门面"""

    def __init__(
        self,
        chat_memory_max_messages: int = 20,
        working_memory_ttl_minutes: int = 30,
        chat_storage_dir: str = "data/chat-history",
        profile_storage_dir: str = "data/user-profiles"
    ):
        # Layer 1: 短期记忆
        self.chat_storage_dir = chat_storage_dir
        self.chat_memory_max_messages = chat_memory_max_messages
        self._chat_memories = {}  # conversation_id -> ChatMemory

        # Layer 2: 工作记忆
        self.working_memory_manager = WorkingMemoryManager(ttl_minutes=working_memory_ttl_minutes)

        # Layer 3: 长期记忆
        self.long_term_memory_manager = LongTermMemoryManager(storage_dir=profile_storage_dir)

    def get_chat_memory(self, conversation_id: str) -> ChatMemory:
        """获取或创建短期记忆"""
        if conversation_id not in self._chat_memories:
            self._chat_memories[conversation_id] = ChatMemory(
                chat_id=conversation_id,
                max_messages=self.chat_memory_max_messages,
                storage_dir=self.chat_storage_dir
            )
        return self._chat_memories[conversation_id]

    def process_user_message(self, user_id: str, conversation_id: str, user_message: str):
        """
        处理用户消息，更新三层记忆

        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            user_message: 用户消息内容
        """
        # Layer 1: 添加到短期记忆
        chat_memory = self.get_chat_memory(conversation_id)
        chat_memory.add_user_message(user_message)

        # Layer 2: 提取实体和意图到工作记忆
        self.working_memory_manager.extract_and_update(conversation_id, user_message)

    def process_assistant_message(self, conversation_id: str, assistant_message: str):
        """
        处理助手消息，添加到短期记忆

        Args:
            conversation_id: 会话ID
            assistant_message: 助手消息内容
        """
        # Layer 1: 添加到短期记忆
        chat_memory = self.get_chat_memory(conversation_id)
        chat_memory.add_assistant_message(assistant_message)

    def build_enhanced_prompt(
        self,
        user_id: str,
        conversation_id: str,
        current_city: Optional[str] = None,
        include_chat_history: bool = True,
        chat_history_limit: int = 10
    ) -> str:
        """
        生成增强的系统提示

        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            current_city: 当前查询的城市
            include_chat_history: 是否包含聊天历史
            chat_history_limit: 聊天历史条数限制

        Returns:
            增强的提示词字符串
        """
        prompt_parts = []

        # 1. 添加聊天历史（Layer 1）
        if include_chat_history:
            chat_memory = self.get_chat_memory(conversation_id)
            chat_history = chat_memory.get_context_string(limit=chat_history_limit)
            if chat_history:
                prompt_parts.append("【对话历史】")
                prompt_parts.append(chat_history)
                prompt_parts.append("")

        # 2. 添加工作记忆的上下文摘要（Layer 2）
        context_summary = self.working_memory_manager.get_context_summary(conversation_id)
        if context_summary:
            prompt_parts.append(context_summary)

        # 3. 添加长期记忆的个性化提示（Layer 3）
        if current_city:
            personalized_hint = self.long_term_memory_manager.get_personalized_hint(user_id, current_city)
            if personalized_hint:
                prompt_parts.append("【个性化提示】")
                prompt_parts.append(personalized_hint)
                prompt_parts.append("")

        return "\n".join(prompt_parts)

    def end_conversation(self, user_id: str, conversation_id: str):
        """
        会话结束时的学习流程
        从工作记忆中提取信息，更新长期记忆

        Args:
            user_id: 用户ID
            conversation_id: 会话ID
        """
        # 从工作记忆学习并更新长期记忆
        working_memory = self.working_memory_manager.get_or_create(conversation_id)
        self.long_term_memory_manager.learn_from_conversation(user_id, conversation_id, working_memory)

        # 可选：清理工作记忆
        # self.working_memory_manager.delete(conversation_id)

    def cleanup_expired_working_memory(self):
        """清理过期的工作记忆"""
        self.working_memory_manager.cleanup_expired()

    def delete_user_data(self, user_id: str):
        """
        删除用户所有数据（GDPR合规）

        Args:
            user_id: 用户ID
        """
        # 删除长期记忆
        self.long_term_memory_manager.delete_user_data(user_id)

        # 注意：短期记忆和工作记忆按conversation_id存储
        # 如果需要删除特定用户的所有会话，需要额外的映射关系

    def get_user_stats(self, user_id: str) -> dict:
        """
        获取用户统计信息

        Args:
            user_id: 用户ID

        Returns:
            用户统计信息字典
        """
        return self.long_term_memory_manager.get_user_stats(user_id)

    def get_memory_stats(self) -> dict:
        """
        获取整体记忆系统统计信息

        Returns:
            记忆系统统计信息字典
        """
        return {
            "chat_memories": len(self._chat_memories),
            "working_memories": self.working_memory_manager.get_memory_stats(),
        }


if __name__ == "__main__":
    # 测试代码
    print("=== 测试记忆服务 ===")

    service = MemoryService()

    user_id = "test_user_001"
    conv_id = "test_conv_001"

    # 模拟对话流程
    print("\n1. 处理用户消息")
    service.process_user_message(user_id, conv_id, "我要去北京出差，拜访华为公司")
    service.process_assistant_message(conv_id, "好的，请问您需要查询北京的天气吗？")

    service.process_user_message(user_id, conv_id, "是的，还要推荐希尔顿酒店")
    service.process_assistant_message(conv_id, "北京明天晴天，推荐您入住希尔顿酒店")

    # 生成增强提示
    print("\n2. 生成增强提示")
    enhanced_prompt = service.build_enhanced_prompt(user_id, conv_id, current_city="北京")
    print(enhanced_prompt)

    # 结束会话并学习
    print("\n3. 结束会话并学习")
    service.end_conversation(user_id, conv_id)

    # 模拟第二次对话
    print("\n4. 第二次对话（测试个性化）")
    conv_id_2 = "test_conv_002"
    service.process_user_message(user_id, conv_id_2, "我又要去北京了")

    enhanced_prompt_2 = service.build_enhanced_prompt(user_id, conv_id_2, current_city="北京")
    print(enhanced_prompt_2)

    # 获取统计信息
    print("\n5. 统计信息")
    user_stats = service.get_user_stats(user_id)
    print(f"用户会话数: {user_stats['conversation_count']}")
    print(f"常去城市: {user_stats['top_cities']}")

    memory_stats = service.get_memory_stats()
    print(f"活跃会话数: {memory_stats['chat_memories']}")
    print(f"工作记忆数: {memory_stats['working_memories']['total_conversations']}")

    # 清理测试数据
    service.delete_user_data(user_id)
    print("\n✅ 测试完成")
