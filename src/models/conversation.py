# -*- coding: utf-8 -*-
"""
会话和消息数据模型
P0-2: 会话管理系统
创建日期: 2026-07-15
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================
# 消息模型
# ============================================

class MessageCreate(BaseModel):
    """创建消息请求"""
    role: str = Field(..., description="消息角色：user/assistant/system")
    content: str = Field(..., description="消息内容")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="消息元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "帮我查询明天去成都的机票",
                "metadata": {"intent": "flight_search"}
            }
        }


class Message(BaseModel):
    """消息对象"""
    message_id: int = Field(..., description="消息ID")
    conversation_id: str = Field(..., description="会话ID")
    role: str = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="消息元数据")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "message_id": 1,
                "conversation_id": "conv_123abc",
                "role": "user",
                "content": "帮我查询明天去成都的机票",
                "metadata": {"intent": "flight_search"},
                "created_at": "2026-07-15T10:30:00"
            }
        }


# ============================================
# 会话模型
# ============================================

class ConversationCreate(BaseModel):
    """创建会话请求"""
    title: Optional[str] = Field(None, description="会话标题")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "成都差旅查询"
            }
        }


class ConversationUpdate(BaseModel):
    """更新会话请求"""
    title: Optional[str] = Field(None, description="会话标题")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "成都差旅查询 - 已完成"
            }
        }


class Conversation(BaseModel):
    """会话对象"""
    conversation_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    title: Optional[str] = Field(None, description="会话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_message_at: Optional[datetime] = Field(None, description="最后消息时间")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123abc",
                "user_id": "user_001",
                "title": "成都差旅查询",
                "created_at": "2026-07-15T10:00:00",
                "updated_at": "2026-07-15T10:30:00",
                "last_message_at": "2026-07-15T10:30:00"
            }
        }


class ConversationWithMessages(Conversation):
    """会话及其消息列表"""
    messages: List[Message] = Field(default_factory=list, description="消息列表")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123abc",
                "user_id": "user_001",
                "title": "成都差旅查询",
                "created_at": "2026-07-15T10:00:00",
                "updated_at": "2026-07-15T10:30:00",
                "last_message_at": "2026-07-15T10:30:00",
                "messages": [
                    {
                        "message_id": 1,
                        "conversation_id": "conv_123abc",
                        "role": "user",
                        "content": "帮我查询明天去成都的机票",
                        "metadata": {},
                        "created_at": "2026-07-15T10:30:00"
                    }
                ]
            }
        }


# ============================================
# 分页响应
# ============================================

class ConversationListResponse(BaseModel):
    """会话列表响应"""
    conversations: List[Conversation] = Field(..., description="会话列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")

    class Config:
        json_schema_extra = {
            "example": {
                "conversations": [],
                "total": 10,
                "page": 1,
                "page_size": 20
            }
        }


class MessageListResponse(BaseModel):
    """消息列表响应"""
    messages: List[Message] = Field(..., description="消息列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [],
                "total": 50,
                "page": 1,
                "page_size": 50
            }
        }
