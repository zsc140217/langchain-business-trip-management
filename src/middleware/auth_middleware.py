# -*- coding: utf-8 -*-
"""
认证中间件
P0-1: 用户认证系统
创建日期: 2026-07-15
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Header

from src.models.user import User, TokenData
from src.auth import jwt_handler
from src.services.user_service import user_service


async def get_current_user(
    authorization: Optional[str] = Header(None, description="Bearer Token")
) -> User:
    """
    获取当前已认证用户（FastAPI依赖注入函数）

    从请求头Authorization中提取Bearer Token，验证Token有效性，
    并返回当前登录的用户对象。

    Args:
        authorization: Authorization请求头，格式为 "Bearer <token>"

    Returns:
        User: 当前已认证用户对象

    Raises:
        HTTPException: 401 未授权 - Token无效、过期或用户未激活
    """
    # 检查Authorization header是否存在
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授权",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 提取Bearer Token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授权",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # 验证Token
    token_data: Optional[TokenData] = jwt_handler.verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授权",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查Token是否过期
    if jwt_handler.is_token_expired(token_data):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授权",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户信息
    user = user_service.get_user_by_id(token_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授权",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授权",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    验证管理员权限（FastAPI依赖注入函数）

    检查当前用户是否具有管理员权限。

    Args:
        current_user: 当前已认证用户（通过get_current_user依赖注入）

    Returns:
        User: 当前管理员用户对象

    Raises:
        HTTPException: 403 权限不足 - 用户不是管理员
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足",
        )

    return current_user


async def require_executive(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    验证高管权限（FastAPI依赖注入函数）

    检查当前用户是否具有高管权限。

    Args:
        current_user: 当前已认证用户（通过get_current_user依赖注入）

    Returns:
        User: 当前高管用户对象

    Raises:
        HTTPException: 403 权限不足 - 用户不是高管
    """
    if not current_user.is_executive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足",
        )

    return current_user
