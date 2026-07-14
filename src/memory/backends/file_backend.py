"""
文件存储后端 - 包装现有实现
默认后端，零依赖
"""

import json
import os
from typing import List, Dict, Optional, Set
from datetime import datetime
from pathlib import Path
from .base import ShortTermBackend, LongTermBackend


class FileShortTermBackend(ShortTermBackend):
    """文件存储的短期记忆后端"""

    def __init__(self, storage_dir: str = "data/chat-history"):
        self.storage_dir = storage_dir
        Path(storage_dir).mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, chat_id: str) -> str:
        return os.path.join(self.storage_dir, f"{chat_id}.json")

    def _load_messages(self, chat_id: str) -> List[Dict]:
        file_path = self._get_file_path(chat_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('messages', [])
            except Exception as e:
                print(f"加载消息失败: {e}")
        return []

    def _save_messages(self, chat_id: str, messages: List[Dict]):
        file_path = self._get_file_path(chat_id)
        try:
            data = {
                'chat_id': chat_id,
                'updated_at': datetime.now().isoformat(),
                'messages': messages
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存消息失败: {e}")

    def add_message(self, chat_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        messages = self._load_messages(chat_id)
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        messages.append(message)

        # 维持滑动窗口（最多20条）
        if len(messages) > 20:
            messages = messages[-20:]

        self._save_messages(chat_id, messages)

    def get_messages(self, chat_id: str, limit: Optional[int] = None) -> List[Dict]:
        messages = self._load_messages(chat_id)
        if limit:
            return messages[-limit:]
        return messages

    def clear(self, chat_id: str):
        self._save_messages(chat_id, [])

    def delete_storage(self, chat_id: str):
        file_path = self._get_file_path(chat_id)
        if os.path.exists(file_path):
            os.remove(file_path)


class FileLongTermBackend(LongTermBackend):
    """文件存储的长期记忆后端"""

    def __init__(self, storage_dir: str = "data/user-profiles"):
        self.storage_dir = storage_dir
        Path(storage_dir).mkdir(parents=True, exist_ok=True)

    def _get_profile_path(self, user_id: str) -> str:
        return os.path.join(self.storage_dir, f"{user_id}.json")

    def save_profile(self, user_id: str, profile_data: Dict):
        profile_path = self._get_profile_path(user_id)
        profile_data['updated_at'] = datetime.now().isoformat()
        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户画像失败: {e}")

    def get_profile(self, user_id: str) -> Optional[Dict]:
        profile_path = self._get_profile_path(user_id)
        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载用户画像失败: {e}")
        return None

    def update_preferences(self, user_id: str, key: str, increment: int = 1):
        profile = self.get_profile(user_id) or {
            'user_id': user_id,
            'created_at': datetime.now().isoformat()
        }

        # 这是一个通用方法，实际使用时需要指定字段路径
        # 这里简化处理，由上层调用者处理
        self.save_profile(user_id, profile)

    def delete_profile(self, user_id: str):
        profile_path = self._get_profile_path(user_id)
        if os.path.exists(profile_path):
            os.remove(profile_path)

    def save_query_history(self, user_id: str, thread_id: str, query: str, response: str):
        # 文件后端简化：不单独存储查询历史
        # 可以扩展为单独的history文件
        pass

    def get_query_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        # 文件后端简化：返回空列表
        return []
