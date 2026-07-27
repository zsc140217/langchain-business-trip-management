"""
PostgreSQL后端 - 长期记忆（用户画像、查询历史）
需要安装: pip install psycopg2-binary
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from datetime import datetime
from .base import LongTermBackend


class PostgresLongTermBackend(LongTermBackend):
    """PostgreSQL存储的长期记忆后端"""

    def __init__(self, connection_string: str = None):
        """
        Args:
            connection_string: PostgreSQL连接字符串
                默认: postgresql://dev:dev123@localhost:5432/travel_agent
        """
        if connection_string is None:
            connection_string = "postgresql://dev:dev123@localhost:5432/travel_agent"

        try:
            self.conn = psycopg2.connect(connection_string)
            self.conn.autocommit = True
            print("[OK] PostgreSQL连接成功")
        except Exception as e:
            raise ConnectionError(f"PostgreSQL连接失败: {e}")

    def save_profile(self, user_id: str, profile_data: Dict):
        """保存用户画像（UPSERT）"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_profiles (
                    user_id, preferences, preferred_cities, preferred_hotels,
                    frequent_customers, common_intents, conversation_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    preferences = EXCLUDED.preferences,
                    preferred_cities = EXCLUDED.preferred_cities,
                    preferred_hotels = EXCLUDED.preferred_hotels,
                    frequent_customers = EXCLUDED.frequent_customers,
                    common_intents = EXCLUDED.common_intents,
                    conversation_count = EXCLUDED.conversation_count,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                user_id,
                json.dumps(profile_data.get('preferences', {})),
                json.dumps(profile_data.get('preferred_cities', {})),
                json.dumps(profile_data.get('preferred_hotels', {})),
                json.dumps(profile_data.get('frequent_customers', {})),
                profile_data.get('common_intents', []),
                profile_data.get('conversation_count', 0)
            ))

    def get_profile(self, user_id: str) -> Optional[Dict]:
        """获取用户画像"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT user_id, preferences, preferred_cities, preferred_hotels,
                       frequent_customers, common_intents, conversation_count,
                       created_at, updated_at
                FROM user_profiles
                WHERE user_id = %s
            """, (user_id,))

            row = cur.fetchone()
            if row:
                return dict(row)
            return None

    def update_preferences(self, user_id: str, key: str, increment: int = 1):
        """更新偏好统计"""
        # 这个方法在PostgreSQL中需要更复杂的逻辑
        # 简化处理：由上层调用 get_profile -> 修改 -> save_profile
        pass

    def delete_profile(self, user_id: str):
        """删除用户画像（级联删除查询历史）"""
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))

    def save_query_history(self, user_id: str, thread_id: str, query: str, response: str):
        """保存查询历史"""
        with self.conn.cursor() as cur:
            # 确保user_id存在
            cur.execute("""
                INSERT INTO user_profiles (user_id, preferences)
                VALUES (%s, '{}')
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id,))

            # 插入查询历史
            cur.execute("""
                INSERT INTO query_history (user_id, thread_id, query, response)
                VALUES (%s, %s, %s, %s)
            """, (user_id, thread_id, query, response))

    def get_query_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """获取查询历史"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, thread_id, query, response, created_at
                FROM query_history
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, limit))

            rows = cur.fetchall()
            return [dict(row) for row in rows]

    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM user_profiles")
            total_users = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM query_history")
            total_queries = cur.fetchone()[0]

            return {
                "total_users": total_users,
                "total_queries": total_queries,
                "backend": "postgresql"
            }

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    # 测试代码
    print("=== 测试PostgreSQL长期记忆后端 ===")

    try:
        backend = PostgresLongTermBackend()

        # 保存用户画像
        profile_data = {
            'user_id': 'test_user_001',
            'preferences': {'language': 'zh'},
            'preferred_cities': {'北京': 2, '上海': 1},
            'preferred_hotels': {'希尔顿酒店': 1},
            'frequent_customers': {'华为公司': 1},
            'common_intents': ['查询天气', '查询酒店'],
            'conversation_count': 2
        }
        backend.save_profile('test_user_001', profile_data)
        print("[OK] 保存用户画像成功")

        # 获取用户画像
        profile = backend.get_profile('test_user_001')
        print(f"\n用户画像: {profile['user_id']}")
        print(f"  会话数: {profile['conversation_count']}")
        print(f"  常去城市: {profile['preferred_cities']}")

        # 保存查询历史
        backend.save_query_history(
            'test_user_001',
            'test_thread_001',
            '北京的天气怎么样？',
            '北京明天晴天，气温15-25度'
        )
        print("\n[OK] 保存查询历史成功")

        # 获取查询历史
        history = backend.get_query_history('test_user_001', limit=5)
        print(f"\n查询历史 ({len(history)}条):")
        for h in history:
            print(f"  {h['created_at']}: {h['query']}")

        # 获取统计
        stats = backend.get_stats()
        print(f"\n统计信息: {stats}")

        # 清理测试数据
        backend.delete_profile('test_user_001')
        print("\n[OK] 测试完成")

        backend.close()

    except ConnectionError as e:
        print(f"[WARNING] {e}")
        print("提示：请先启动PostgreSQL服务器")
