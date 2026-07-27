"""
Layer 3: 长期记忆 (LongTermMemoryManager)
- 存储：PostgreSQL数据库 (user_profiles表)
- 容量：无限制
- 用途：用户偏好学习、个性化推荐
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.user_profile_repository import UserProfileRepository


@dataclass
class UserProfile:
    """用户画像（数据类，用于内存表示）"""
    user_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 偏好统计
    preferred_cities: Dict[str, int] = field(default_factory=dict)  # 城市 -> 访问次数
    preferred_hotels: Dict[str, int] = field(default_factory=dict)  # 酒店 -> 预订次数
    frequent_customers: Dict[str, int] = field(default_factory=dict)  # 客户 -> 拜访次数

    # 行为模式
    common_intents: List[str] = field(default_factory=list)  # 常见意图
    conversation_count: int = 0  # 总会话数

    # 个性化设置
    preferences: Dict[str, str] = field(default_factory=dict)  # 自定义偏好


class LongTermMemoryManager:
    """长期记忆管理器（使用PostgreSQL存储）"""

    def __init__(self):
        """初始化长期记忆管理器（使用数据库）"""
        self.repository = UserProfileRepository()

    def load_profile(self, user_id: str) -> UserProfile:
        """
        加载用户画像

        Args:
            user_id: 用户ID

        Returns:
            用户画像对象
        """
        try:
            profile_dict = self.repository.find_by_user_id(user_id)

            if profile_dict:
                # 从数据库加载
                return UserProfile(
                    user_id=profile_dict["user_id"],
                    created_at=profile_dict["created_at"],
                    updated_at=profile_dict["updated_at"],
                    preferred_cities=profile_dict["preferred_cities"],
                    preferred_hotels=profile_dict["preferred_hotels"],
                    frequent_customers=profile_dict["frequent_customers"],
                    common_intents=profile_dict["common_intents"],
                    conversation_count=profile_dict["conversation_count"],
                    preferences=profile_dict["preferences"],
                )
            else:
                # 创建新画像
                new_profile = self.repository.create(user_id)
                return UserProfile(
                    user_id=new_profile["user_id"],
                    created_at=new_profile["created_at"],
                    updated_at=new_profile["updated_at"],
                    preferred_cities=new_profile["preferred_cities"],
                    preferred_hotels=new_profile["preferred_hotels"],
                    frequent_customers=new_profile["frequent_customers"],
                    common_intents=new_profile["common_intents"],
                    conversation_count=new_profile["conversation_count"],
                    preferences=new_profile["preferences"],
                )
        except Exception as e:
            print(f"加载用户画像失败: {e}")
            # 返回空画像（不写入数据库）
            return UserProfile(user_id=user_id)

    def learn_from_conversation(self, user_id: str, conversation_id: str, working_memory):
        """
        从工作记忆中学习，更新长期记忆（使用数据库原子操作）

        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            working_memory: 工作记忆对象
        """
        try:
            # 1. 更新城市偏好
            for city in working_memory.cities:
                self.repository.increment_city_count(user_id, city)

            # 2. 更新酒店偏好
            for hotel in working_memory.hotels:
                self.repository.increment_hotel_count(user_id, hotel)

            # 3. 更新客户拜访记录
            for customer in working_memory.customers:
                self.repository.increment_customer_count(user_id, customer)

            # 4. 更新意图统计
            if working_memory.current_intent:
                self.repository.add_intent(user_id, working_memory.current_intent)

            # 5. 增加会话计数
            self.repository.increment_conversation_count(user_id)

        except Exception as e:
            print(f"学习失败: {e}")

    def get_personalized_hint(self, user_id: str, current_city: Optional[str] = None) -> str:
        """
        生成个性化提示

        Args:
            user_id: 用户ID
            current_city: 当前查询的城市

        Returns:
            个性化提示字符串
        """
        profile = self.load_profile(user_id)
        hints = []

        # 1. 城市相关提示
        if current_city and current_city in profile.preferred_cities:
            visit_count = profile.preferred_cities[current_city]
            hints.append(f"您已经第{visit_count}次查询{current_city}的信息了")

            # 推荐常去的酒店
            if profile.preferred_hotels:
                top_hotel = max(profile.preferred_hotels.items(), key=lambda x: x[1])[0]
                hints.append(f"根据您的历史记录，推荐{top_hotel}")

        # 2. 客户相关提示
        if profile.frequent_customers:
            top_customers = sorted(
                profile.frequent_customers.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            customer_names = [c[0] for c in top_customers]
            hints.append(f"您经常拜访的客户: {', '.join(customer_names)}")

        # 3. 行为模式提示
        if profile.common_intents:
            hints.append(f"您常用的功能: {', '.join(profile.common_intents[:3])}")

        return "\n".join(hints)

    def get_top_cities(self, user_id: str, top_n: int = 5) -> List[tuple]:
        """
        获取用户最常去的城市

        Args:
            user_id: 用户ID
            top_n: 返回数量

        Returns:
            [(城市名, 访问次数), ...]
        """
        try:
            return self.repository.get_top_cities(user_id, top_n)
        except Exception as e:
            print(f"获取常去城市失败: {e}")
            return []

    def get_top_hotels(self, user_id: str, top_n: int = 5) -> List[tuple]:
        """
        获取用户最常预订的酒店

        Args:
            user_id: 用户ID
            top_n: 返回数量

        Returns:
            [(酒店名, 预订次数), ...]
        """
        try:
            return self.repository.get_top_hotels(user_id, top_n)
        except Exception as e:
            print(f"获取常订酒店失败: {e}")
            return []

    def set_preference(self, user_id: str, key: str, value: str):
        """
        设置用户偏好

        Args:
            user_id: 用户ID
            key: 偏好键
            value: 偏好值
        """
        try:
            self.repository.set_preference(user_id, key, value)
        except Exception as e:
            print(f"设置偏好失败: {e}")

    def get_preference(self, user_id: str, key: str) -> Optional[str]:
        """
        获取用户偏好

        Args:
            user_id: 用户ID
            key: 偏好键

        Returns:
            偏好值，不存在则返回None
        """
        try:
            return self.repository.get_preference(user_id, key)
        except Exception as e:
            print(f"获取偏好失败: {e}")
            return None

    def delete_user_data(self, user_id: str):
        """
        删除用户数据（GDPR合规）

        Args:
            user_id: 用户ID
        """
        try:
            if self.repository.delete(user_id):
                print(f"已删除用户 {user_id} 的数据")
            else:
                print(f"用户 {user_id} 的数据不存在")
        except Exception as e:
            print(f"删除用户数据失败: {e}")

    def get_user_stats(self, user_id: str) -> Dict:
        """
        获取用户统计信息

        Args:
            user_id: 用户ID

        Returns:
            用户统计信息字典
        """
        try:
            profile = self.load_profile(user_id)
            return {
                "user_id": profile.user_id,
                "conversation_count": profile.conversation_count,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
                "top_cities": self.get_top_cities(user_id, 3),
                "top_hotels": self.get_top_hotels(user_id, 3),
                "common_intents": profile.common_intents,
                "preferences": profile.preferences,
            }
        except Exception as e:
            print(f"获取用户统计失败: {e}")
            return {
                "user_id": user_id,
                "conversation_count": 0,
                "created_at": None,
                "updated_at": None,
                "top_cities": [],
                "top_hotels": [],
                "common_intents": [],
                "preferences": {},
            }


if __name__ == "__main__":
    # 测试代码
    print("=== 测试长期记忆（数据库版本） ===")

    manager = LongTermMemoryManager()

    # 模拟工作记忆
    from working_memory import WorkingMemory

    working_mem = WorkingMemory(conversation_id="test_conv_001")
    working_mem.add_city("北京")
    working_mem.add_city("上海")
    working_mem.add_hotel("希尔顿酒店")
    working_mem.add_customer("华为公司")
    working_mem.update_intent("查询天气")

    # 学习并更新长期记忆
    user_id = "test_user_db_001"
    manager.learn_from_conversation(user_id, "test_conv_001", working_mem)

    # 再次学习（模拟多次访问）
    working_mem2 = WorkingMemory(conversation_id="test_conv_002")
    working_mem2.add_city("北京")
    working_mem2.add_hotel("希尔顿酒店")
    working_mem2.add_customer("华为公司")
    working_mem2.update_intent("查询酒店")
    manager.learn_from_conversation(user_id, "test_conv_002", working_mem2)

    # 获取个性化提示
    print("\n=== 个性化提示 ===")
    hint = manager.get_personalized_hint(user_id, "北京")
    print(hint)

    # 获取统计信息
    print("\n=== 用户统计 ===")
    stats = manager.get_user_stats(user_id)
    print(f"会话总数: {stats['conversation_count']}")
    print(f"常去城市: {stats['top_cities']}")
    print(f"常订酒店: {stats['top_hotels']}")
    print(f"常用功能: {stats['common_intents']}")

    # 清理测试数据
    manager.delete_user_data(user_id)
    print("\n[OK] 测试完成")
