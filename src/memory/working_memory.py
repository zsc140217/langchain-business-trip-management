"""
Layer 2: 工作记忆 (WorkingMemoryManager)
- 存储：内存 (dict)
- 容量：30分钟TTL自动清理
- 用途：实体提取、意图追踪
"""

import re
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class WorkingMemory:
    """工作记忆数据结构"""
    conversation_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)

    # 实体提取
    cities: Set[str] = field(default_factory=set)
    customers: Set[str] = field(default_factory=set)
    dates: Set[str] = field(default_factory=set)
    hotels: Set[str] = field(default_factory=set)

    # 意图追踪
    current_intent: Optional[str] = None
    intent_history: List[str] = field(default_factory=list)

    # 上下文摘要
    context_summary: str = ""

    def update_access_time(self):
        """更新最后访问时间"""
        self.last_accessed = datetime.now()

    def add_city(self, city: str):
        """添加城市实体"""
        self.cities.add(city)
        self.update_access_time()

    def add_customer(self, customer: str):
        """添加客户实体"""
        self.customers.add(customer)
        self.update_access_time()

    def add_date(self, date: str):
        """添加日期实体"""
        self.dates.add(date)
        self.update_access_time()

    def add_hotel(self, hotel: str):
        """添加酒店实体"""
        self.hotels.add(hotel)
        self.update_access_time()

    def update_intent(self, intent: str):
        """更新意图"""
        if self.current_intent != intent:
            if self.current_intent:
                self.intent_history.append(self.current_intent)
            self.current_intent = intent
        self.update_access_time()

    def get_summary(self) -> str:
        """生成上下文摘要"""
        parts = []

        if self.cities:
            parts.append(f"涉及城市: {', '.join(self.cities)}")

        if self.customers:
            parts.append(f"客户: {', '.join(self.customers)}")

        if self.dates:
            parts.append(f"日期: {', '.join(self.dates)}")

        if self.hotels:
            parts.append(f"酒店: {', '.join(self.hotels)}")

        if self.current_intent:
            parts.append(f"当前意图: {self.current_intent}")

        return "\n".join(parts) if parts else ""

    def is_expired(self, ttl_minutes: int = 30) -> bool:
        """检查是否过期"""
        expiry_time = self.last_accessed + timedelta(minutes=ttl_minutes)
        return datetime.now() > expiry_time


class WorkingMemoryManager:
    """工作记忆管理器"""

    def __init__(self, ttl_minutes: int = 30):
        self.ttl_minutes = ttl_minutes
        self.memory_store: Dict[str, WorkingMemory] = {}
        self.lock = Lock()

        # 实体识别规则
        self.city_keywords = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "西安", "南京", "武汉"]
        self.intent_patterns = {
            "查询天气": ["天气", "气温", "下雨", "晴天", "阴天"],
            "查询酒店": ["酒店", "住宿", "入住", "预订"],
            "查询航班": ["航班", "机票", "飞机", "起飞"],
            "查询政策": ["政策", "规定", "标准", "报销"],
            "行程规划": ["行程", "安排", "计划", "日程"],
        }

    def get_or_create(self, conversation_id: str) -> WorkingMemory:
        """获取或创建工作记忆"""
        with self.lock:
            if conversation_id not in self.memory_store:
                self.memory_store[conversation_id] = WorkingMemory(conversation_id=conversation_id)

            memory = self.memory_store[conversation_id]
            memory.update_access_time()
            return memory

    def extract_and_update(self, conversation_id: str, user_message: str):
        """从用户消息中提取实体和意图"""
        memory = self.get_or_create(conversation_id)

        # 1. 提取城市实体
        for city in self.city_keywords:
            if city in user_message:
                memory.add_city(city)

        # 2. 提取客户实体
        customer_patterns = [
            r'(\w+公司)',
            r'(\w+客户)',
            r'拜访(\w+)',
        ]
        for pattern in customer_patterns:
            matches = re.findall(pattern, user_message)
            for match in matches:
                memory.add_customer(match)

        # 3. 提取日期实体
        date_patterns = [
            r'(\d+月\d+日)',
            r'(明天|后天|下周)',
            r'(\d{4}-\d{2}-\d{2})',
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, user_message)
            for match in matches:
                memory.add_date(match)

        # 4. 提取酒店实体
        hotel_patterns = [
            r'(\w+酒店)',
            r'(\w+宾馆)',
        ]
        for pattern in hotel_patterns:
            matches = re.findall(pattern, user_message)
            for match in matches:
                memory.add_hotel(match)

        # 5. 识别意图
        for intent, keywords in self.intent_patterns.items():
            if any(keyword in user_message for keyword in keywords):
                memory.update_intent(intent)
                break

    def get_context_summary(self, conversation_id: str) -> str:
        """获取上下文摘要"""
        if conversation_id in self.memory_store:
            memory = self.memory_store[conversation_id]
            summary = memory.get_summary()
            if summary:
                return f"【当前对话上下文】\n{summary}\n"
        return ""

    def cleanup_expired(self):
        """清理过期的工作记忆"""
        with self.lock:
            expired_ids = [
                conv_id for conv_id, memory in self.memory_store.items()
                if memory.is_expired(self.ttl_minutes)
            ]

            for conv_id in expired_ids:
                del self.memory_store[conv_id]

            if expired_ids:
                print(f"清理了 {len(expired_ids)} 个过期的工作记忆")

    def delete(self, conversation_id: str):
        """删除指定的工作记忆"""
        with self.lock:
            if conversation_id in self.memory_store:
                del self.memory_store[conversation_id]

    def get_all_conversations(self) -> List[str]:
        """获取所有会话ID"""
        return list(self.memory_store.keys())

    def get_memory_stats(self) -> Dict:
        """获取内存统计信息"""
        return {
            "total_conversations": len(self.memory_store),
            "ttl_minutes": self.ttl_minutes,
            "conversations": [
                {
                    "id": conv_id,
                    "created_at": memory.created_at.isoformat(),
                    "last_accessed": memory.last_accessed.isoformat(),
                    "entities": {
                        "cities": len(memory.cities),
                        "customers": len(memory.customers),
                        "dates": len(memory.dates),
                        "hotels": len(memory.hotels),
                    },
                    "current_intent": memory.current_intent,
                }
                for conv_id, memory in self.memory_store.items()
            ]
        }


if __name__ == "__main__":
    # 测试代码
    print("=== 测试工作记忆 ===")

    manager = WorkingMemoryManager(ttl_minutes=30)

    # 测试实体提取
    test_messages = [
        "我要去北京出差，拜访华为公司",
        "明天的天气怎么样？",
        "帮我推荐一下希尔顿酒店",
        "查询一下差旅政策",
    ]

    conv_id = "test_conv_001"

    for msg in test_messages:
        print(f"\n用户消息: {msg}")
        manager.extract_and_update(conv_id, msg)
        print(manager.get_context_summary(conv_id))

    # 测试统计信息
    print("\n=== 内存统计 ===")
    stats = manager.get_memory_stats()
    print(f"总会话数: {stats['total_conversations']}")
    for conv in stats['conversations']:
        print(f"\n会话ID: {conv['id']}")
        print(f"  实体数: {conv['entities']}")
        print(f"  当前意图: {conv['current_intent']}")

    print("\n✅ 测试完成")
