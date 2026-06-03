"""
Summary Memory - 摘要记忆

实现对话历史的自动摘要，压缩长对话内容。
使用 ConversationSummaryMemory 生成和维护对话摘要。
"""

from typing import Dict, Any, Optional
from langchain.memory import ConversationSummaryMemory
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import os


class SummaryMemory:
    """摘要记忆 - 自动生成和维护对话摘要"""

    def __init__(
        self,
        llm: Optional[ChatTongyi] = None,
        memory_key: str = "history_summary",
        max_token_limit: int = 2000
    ):
        """
        初始化摘要记忆

        Args:
            llm: 用于生成摘要的语言模型
            memory_key: 内存键名
            max_token_limit: 最大token限制
        """
        self.memory_key = memory_key
        self.max_token_limit = max_token_limit

        # 初始化LLM
        if llm is None:
            api_key = os.getenv('DASHSCOPE_API_KEY')
            if not api_key:
                raise ValueError("DASHSCOPE_API_KEY not found in environment")

            self.llm = ChatTongyi(
                model="qwen-turbo",
                dashscope_api_key=api_key,
                temperature=0.3
            )
        else:
            self.llm = llm

        # 初始化摘要记忆
        self.memory = ConversationSummaryMemory(
            llm=self.llm,
            memory_key=memory_key,
            max_token_limit=max_token_limit
        )

    def add_message(self, role: str, content: str) -> None:
        """
        添加消息并更新摘要

        Args:
            role: 角色 ('human' 或 'ai')
            content: 消息内容
        """
        if role.lower() == 'human':
            self.memory.chat_memory.add_user_message(content)
        elif role.lower() == 'ai':
            self.memory.chat_memory.add_ai_message(content)

    def add_exchange(self, human_message: str, ai_message: str) -> None:
        """
        添加一次完整的对话交互

        Args:
            human_message: 用户消息
            ai_message: AI响应
        """
        self.add_message('human', human_message)
        self.add_message('ai', ai_message)

    def get_summary(self) -> str:
        """
        获取当前对话摘要

        Returns:
            摘要文本
        """
        variables = self.memory.load_memory_variables({})
        return variables.get(self.memory_key, "")

    def get_context(self) -> str:
        """
        获取摘要上下文（用于提示词）

        Returns:
            格式化的摘要文本
        """
        summary = self.get_summary()

        if not summary:
            return "暂无对话历史摘要。"

        return f"对话历史摘要：{summary}"

    def predict_new_summary(
        self,
        human_message: str,
        ai_message: str
    ) -> str:
        """
        预测添加新消息后的摘要（不实际添加）

        Args:
            human_message: 用户消息
            ai_message: AI响应

        Returns:
            预测的新摘要
        """
        current_summary = self.get_summary()

        # 构建预测提示
        prompt = f"""当前对话摘要：{current_summary}

新的对话：
用户：{human_message}
助手：{ai_message}

请更新对话摘要，保留关键信息并整合新内容："""

        response = self.llm.invoke(prompt)
        return response.content

    def clear(self) -> None:
        """清空摘要记忆"""
        self.memory.clear()

    def get_memory_variables(self) -> Dict[str, Any]:
        """
        获取记忆变量（用于LangChain集成）

        Returns:
            包含摘要的字典
        """
        return self.memory.load_memory_variables({})

    def to_dict(self) -> Dict[str, Any]:
        """
        导出为字典格式

        Returns:
            包含配置和摘要的字典
        """
        return {
            'memory_key': self.memory_key,
            'max_token_limit': self.max_token_limit,
            'summary': self.get_summary(),
            'message_count': len(self.memory.chat_memory.messages)
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        llm: Optional[ChatTongyi] = None
    ) -> 'SummaryMemory':
        """
        从字典创建实例

        Args:
            data: 字典数据
            llm: 语言模型实例

        Returns:
            SummaryMemory实例
        """
        instance = cls(
            llm=llm,
            memory_key=data.get('memory_key', 'history_summary'),
            max_token_limit=data.get('max_token_limit', 2000)
        )

        # 注意：摘要本身不能直接恢复，需要重新生成
        # 这里只能恢复配置

        return instance
