# -*- coding: utf-8 -*-
"""
用户数据模型
P0-1: 用户认证系统
创建日期: 2026-07-15
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=100, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: str = Field(..., min_length=1, max_length=100, description="姓名")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    phone: Optional[str] = Field(None, max_length=20, description="电话")


class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    is_executive: bool = Field(False, description="是否高管")
    is_admin: bool = Field(False, description="是否管理员")


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """数据库中的用户模型"""
    user_id: str
    password_hash: str
    is_executive: bool
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserBase):
    """用户响应模型（不包含敏感信息）"""
    user_id: str
    is_executive: bool
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT Token响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: User = Field(..., description="用户信息")


class TokenData(BaseModel):
    """Token载荷数据"""
    user_id: str
    username: str
    is_executive: bool
    is_admin: bool
    exp: Optional[datetime] = None


class UserSession(BaseModel):
    """用户会话模型"""
    session_id: str
    user_id: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
