"""
记忆系统后端抽象接口
支持多种存储后端：文件、Redis、PostgreSQL
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Set
from datetime import datetime


class ShortTermBackend(ABC):
    """短期记忆后端抽象类"""

    @abstractmethod
    def add_message(self, chat_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """添加消息"""
        pass

    @abstractmethod
    def get_messages(self, chat_id: str, limit: Optional[int] = None) -> List[Dict]:
        """获取消息历史"""
        pass

    @abstractmethod
    def clear(self, chat_id: str):
        """清空消息历史"""
        pass

    @abstractmethod
    def delete_storage(self, chat_id: str):
        """删除存储"""
        pass


class WorkingMemoryBackend(ABC):
    """工作记忆后端抽象类"""

    @abstractmethod
    def save_entities(self, conversation_id: str, entities: Dict[str, Set[str]]):
        """保存实体"""
        pass

    @abstractmethod
    def get_entities(self, conversation_id: str) -> Dict[str, Set[str]]:
        """获取实体"""
        pass

    @abstractmethod
    def update_intent(self, conversation_id: str, intent: str):
        """更新意图"""
        pass

    @abstractmethod
    def get_intent(self, conversation_id: str) -> Optional[str]:
        """获取当前意图"""
        pass

    @abstractmethod
    def delete(self, conversation_id: str):
        """删除工作记忆"""
        pass


class LongTermBackend(ABC):
    """长期记忆后端抽象类"""

    @abstractmethod
    def save_profile(self, user_id: str, profile_data: Dict):
        """保存用户画像"""
        pass

    @abstractmethod
    def get_profile(self, user_id: str) -> Optional[Dict]:
        """获取用户画像"""
        pass

    @abstractmethod
    def update_preferences(self, user_id: str, key: str, increment: int = 1):
        """更新偏好统计（如城市访问次数）"""
        pass

    @abstractmethod
    def delete_profile(self, user_id: str):
        """删除用户画像"""
        pass

    @abstractmethod
    def save_query_history(self, user_id: str, thread_id: str, query: str, response: str):
        """保存查询历史"""
        pass

    @abstractmethod
    def get_query_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """获取查询历史"""
        pass
