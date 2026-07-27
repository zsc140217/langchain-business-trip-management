# -*- coding: utf-8 -*-
"""
密码加密处理
P0-1: 用户认证系统
创建日期: 2026-07-15
"""

import bcrypt


class PasswordHasher:
    """密码加密工具类"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用bcrypt加密密码

        Args:
            password: 明文密码

        Returns:
            加密后的密码哈希
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码是否正确

        Args:
            plain_password: 明文密码
            hashed_password: 加密后的密码哈希

        Returns:
            密码是否匹配
        """
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)


# 单例实例
password_hasher = PasswordHasher()
