# -*- coding: utf-8 -*-
"""
会话管理API
P0-2: 会话管理系统
创建日期: 2026-07-15
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from src.models.user import User
from src.models.conversation import (
    Conversation,
    ConversationCreate,
    ConversationUpdate,
    ConversationListResponse,
    Message,
    MessageCreate,
    MessageListResponse,
    ConversationWithMessages
)
from src.services.conversation_service import conversation_service
from src.middleware.auth_middleware import get_current_user


router = APIRouter(prefix="/api/conversations", tags=["会话管理"])


# ============================================
# 会话相关接口
# ============================================

@router.post("", response_model=Conversation, summary="创建新会话")
async def create_conversation(
    conversation_create: ConversationCreate,
    current_user: User = Depends(get_current_user)
):
    """
    创建新会话

    - **title**: 会话标题（可选）
    """
    try:
        conversation = conversation_service.create_conversation(
            user_id=current_user.user_id,
            conversation_create=conversation_create
        )
        return conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("", response_model=ConversationListResponse, summary="获取会话列表")
async def list_conversations(
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的会话列表（分页）

    - **page**: 页码（从1开始）
    - **page_size**: 每页大小（1-100）
    """
    try:
        conversations, total = conversation_service.list_conversations(
            user_id=current_user.user_id,
            page=page,
            page_size=page_size
        )
        return ConversationListResponse(
            conversations=conversations,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.get("/{conversation_id}", response_model=ConversationWithMessages, summary="获取会话详情")
async def get_conversation(
    conversation_id: str,
    message_limit: int = Query(50, ge=1, le=200, description="消息数量限制"),
    current_user: User = Depends(get_current_user)
):
    """
    获取会话详情及最近的消息

    - **conversation_id**: 会话ID
    - **message_limit**: 返回的消息数量（1-200）
    """
    conversation = conversation_service.get_conversation_with_messages(
        conversation_id=conversation_id,
        user_id=current_user.user_id,
        message_limit=message_limit
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在或无权访问")

    return conversation


@router.put("/{conversation_id}", response_model=Conversation, summary="更新会话")
async def update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    更新会话信息

    - **conversation_id**: 会话ID
    - **title**: 新标题
    """
    conversation = conversation_service.update_conversation(
        conversation_id=conversation_id,
        user_id=current_user.user_id,
        conversation_update=conversation_update
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在或无权访问")

    return conversation


@router.delete("/{conversation_id}", summary="删除会话")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    删除会话（级联删除所有消息）

    - **conversation_id**: 会话ID
    """
    success = conversation_service.delete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.user_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在或无权访问")

    return {"message": "会话删除成功", "conversation_id": conversation_id}


# ============================================
# 消息相关接口
# ============================================

@router.get("/{conversation_id}/messages", response_model=MessageListResponse, summary="获取消息列表")
async def list_messages(
    conversation_id: str,
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    page_size: int = Query(50, ge=1, le=200, description="每页大小"),
    current_user: User = Depends(get_current_user)
):
    """
    获取会话的消息列表（分页）

    - **conversation_id**: 会话ID
    - **page**: 页码（从1开始）
    - **page_size**: 每页大小（1-200）
    """
    result = conversation_service.list_messages(
        conversation_id=conversation_id,
        user_id=current_user.user_id,
        page=page,
        page_size=page_size
    )
    if result is None:
        raise HTTPException(status_code=404, detail="会话不存在或无权访问")

    messages, total = result
    return MessageListResponse(
        messages=messages,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/{conversation_id}/messages", response_model=Message, summary="发送消息")
async def send_message(
    conversation_id: str,
    message_create: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    """
    向会话发送消息

    - **conversation_id**: 会话ID
    - **role**: 消息角色（user/assistant/system）
    - **content**: 消息内容
    - **metadata**: 消息元数据（可选）
    """
    message = conversation_service.send_message(
        conversation_id=conversation_id,
        user_id=current_user.user_id,
        message_create=message_create
    )
    if not message:
        raise HTTPException(status_code=404, detail="会话不存在或无权访问")

    return message
