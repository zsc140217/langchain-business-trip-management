"""
Layer 1: 短期记忆 (ChatMemory)
- 存储：文件持久化 (data/chat-history/{chat_id}.json)
- 容量：滑动窗口20条消息
- 用途：上下文理解
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


class ChatMemory:
    """基于文件的聊天记忆"""

    def __init__(self, chat_id: str, max_messages: int = 20, storage_dir: str = "data/chat-history"):
        self.chat_id = chat_id
        self.max_messages = max_messages
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, f"{chat_id}.json")

        # 确保存储目录存在
        Path(storage_dir).mkdir(parents=True, exist_ok=True)

        # 加载历史消息
        self.messages = self._load_messages()

    def _load_messages(self) -> List[Dict]:
        """从文件加载消息历史"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('messages', [])
            except Exception as e:
                print(f"加载消息历史失败: {e}")
                return []
        return []

    def _save_messages(self):
        """保存消息历史到文件"""
        try:
            data = {
                'chat_id': self.chat_id,
                'updated_at': datetime.now().isoformat(),
                'messages': self.messages
            }
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存消息历史失败: {e}")

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """添加消息（自动维护滑动窗口）"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        self.messages.append(message)

        # 维护滑动窗口
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

        self._save_messages()

    def add_user_message(self, content: str, metadata: Optional[Dict] = None):
        """添加用户消息"""
        self.add_message('user', content, metadata)

    def add_assistant_message(self, content: str, metadata: Optional[Dict] = None):
        """添加助手消息"""
        self.add_message('assistant', content, metadata)

    def get_messages(self, limit: Optional[int] = None) -> List[Dict]:
        """获取消息历史"""
        if limit:
            return self.messages[-limit:]
        return self.messages

    def get_context_string(self, limit: Optional[int] = None) -> str:
        """获取上下文字符串（用于提示词）"""
        messages = self.get_messages(limit)
        context_parts = []

        for msg in messages:
            role = "用户" if msg['role'] == 'user' else "助手"
            context_parts.append(f"{role}: {msg['content']}")

        return "\n".join(context_parts)

    def clear(self):
        """清空消息历史"""
        self.messages = []
        self._save_messages()

    def get_last_n_messages(self, n: int) -> List[Dict]:
        """获取最近N条消息"""
        return self.messages[-n:] if len(self.messages) >= n else self.messages

    def count_messages(self) -> int:
        """获取消息数量"""
        return len(self.messages)

    def delete_storage(self):
        """删除存储文件（GDPR合规）"""
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
            self.messages = []


if __name__ == "__main__":
    # 测试代码
    print("=== 测试短期记忆 ===")

    memory = ChatMemory("test_chat_001", max_messages=5)

    # 添加消息
    memory.add_user_message("我要去北京出差")
    memory.add_assistant_message("好的，请问您需要查询北京的天气吗？")
    memory.add_user_message("是的，还要推荐酒店")
    memory.add_assistant_message("北京明天晴天，推荐您入住希尔顿酒店")

    # 获取上下文
    print("\n上下文字符串:")
    print(memory.get_context_string())

    # 测试滑动窗口
    print(f"\n当前消息数: {memory.count_messages()}")
    for i in range(3):
        memory.add_user_message(f"测试消息 {i+1}")

    print(f"添加3条后消息数: {memory.count_messages()}")
    print("\n最终消息:")
    for msg in memory.get_messages():
        print(f"  {msg['role']}: {msg['content']}")

    # 清理测试数据
    memory.delete_storage()
    print("\n✅ 测试完成")
