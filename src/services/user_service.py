# -*- coding: utf-8 -*-
"""
用户服务层
P0-1: 用户认证系统
创建日期: 2026-07-15
"""

import hashlib
from typing import Optional

from src.models.user import User, UserCreate, UserUpdate, Token
from src.database.user_repository import user_repository
from src.auth import password_hasher, jwt_handler


class UserService:
    """用户服务层"""

    def __init__(self):
        """初始化用户服务"""
        self.repository = user_repository
        self.password_hasher = password_hasher
        self.jwt_handler = jwt_handler

    def register_user(self, user_create: UserCreate) -> Token:
        """
        注册新用户

        Args:
            user_create: 用户创建数据

        Returns:
            Token: 包含访问令牌和用户信息

        Raises:
            ValueError: 用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        existing_user = self.repository.get_user_by_username(user_create.username)
        if existing_user:
            raise ValueError(f"用户名 '{user_create.username}' 已存在")

        # 检查邮箱是否已存在
        existing_email = self.repository.get_user_by_email(user_create.email)
        if existing_email:
            raise ValueError(f"邮箱 '{user_create.email}' 已被注册")

        # 加密密码
        password_hash = self.password_hasher.hash_password(user_create.password)

        # 创建用户
        user_in_db = self.repository.create_user(user_create, password_hash)

        # 生成JWT Token
        access_token, expires_at = self.jwt_handler.create_access_token(
            user_id=user_in_db.user_id,
            username=user_in_db.username,
            is_executive=user_in_db.is_executive,
            is_admin=user_in_db.is_admin
        )

        # 计算token哈希并创建session
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        session = self.repository.create_session(
            user_id=user_in_db.user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )

        # 构造用户响应对象（不包含password_hash）
        user = User(
            user_id=user_in_db.user_id,
            username=user_in_db.username,
            email=user_in_db.email,
            full_name=user_in_db.full_name,
            department=user_in_db.department,
            position=user_in_db.position,
            phone=user_in_db.phone,
            is_executive=user_in_db.is_executive,
            is_active=user_in_db.is_active,
            is_admin=user_in_db.is_admin,
            created_at=user_in_db.created_at,
            updated_at=user_in_db.updated_at
        )

        # 计算过期时间（秒）
        expires_in = int((expires_at - user_in_db.created_at).total_seconds())

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            user=user
        )

    def login_user(self, username: str, password: str) -> Token:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            Token: 包含访问令牌和用户信息

        Raises:
            ValueError: 用户不存在、密码错误或用户未激活
        """
        # 根据用户名获取用户
        user_in_db = self.repository.get_user_by_username(username)
        if not user_in_db:
            raise ValueError("用户名或密码错误")

        # 检查用户是否激活
        if not user_in_db.is_active:
            raise ValueError("用户账户已被禁用")

        # 验证密码
        if not self.password_hasher.verify_password(password, user_in_db.password_hash):
            raise ValueError("用户名或密码错误")

        # 生成JWT Token
        access_token, expires_at = self.jwt_handler.create_access_token(
            user_id=user_in_db.user_id,
            username=user_in_db.username,
            is_executive=user_in_db.is_executive,
            is_admin=user_in_db.is_admin
        )

        # 计算token哈希并创建session
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        session = self.repository.create_session(
            user_id=user_in_db.user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )

        # 构造用户响应对象（不包含password_hash）
        user = User(
            user_id=user_in_db.user_id,
            username=user_in_db.username,
            email=user_in_db.email,
            full_name=user_in_db.full_name,
            department=user_in_db.department,
            position=user_in_db.position,
            phone=user_in_db.phone,
            is_executive=user_in_db.is_executive,
            is_active=user_in_db.is_active,
            is_admin=user_in_db.is_admin,
            created_at=user_in_db.created_at,
            updated_at=user_in_db.updated_at
        )

        # 计算过期时间（秒）
        from datetime import datetime
        expires_in = int((expires_at - datetime.utcnow()).total_seconds())

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            user=user
        )

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        根据用户ID获取用户

        Args:
            user_id: 用户ID

        Returns:
            Optional[User]: 用户对象（不包含password_hash）或None
        """
        user_in_db = self.repository.get_user_by_id(user_id)
        if not user_in_db:
            return None

        # 转换为User对象（不包含password_hash）
        return User(
            user_id=user_in_db.user_id,
            username=user_in_db.username,
            email=user_in_db.email,
            full_name=user_in_db.full_name,
            department=user_in_db.department,
            position=user_in_db.position,
            phone=user_in_db.phone,
            is_executive=user_in_db.is_executive,
            is_active=user_in_db.is_active,
            is_admin=user_in_db.is_admin,
            created_at=user_in_db.created_at,
            updated_at=user_in_db.updated_at
        )

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户

        Args:
            username: 用户名

        Returns:
            Optional[User]: 用户对象（不包含password_hash）或None
        """
        user_in_db = self.repository.get_user_by_username(username)
        if not user_in_db:
            return None

        # 转换为User对象（不包含password_hash）
        return User(
            user_id=user_in_db.user_id,
            username=user_in_db.username,
            email=user_in_db.email,
            full_name=user_in_db.full_name,
            department=user_in_db.department,
            position=user_in_db.position,
            phone=user_in_db.phone,
            is_executive=user_in_db.is_executive,
            is_active=user_in_db.is_active,
            is_admin=user_in_db.is_admin,
            created_at=user_in_db.created_at,
            updated_at=user_in_db.updated_at
        )

    def update_user_info(self, user_id: str, user_update: UserUpdate) -> User:
        """
        更新用户信息

        Args:
            user_id: 用户ID
            user_update: 用户更新数据

        Returns:
            User: 更新后的用户对象

        Raises:
            ValueError: 用户不存在
        """
        # 检查用户是否存在
        existing_user = self.repository.get_user_by_id(user_id)
        if not existing_user:
            raise ValueError(f"用户ID '{user_id}' 不存在")

        # 构建更新字段字典（排除None值）
        update_data = {}
        if user_update.email is not None:
            # 检查新邮箱是否被其他用户占用
            existing_email = self.repository.get_user_by_email(user_update.email)
            if existing_email and existing_email.user_id != user_id:
                raise ValueError(f"邮箱 '{user_update.email}' 已被其他用户使用")
            update_data['email'] = user_update.email

        if user_update.full_name is not None:
            update_data['full_name'] = user_update.full_name
        if user_update.department is not None:
            update_data['department'] = user_update.department
        if user_update.position is not None:
            update_data['position'] = user_update.position
        if user_update.phone is not None:
            update_data['phone'] = user_update.phone
        if user_update.is_active is not None:
            update_data['is_active'] = user_update.is_active

        # 更新用户
        user_in_db = self.repository.update_user(user_id, **update_data)
        if not user_in_db:
            raise ValueError(f"更新用户失败")

        # 转换为User对象（不包含password_hash）
        return User(
            user_id=user_in_db.user_id,
            username=user_in_db.username,
            email=user_in_db.email,
            full_name=user_in_db.full_name,
            department=user_in_db.department,
            position=user_in_db.position,
            phone=user_in_db.phone,
            is_executive=user_in_db.is_executive,
            is_active=user_in_db.is_active,
            is_admin=user_in_db.is_admin,
            created_at=user_in_db.created_at,
            updated_at=user_in_db.updated_at
        )

    def logout_user(self, session_id: str) -> bool:
        """
        用户登出

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否登出成功
        """
        return self.repository.delete_session(session_id)


# 创建单例实例
user_service = UserService()
