# -*- coding: utf-8 -*-
"""
JWT Token处理
P0-1: 用户认证系统
创建日期: 2026-07-15
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

import jwt
from jwt.exceptions import InvalidTokenError

from src.models.user import TokenData


class JWTHandler:
    """JWT Token处理器"""

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 1440  # 24小时
    ):
        """
        初始化JWT处理器

        Args:
            secret_key: JWT密钥（从环境变量读取，若无则生成随机密钥）
            algorithm: 加密算法
            access_token_expire_minutes: Token过期时间（分钟）
        """
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY") or self._generate_secret_key()
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes

    @staticmethod
    def _generate_secret_key() -> str:
        """生成随机密钥（用于开发环境）"""
        return str(uuid.uuid4())

    def create_access_token(
        self,
        user_id: str,
        username: str,
        is_executive: bool,
        is_admin: bool,
        expires_delta: Optional[timedelta] = None
    ) -> tuple[str, datetime]:
        """
        创建访问令牌

        Args:
            user_id: 用户ID
            username: 用户名
            is_executive: 是否高管
            is_admin: 是否管理员
            expires_delta: 自定义过期时间

        Returns:
            (token字符串, 过期时间)
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode = {
            "sub": user_id,
            "username": username,
            "is_executive": is_executive,
            "is_admin": is_admin,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # JWT ID，用于Token唯一标识
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt, expire

    def verify_token(self, token: str) -> Optional[TokenData]:
        """
        验证并解析Token

        Args:
            token: JWT Token字符串

        Returns:
            TokenData对象，若Token无效则返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            username: str = payload.get("username")
            is_executive: bool = payload.get("is_executive", False)
            is_admin: bool = payload.get("is_admin", False)
            exp: datetime = datetime.fromtimestamp(payload.get("exp"))

            if user_id is None or username is None:
                return None

            return TokenData(
                user_id=user_id,
                username=username,
                is_executive=is_executive,
                is_admin=is_admin,
                exp=exp
            )
        except InvalidTokenError:
            return None

    def is_token_expired(self, token_data: TokenData) -> bool:
        """
        检查Token是否过期

        Args:
            token_data: Token数据

        Returns:
            是否过期
        """
        if token_data.exp is None:
            return True
        return datetime.utcnow() > token_data.exp


# 单例实例
jwt_handler = JWTHandler()
