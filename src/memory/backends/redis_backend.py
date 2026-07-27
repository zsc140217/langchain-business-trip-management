"""
Redis后端 - 短期记忆（对话历史）
需要安装: pip install redis
"""

import json
import redis
from typing import List, Dict, Optional
from datetime import datetime
from .base import ShortTermBackend


class RedisShortTermBackend(ShortTermBackend):
    """Redis存储的短期记忆后端"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", ttl: int = 86400):
        """
        Args:
            redis_url: Redis连接URL
            ttl: 消息过期时间（秒），默认24小时
        """
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self.client.ping()  # 测试连接
            self.ttl = ttl
            print("[OK] Redis连接成功")
        except Exception as e:
            raise ConnectionError(f"Redis连接失败: {e}")

    def _get_key(self, chat_id: str) -> str:
        return f"chat:history:{chat_id}"

    def add_message(self, chat_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        key = self._get_key(chat_id)
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        # 使用Redis列表存储消息
        self.client.lpush(key, json.dumps(message, ensure_ascii=False))

        # 维持滑动窗口（最多20条）
        self.client.ltrim(key, 0, 19)

        # 设置过期时间
        self.client.expire(key, self.ttl)

    def get_messages(self, chat_id: str, limit: Optional[int] = None) -> List[Dict]:
        key = self._get_key(chat_id)

        # 从Redis获取消息（逆序存储，所以需要反转）
        end = (limit - 1) if limit else -1
        messages_json = self.client.lrange(key, 0, end)

        # 解析并反转顺序（最新的在后面）
        messages = [json.loads(msg) for msg in reversed(messages_json)]
        return messages

    def clear(self, chat_id: str):
        key = self._get_key(chat_id)
        self.client.delete(key)

    def delete_storage(self, chat_id: str):
        self.clear(chat_id)

    def get_all_chat_ids(self) -> List[str]:
        """获取所有聊天ID（调试用）"""
        keys = self.client.keys("chat:history:*")
        return [key.replace("chat:history:", "") for key in keys]

    def get_stats(self) -> Dict:
        """获取统计信息"""
        all_keys = self.client.keys("chat:history:*")
        return {
            "total_chats": len(all_keys),
            "backend": "redis",
            "ttl": self.ttl
        }


if __name__ == "__main__":
    # 测试代码
    print("=== 测试Redis短期记忆后端 ===")

    try:
        backend = RedisShortTermBackend()

        # 添加消息
        backend.add_message("test_chat_001", "user", "我要去北京出差")
        backend.add_message("test_chat_001", "assistant", "好的，请问您需要查询什么？")
        backend.add_message("test_chat_001", "user", "查询天气")

        # 获取消息
        messages = backend.get_messages("test_chat_001")
        print(f"\n获取到 {len(messages)} 条消息:")
        for msg in messages:
            print(f"  {msg['role']}: {msg['content']}")

        # 获取统计
        stats = backend.get_stats()
        print(f"\n统计信息: {stats}")

        # 清理
        backend.clear("test_chat_001")
        print("\n[OK] 测试完成")

    except ConnectionError as e:
        print(f"[WARNING] {e}")
        print("提示：请先启动Redis服务器")
