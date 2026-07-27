# -*- coding: utf-8 -*-
"""
认证API路由
P0-1: 用户认证系统
创建日期: 2026-07-15
"""

from fastapi import APIRouter, Depends, HTTPException, status
from src.models.user import User, UserCreate, UserLogin, UserUpdate, Token
from src.services.user_service import user_service
from src.middleware.auth_middleware import get_current_user

# 创建路由器
router = APIRouter(
    prefix="/api/auth",
    tags=["认证"]
)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate):
    """
    用户注册

    Args:
        user_create: 用户创建数据

    Returns:
        Token: 包含访问令牌和用户信息

    Raises:
        HTTPException: 400 - 用户名或邮箱已存在
        HTTPException: 500 - 服务器内部错误
    """
    try:
        token = user_service.register_user(user_create)
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(user_login: UserLogin):
    """
    用户登录

    Args:
        user_login: 用户登录数据

    Returns:
        Token: 包含访问令牌和用户信息

    Raises:
        HTTPException: 400 - 用户名或密码错误、用户未激活
        HTTPException: 500 - 服务器内部错误
    """
    try:
        token = user_service.login_user(
            username=user_login.username,
            password=user_login.password
        )
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息

    Args:
        current_user: 当前登录用户（通过依赖注入）

    Returns:
        User: 当前用户信息

    Raises:
        HTTPException: 401 - 未授权（由get_current_user中间件抛出）
    """
    return current_user


@router.put("/me", response_model=User)
async def update_current_user_info(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    更新当前用户信息

    Args:
        user_update: 用户更新数据
        current_user: 当前登录用户（通过依赖注入）

    Returns:
        User: 更新后的用户信息

    Raises:
        HTTPException: 400 - 更新数据无效
        HTTPException: 401 - 未授权（由get_current_user中间件抛出）
        HTTPException: 500 - 服务器内部错误
    """
    try:
        updated_user = user_service.update_user_info(
            user_id=current_user.user_id,
            user_update=user_update
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户信息失败: {str(e)}"
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    用户登出

    Args:
        current_user: 当前登录用户（通过依赖注入）

    Returns:
        dict: 登出成功消息

    Raises:
        HTTPException: 401 - 未授权（由get_current_user中间件抛出）
        HTTPException: 500 - 服务器内部错误

    Note:
        实际的会话清理需要在get_current_user中间件中获取session_id后调用
        user_service.logout_user(session_id)来完成
    """
    try:
        # Note: 这里需要从请求中获取session_id或token来删除session
        # 实际实现可能需要调整，取决于auth_middleware如何传递session信息
        return {"message": "登出成功"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失败: {str(e)}"
        )
