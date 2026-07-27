# -*- coding: utf-8 -*-
"""
会话服务层
P0-2: 会话管理系统
创建日期: 2026-07-15
"""

from typing import Optional, List, Tuple
from src.database.conversation_repository import conversation_repository
from src.models.conversation import (
    Conversation,
    ConversationCreate,
    ConversationUpdate,
    Message,
    MessageCreate,
    ConversationWithMessages
)


class ConversationService:
    """会话业务逻辑层"""

    def __init__(self):
        self.repo = conversation_repository

    def create_conversation(
        self,
        user_id: str,
        conversation_create: ConversationCreate
    ) -> Conversation:
        """
        创建新会话

        Args:
            user_id: 用户ID
            conversation_create: 会话创建数据

        Returns:
            Conversation: 创建的会话
        """
        return self.repo.create_conversation(user_id, conversation_create)

    def get_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> Optional[Conversation]:
        """
        获取会话详情

        Args:
            conversation_id: 会话ID
            user_id: 用户ID（验证权限）

        Returns:
            Optional[Conversation]: 会话对象或None
        """
        return self.repo.get_conversation_by_id(conversation_id, user_id)

    def list_conversations(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Conversation], int]:
        """
        获取用户会话列表

        Args:
            user_id: 用户ID
            page: 页码（从1开始）
            page_size: 每页大小

        Returns:
            Tuple[List[Conversation], int]: (会话列表, 总数)
        """
        return self.repo.list_conversations(user_id, page, page_size)

    def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        conversation_update: ConversationUpdate
    ) -> Optional[Conversation]:
        """
        更新会话信息

        Args:
            conversation_id: 会话ID
            user_id: 用户ID（验证权限）
            conversation_update: 更新数据

        Returns:
            Optional[Conversation]: 更新后的会话或None
        """
        return self.repo.update_conversation(
            conversation_id,
            user_id,
            title=conversation_update.title
        )

    def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """
        删除会话

        Args:
            conversation_id: 会话ID
            user_id: 用户ID（验证权限）

        Returns:
            bool: 是否删除成功
        """
        return self.repo.delete_conversation(conversation_id, user_id)

    # ============================================
    # 消息相关操作
    # ============================================

    def send_message(
        self,
        conversation_id: str,
        user_id: str,
        message_create: MessageCreate
    ) -> Optional[Message]:
        """
        发送消息到会话

        Args:
            conversation_id: 会话ID
            user_id: 用户ID（验证权限）
            message_create: 消息创建数据

        Returns:
            Optional[Message]: 创建的消息或None（会话不存在）
        """
        # 验证会话存在且属于该用户
        conversation = self.repo.get_conversation_by_id(conversation_id, user_id)
        if not conversation:
            return None

        return self.repo.create_message(conversation_id, message_create)

    def list_messages(
        self,
        conversation_id: str,
        user_id: str,
        page: int = 1,
        page_size: int = 50
    ) -> Optional[Tuple[List[Message], int]]:
        """
        获取会话消息列表

        Args:
            conversation_id: 会话ID
            user_id: 用户ID（验证权限）
            page: 页码（从1开始）
            page_size: 每页大小

        Returns:
            Optional[Tuple[List[Message], int]]: (消息列表, 总数) 或 None（会话不存在）
        """
        # 验证会话存在且属于该用户
        conversation = self.repo.get_conversation_by_id(conversation_id, user_id)
        if not conversation:
            return None

        return self.repo.list_messages(conversation_id, page, page_size)

    def get_conversation_with_messages(
        self,
        conversation_id: str,
        user_id: str,
        message_limit: int = 50
    ) -> Optional[ConversationWithMessages]:
        """
        获取会话及其消息

        Args:
            conversation_id: 会话ID
            user_id: 用户ID（验证权限）
            message_limit: 消息数量限制

        Returns:
            Optional[ConversationWithMessages]: 会话及消息或None
        """
        return self.repo.get_conversation_with_messages(
            conversation_id,
            user_id,
            message_limit
        )


# 创建单例实例
conversation_service = ConversationService()
