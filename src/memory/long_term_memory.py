"""
Layer 3: 长期记忆 (LongTermMemoryManager)
- 存储：JSON文件 (data/user-profiles/{user_id}.json)
- 容量：无限制
- 用途：用户偏好学习、个性化推荐
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from collections import Counter
from dataclasses import dataclass, field, asdict


@dataclass
class UserProfile:
    """用户画像"""
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
    """长期记忆管理器"""

    def __init__(self, storage_dir: str = "data/user-profiles"):
        self.storage_dir = storage_dir
        Path(storage_dir).mkdir(parents=True, exist_ok=True)

    def _get_profile_path(self, user_id: str) -> str:
        """获取用户画像文件路径"""
        return os.path.join(self.storage_dir, f"{user_id}.json")

    def load_profile(self, user_id: str) -> UserProfile:
        """加载用户画像"""
        profile_path = self._get_profile_path(user_id)

        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return UserProfile(**data)
            except Exception as e:
                print(f"加载用户画像失败: {e}")

        # 创建新画像
        return UserProfile(user_id=user_id)

    def save_profile(self, profile: UserProfile):
        """保存用户画像"""
        profile.updated_at = datetime.now().isoformat()
        profile_path = self._get_profile_path(profile.user_id)

        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(profile), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户画像失败: {e}")

    def learn_from_conversation(self, user_id: str, conversation_id: str, working_memory):
        """从工作记忆中学习，更新长期记忆"""
        profile = self.load_profile(user_id)

        # 1. 更新城市偏好
        for city in working_memory.cities:
            profile.preferred_cities[city] = profile.preferred_cities.get(city, 0) + 1

        # 2. 更新酒店偏好
        for hotel in working_memory.hotels:
            profile.preferred_hotels[hotel] = profile.preferred_hotels.get(hotel, 0) + 1

        # 3. 更新客户拜访记录
        for customer in working_memory.customers:
            profile.frequent_customers[customer] = profile.frequent_customers.get(customer, 0) + 1

        # 4. 更新意图统计
        if working_memory.current_intent:
            if working_memory.current_intent not in profile.common_intents:
                profile.common_intents.append(working_memory.current_intent)

        # 5. 增加会话计数
        profile.conversation_count += 1

        # 保存更新后的画像
        self.save_profile(profile)

    def get_personalized_hint(self, user_id: str, current_city: Optional[str] = None) -> str:
        """生成个性化提示"""
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
        """获取用户最常去的城市"""
        profile = self.load_profile(user_id)
        return sorted(
            profile.preferred_cities.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

    def get_top_hotels(self, user_id: str, top_n: int = 5) -> List[tuple]:
        """获取用户最常预订的酒店"""
        profile = self.load_profile(user_id)
        return sorted(
            profile.preferred_hotels.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

    def set_preference(self, user_id: str, key: str, value: str):
        """设置用户偏好"""
        profile = self.load_profile(user_id)
        profile.preferences[key] = value
        self.save_profile(profile)

    def get_preference(self, user_id: str, key: str) -> Optional[str]:
        """获取用户偏好"""
        profile = self.load_profile(user_id)
        return profile.preferences.get(key)

    def delete_user_data(self, user_id: str):
        """删除用户数据（GDPR合规）"""
        profile_path = self._get_profile_path(user_id)
        if os.path.exists(profile_path):
            os.remove(profile_path)
            print(f"已删除用户 {user_id} 的数据")

    def get_user_stats(self, user_id: str) -> Dict:
        """获取用户统计信息"""
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


if __name__ == "__main__":
    # 测试代码
    print("=== 测试长期记忆 ===")

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
    user_id = "test_user_001"
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
    print("\n✅ 测试完成")
