# -*- coding: utf-8 -*-
"""
用户数据访问层
P0-1: 用户认证系统
创建日期: 2026-07-15
"""

import os
import uuid
from datetime import datetime
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from src.models.user import User, UserInDB, UserCreate, UserSession


class UserRepository:
    """用户数据访问层"""

    def __init__(self):
        """初始化数据库连接配置"""
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'business_trip'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = psycopg2.connect(**self.db_config)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def create_user(self, user_create: UserCreate, password_hash: str) -> UserInDB:
        """
        创建新用户

        Args:
            user_create: 用户创建数据
            password_hash: 密码哈希

        Returns:
            UserInDB: 创建的用户对象
        """
        user_id = f"user_{uuid.uuid4()}"
        now = datetime.utcnow()

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO users (
                        user_id, username, email, full_name, department, position,
                        phone, password_hash, is_executive, is_admin, is_active,
                        created_at, updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING *
                """, (
                    user_id,
                    user_create.username,
                    user_create.email,
                    user_create.full_name,
                    user_create.department,
                    user_create.position,
                    user_create.phone,
                    password_hash,
                    user_create.is_executive,
                    user_create.is_admin,
                    True,  # is_active默认为True
                    now,
                    now
                ))
                row = cur.fetchone()
                return UserInDB(**dict(row))

    def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """
        根据用户ID获取用户

        Args:
            user_id: 用户ID

        Returns:
            Optional[UserInDB]: 用户对象或None
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM users WHERE user_id = %s
                """, (user_id,))
                row = cur.fetchone()
                return UserInDB(**dict(row)) if row else None

    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """
        根据用户名获取用户

        Args:
            username: 用户名

        Returns:
            Optional[UserInDB]: 用户对象或None
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM users WHERE username = %s
                """, (username,))
                row = cur.fetchone()
                return UserInDB(**dict(row)) if row else None

    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        根据邮箱获取用户

        Args:
            email: 邮箱地址

        Returns:
            Optional[UserInDB]: 用户对象或None
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM users WHERE email = %s
                """, (email,))
                row = cur.fetchone()
                return UserInDB(**dict(row)) if row else None

    def update_user(self, user_id: str, **kwargs) -> Optional[UserInDB]:
        """
        更新用户信息

        Args:
            user_id: 用户ID
            **kwargs: 要更新的字段和值

        Returns:
            Optional[UserInDB]: 更新后的用户对象或None
        """
        if not kwargs:
            return self.get_user_by_id(user_id)

        # 构建更新SQL
        update_fields = []
        values = []

        allowed_fields = [
            'email', 'full_name', 'department', 'position',
            'phone', 'is_active', 'is_executive', 'is_admin'
        ]

        for field, value in kwargs.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = %s")
                values.append(value)

        if not update_fields:
            return self.get_user_by_id(user_id)

        # 添加updated_at字段
        update_fields.append("updated_at = %s")
        values.append(datetime.utcnow())

        # 添加user_id到values
        values.append(user_id)

        sql = f"""
            UPDATE users
            SET {', '.join(update_fields)}
            WHERE user_id = %s
            RETURNING *
        """

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, values)
                row = cur.fetchone()
                return UserInDB(**dict(row)) if row else None

    def create_session(self, user_id: str, token_hash: str, expires_at: datetime) -> UserSession:
        """
        创建用户会话

        Args:
            user_id: 用户ID
            token_hash: 令牌哈希
            expires_at: 过期时间

        Returns:
            UserSession: 会话对象
        """
        session_id = f"session_{uuid.uuid4()}"
        now = datetime.utcnow()

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO user_sessions (
                        session_id, user_id, token_hash, expires_at, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING session_id, user_id, expires_at, created_at
                """, (session_id, user_id, token_hash, expires_at, now))
                row = cur.fetchone()
                return UserSession(**dict(row))

    def delete_session(self, session_id: str) -> bool:
        """
        删除用户会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否删除成功
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM user_sessions WHERE session_id = %s
                """, (session_id,))
                return cur.rowcount > 0

    def delete_expired_sessions(self) -> int:
        """
        删除所有过期会话

        Returns:
            int: 删除的会话数量
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM user_sessions WHERE expires_at < %s
                """, (datetime.utcnow(),))
                return cur.rowcount


# 创建单例实例
user_repository = UserRepository()
