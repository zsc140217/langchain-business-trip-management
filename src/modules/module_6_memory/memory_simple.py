"""
简化版 Memory 实现 - 不依赖已弃用的 langchain.memory
"""
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class SimpleBufferMemory:
    """简单的对话缓冲记忆"""
    
    def __init__(self, max_turns: int = 5):
        self.messages: List[BaseMessage] = []
        self.max_turns = max_turns
    
    def add_user_message(self, message: str):
        self.messages.append(HumanMessage(content=message))
        self._trim()
    
    def add_ai_message(self, message: str):
        self.messages.append(AIMessage(content=message))
        self._trim()
    
    def _trim(self):
        if len(self.messages) > self.max_turns * 2:
            self.messages = self.messages[-(self.max_turns * 2):]
    
    def get_messages(self) -> List[BaseMessage]:
        return self.messages


# 兼容接口
BufferMemory = SimpleBufferMemory
