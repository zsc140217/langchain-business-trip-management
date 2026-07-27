"""
用户画像数据访问层 (Repository Pattern)
负责 user_profiles 表的CRUD操作
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from .db_config import get_db_connection


class UserProfileRepository:
    """用户画像数据访问层"""

    def find_by_user_id(self, user_id: str) -> Optional[Dict]:
        """
        根据user_id查询用户画像

        Args:
            user_id: 用户ID

        Returns:
            用户画像字典，不存在则返回None
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        user_id,
                        preferences,
                        preferred_cities,
                        preferred_hotels,
                        frequent_customers,
                        common_intents,
                        conversation_count,
                        created_at,
                        updated_at
                    FROM user_profiles
                    WHERE user_id = %s
                """, (user_id,))

                row = cursor.fetchone()
                if not row:
                    return None

                return {
                    "user_id": row[0],
                    "preferences": row[1] or {},
                    "preferred_cities": row[2] or {},
                    "preferred_hotels": row[3] or {},
                    "frequent_customers": row[4] or {},
                    "common_intents": row[5] or [],
                    "conversation_count": row[6] or 0,
                    "created_at": row[7].isoformat() if row[7] else None,
                    "updated_at": row[8].isoformat() if row[8] else None,
                }
        finally:
            conn.close()

    def create(self, user_id: str) -> Dict:
        """
        创建新的用户画像

        Args:
            user_id: 用户ID

        Returns:
            创建的用户画像字典
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_profiles (user_id, preferences, preferred_cities,
                                             preferred_hotels, frequent_customers,
                                             common_intents, conversation_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING user_id, preferences, preferred_cities, preferred_hotels,
                              frequent_customers, common_intents, conversation_count,
                              created_at, updated_at
                """, (user_id, {}, {}, {}, {}, [], 0))

                row = cursor.fetchone()
                conn.commit()

                return {
                    "user_id": row[0],
                    "preferences": row[1] or {},
                    "preferred_cities": row[2] or {},
                    "preferred_hotels": row[3] or {},
                    "frequent_customers": row[4] or {},
                    "common_intents": row[5] or [],
                    "conversation_count": row[6] or 0,
                    "created_at": row[7].isoformat() if row[7] else None,
                    "updated_at": row[8].isoformat() if row[8] else None,
                }
        except Exception as e:
            conn.rollback()
            raise Exception(f"创建用户画像失败: {e}")
        finally:
            conn.close()

    def update(self, user_id: str, profile_data: Dict) -> Dict:
        """
        更新用户画像

        Args:
            user_id: 用户ID
            profile_data: 包含更新字段的字典

        Returns:
            更新后的用户画像字典
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 构建动态更新语句
                update_fields = []
                values = []

                if "preferences" in profile_data:
                    update_fields.append("preferences = %s")
                    values.append(json.dumps(profile_data["preferences"]))

                if "preferred_cities" in profile_data:
                    update_fields.append("preferred_cities = %s")
                    values.append(json.dumps(profile_data["preferred_cities"]))

                if "preferred_hotels" in profile_data:
                    update_fields.append("preferred_hotels = %s")
                    values.append(json.dumps(profile_data["preferred_hotels"]))

                if "frequent_customers" in profile_data:
                    update_fields.append("frequent_customers = %s")
                    values.append(json.dumps(profile_data["frequent_customers"]))

                if "common_intents" in profile_data:
                    update_fields.append("common_intents = %s")
                    values.append(profile_data["common_intents"])

                if "conversation_count" in profile_data:
                    update_fields.append("conversation_count = %s")
                    values.append(profile_data["conversation_count"])

                if not update_fields:
                    # 没有字段需要更新，直接返回当前画像
                    return self.find_by_user_id(user_id)

                # 添加 updated_at 自动更新
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                values.append(user_id)

                query = f"""
                    UPDATE user_profiles
                    SET {', '.join(update_fields)}
                    WHERE user_id = %s
                    RETURNING user_id, preferences, preferred_cities, preferred_hotels,
                              frequent_customers, common_intents, conversation_count,
                              created_at, updated_at
                """

                cursor.execute(query, values)
                row = cursor.fetchone()
                conn.commit()

                if not row:
                    raise Exception(f"用户画像不存在: {user_id}")

                return {
                    "user_id": row[0],
                    "preferences": row[1] or {},
                    "preferred_cities": row[2] or {},
                    "preferred_hotels": row[3] or {},
                    "frequent_customers": row[4] or {},
                    "common_intents": row[5] or [],
                    "conversation_count": row[6] or 0,
                    "created_at": row[7].isoformat() if row[7] else None,
                    "updated_at": row[8].isoformat() if row[8] else None,
                }
        except Exception as e:
            conn.rollback()
            raise Exception(f"更新用户画像失败: {e}")
        finally:
            conn.close()

    def delete(self, user_id: str) -> bool:
        """
        删除用户画像（GDPR合规）

        Args:
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM user_profiles
                    WHERE user_id = %s
                """, (user_id,))

                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f"删除用户画像失败: {e}")
        finally:
            conn.close()

    def increment_city_count(self, user_id: str, city: str) -> None:
        """
        增加城市访问次数（原子操作）

        Args:
            user_id: 用户ID
            city: 城市名称
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_profiles
                    SET preferred_cities = jsonb_set(
                        COALESCE(preferred_cities, '{}'::jsonb),
                        %s,
                        (COALESCE((preferred_cities->%s)::int, 0) + 1)::text::jsonb
                    ),
                    updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, ([city], city, user_id))

                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"增加城市计数失败: {e}")
        finally:
            conn.close()

    def increment_hotel_count(self, user_id: str, hotel: str) -> None:
        """
        增加酒店预订次数（原子操作）

        Args:
            user_id: 用户ID
            hotel: 酒店名称
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_profiles
                    SET preferred_hotels = jsonb_set(
                        COALESCE(preferred_hotels, '{}'::jsonb),
                        %s,
                        (COALESCE((preferred_hotels->%s)::int, 0) + 1)::text::jsonb
                    ),
                    updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, ([hotel], hotel, user_id))

                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"增加酒店计数失败: {e}")
        finally:
            conn.close()

    def increment_customer_count(self, user_id: str, customer: str) -> None:
        """
        增加客户拜访次数（原子操作）

        Args:
            user_id: 用户ID
            customer: 客户名称
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_profiles
                    SET frequent_customers = jsonb_set(
                        COALESCE(frequent_customers, '{}'::jsonb),
                        %s,
                        (COALESCE((frequent_customers->%s)::int, 0) + 1)::text::jsonb
                    ),
                    updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, ([customer], customer, user_id))

                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"增加客户计数失败: {e}")
        finally:
            conn.close()

    def add_intent(self, user_id: str, intent: str) -> None:
        """
        添加常见意图（去重）

        Args:
            user_id: 用户ID
            intent: 意图名称
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 先检查是否已存在
                cursor.execute("""
                    SELECT common_intents FROM user_profiles
                    WHERE user_id = %s
                """, (user_id,))

                row = cursor.fetchone()
                if row and row[0] and intent in row[0]:
                    # 意图已存在，不重复添加
                    return

                # 添加新意图
                cursor.execute("""
                    UPDATE user_profiles
                    SET common_intents = array_append(
                        COALESCE(common_intents, ARRAY[]::text[]),
                        %s
                    ),
                    updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (intent, user_id))

                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"添加意图失败: {e}")
        finally:
            conn.close()

    def increment_conversation_count(self, user_id: str) -> None:
        """
        增加会话计数（原子操作）

        Args:
            user_id: 用户ID
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_profiles
                    SET conversation_count = conversation_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (user_id,))

                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"增加会话计数失败: {e}")
        finally:
            conn.close()

    def get_top_cities(self, user_id: str, limit: int = 5) -> List[Tuple[str, int]]:
        """
        获取最常访问的城市（按次数排序）

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            [(城市名, 访问次数), ...]
        """
        profile = self.find_by_user_id(user_id)
        if not profile or not profile.get("preferred_cities"):
            return []

        cities = profile["preferred_cities"]
        sorted_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)
        return sorted_cities[:limit]

    def get_top_hotels(self, user_id: str, limit: int = 5) -> List[Tuple[str, int]]:
        """
        获取最常预订的酒店（按次数排序）

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            [(酒店名, 预订次数), ...]
        """
        profile = self.find_by_user_id(user_id)
        if not profile or not profile.get("preferred_hotels"):
            return []

        hotels = profile["preferred_hotels"]
        sorted_hotels = sorted(hotels.items(), key=lambda x: x[1], reverse=True)
        return sorted_hotels[:limit]

    def set_preference(self, user_id: str, key: str, value: str) -> None:
        """
        设置用户偏好设置

        Args:
            user_id: 用户ID
            key: 偏好键
            value: 偏好值
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_profiles
                    SET preferences = jsonb_set(
                        COALESCE(preferences, '{}'::jsonb),
                        %s,
                        %s::jsonb
                    ),
                    updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, ([key], json.dumps(value), user_id))

                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"设置偏好失败: {e}")
        finally:
            conn.close()

    def get_preference(self, user_id: str, key: str) -> Optional[str]:
        """
        获取用户偏好设置

        Args:
            user_id: 用户ID
            key: 偏好键

        Returns:
            偏好值，不存在则返回None
        """
        profile = self.find_by_user_id(user_id)
        if not profile or not profile.get("preferences"):
            return None

        return profile["preferences"].get(key)
