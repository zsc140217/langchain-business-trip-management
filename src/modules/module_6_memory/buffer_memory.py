"""
Buffer Memory - 对话缓冲记忆

实现短期对话历史的缓冲管理，保留最近的对话轮次。
使用 ConversationBufferMemory 存储固定窗口的对话历史。
"""

from typing import List, Dict, Any, Optional
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class BufferMemory:
    """对话缓冲记忆 - 保存最近N轮对话"""

    def __init__(
        self,
        max_turns: int = 5,
        memory_key: str = "chat_history",
        return_messages: bool = True
    ):
        """
        初始化缓冲记忆

        Args:
            max_turns: 最大保留对话轮次
            memory_key: 内存键名
            return_messages: 是否返回消息对象
        """
        self.max_turns = max_turns
        self.memory_key = memory_key
        self.return_messages = return_messages

        self.memory = ConversationBufferMemory(
            memory_key=memory_key,
            return_messages=return_messages
        )
        self._turn_count = 0

    def add_message(self, role: str, content: str) -> None:
        """
        添加消息到缓冲区

        Args:
            role: 角色 ('human' 或 'ai')
            content: 消息内容
        """
        if role.lower() == 'human':
            self.memory.chat_memory.add_user_message(content)
        elif role.lower() == 'ai':
            self.memory.chat_memory.add_ai_message(content)
            self._turn_count += 1

        # 维持最大轮次限制
        self._enforce_max_turns()

    def add_exchange(self, human_message: str, ai_message: str) -> None:
        """
        添加一次完整的对话交互

        Args:
            human_message: 用户消息
            ai_message: AI响应
        """
        self.add_message('human', human_message)
        self.add_message('ai', ai_message)

    def _enforce_max_turns(self) -> None:
        """强制执行最大轮次限制"""
        messages = self.memory.chat_memory.messages

        # 每轮对话包含2条消息（human + ai）
        max_messages = self.max_turns * 2

        if len(messages) > max_messages:
            # 移除最早的消息对
            excess = len(messages) - max_messages
            self.memory.chat_memory.messages = messages[excess:]

    def get_messages(self) -> List[BaseMessage]:
        """
        获取所有缓冲的消息

        Returns:
            消息列表
        """
        return self.memory.chat_memory.messages

    def get_context(self) -> str:
        """
        获取格式化的对话上下文

        Returns:
            格式化的对话历史字符串
        """
        messages = self.get_messages()

        if not messages:
            return ""

        context_parts = []
        for msg in messages:
            role = "用户" if isinstance(msg, HumanMessage) else "助手"
            context_parts.append(f"{role}: {msg.content}")

        return "\n".join(context_parts)

    def get_memory_variables(self) -> Dict[str, Any]:
        """
        获取记忆变量（用于LangChain集成）

        Returns:
            包含记忆的字典
        """
        return self.memory.load_memory_variables({})

    def clear(self) -> None:
        """清空缓冲记忆"""
        self.memory.clear()
        self._turn_count = 0

    def get_turn_count(self) -> int:
        """
        获取当前对话轮次数

        Returns:
            轮次数
        """
        return self._turn_count

    def is_full(self) -> bool:
        """
        检查缓冲区是否已满

        Returns:
            是否已满
        """
        return self._turn_count >= self.max_turns

    def to_dict(self) -> Dict[str, Any]:
        """
        导出为字典格式

        Returns:
            包含配置和消息的字典
        """
        return {
            'max_turns': self.max_turns,
            'turn_count': self._turn_count,
            'messages': [
                {
                    'role': 'human' if isinstance(msg, HumanMessage) else 'ai',
                    'content': msg.content
                }
                for msg in self.get_messages()
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BufferMemory':
        """
        从字典创建实例

        Args:
            data: 字典数据

        Returns:
            BufferMemory实例
        """
        instance = cls(max_turns=data.get('max_turns', 5))

        # 恢复消息
        for msg in data.get('messages', []):
            instance.add_message(msg['role'], msg['content'])

        return instance
