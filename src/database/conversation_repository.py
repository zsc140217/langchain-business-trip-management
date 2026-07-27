# -*- coding: utf-8 -*-
"""
会话数据访问层
P0-2: 会话管理系统
创建日期: 2026-07-15
"""

import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from psycopg2.extras import RealDictCursor

from src.database.db_config import db_config
from src.models.conversation import (
    Conversation,
    Message,
    MessageCreate,
    ConversationCreate,
    ConversationWithMessages
)


class ConversationRepository:
    """会话数据访问层"""

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
            Conversation: 创建的会话对象
        """
        conversation_id = f"conv_{uuid.uuid4().hex[:16]}"
        now = datetime.utcnow()

        with db_config.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO conversations (
                        conversation_id, user_id, title, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    conversation_id,
                    user_id,
                    conversation_create.title,
                    now,
                    now
                ))
                row = cur.fetchone()
                return Conversation(**dict(row))

    def get_conversation_by_id(
        self,
        conversation_id: str,
        user_id: str
    ) -> Optional[Conversation]:
        """
        根据会话ID获取会话（验证用户权限）

        Args:
            conversation_id: 会话ID
            user_id: 用户ID

        Returns:
            Optional[Conversation]: 会话对象或None
        """
        with db_config.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM conversations
                    WHERE conversation_id = %s AND user_id = %s
                """, (conversation_id, user_id))
                row = cur.fetchone()
                return Conversation(**dict(row)) if row else None

    def list_conversations(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Conversation], int]:
        """
        获取用户的会话列表（分页）

        Args:
            user_id: 用户ID
            page: 页码（从1开始）
            page_size: 每页大小

        Returns:
            Tuple[List[Conversation], int]: (会话列表, 总数)
        """
        offset = (page - 1) * page_size

        with db_config.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 获取总数
                cur.execute("""
                    SELECT COUNT(*) as total FROM conversations
                    WHERE user_id = %s
                """, (user_id,))
                total = cur.fetchone()['total']

                # 获取分页数据
                cur.execute("""
                    SELECT * FROM conversations
                    WHERE user_id = %s
                    ORDER BY last_message_at DESC NULLS LAST, updated_at DESC
                    LIMIT %s OFFSET %s
                """, (user_id, page_size, offset))
                rows = cur.fetchall()
                conversations = [Conversation(**dict(row)) for row in rows]

                return conversations, total

    def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        title: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        更新会话信息

        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            title: 新标题

        Returns:
            Optional[Conversation]: 更新后的会话对象或None
        """
        with db_config.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    UPDATE conversations
                    SET title = COALESCE(%s, title),
                        updated_at = %s
                    WHERE conversation_id = %s AND user_id = %s
                    RETURNING *
                """, (title, datetime.utcnow(), conversation_id, user_id))
                row = cur.fetchone()
                return Conversation(**dict(row)) if row else None

    def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """
        删除会话（级联删除消息）

        Args:
            conversation_id: 会话ID
            user_id: 用户ID

        Returns:
            bool: 是否删除成功
        """
        with db_config.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM conversations
                    WHERE conversation_id = %s AND user_id = %s
                """, (conversation_id, user_id))
                return cur.rowcount > 0

    # ============================================
    # 消息相关操作
    # ============================================

    def create_message(
        self,
        conversation_id: str,
        message_create: MessageCreate
    ) -> Message:
        """
        创建新消息

        Args:
            conversation_id: 会话ID
            message_create: 消息创建数据

        Returns:
            Message: 创建的消息对象
        """
        now = datetime.utcnow()

        with db_config.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 插入消息
                cur.execute("""
                    INSERT INTO messages (
                        conversation_id, role, content, metadata, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    conversation_id,
                    message_create.role,
                    message_create.content,
                    message_create.metadata or {},
                    now
                ))
                row = cur.fetchone()
                message = Message(**dict(row))

                # 更新会话的 last_message_at
                cur.execute("""
                    UPDATE conversations
                    SET last_message_at = %s, updated_at = %s
                    WHERE conversation_id = %s
                """, (now, now, conversation_id))

                return message

    def list_messages(
        self,
        conversation_id: str,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Message], int]:
        """
        获取会话的消息列表（分页）

        Args:
            conversation_id: 会话ID
            page: 页码（从1开始）
            page_size: 每页大小

        Returns:
            Tuple[List[Message], int]: (消息列表, 总数)
        """
        offset = (page - 1) * page_size

        with db_config.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 获取总数
                cur.execute("""
                    SELECT COUNT(*) as total FROM messages
                    WHERE conversation_id = %s
                """, (conversation_id,))
                total = cur.fetchone()['total']

                # 获取分页数据（按时间升序）
                cur.execute("""
                    SELECT * FROM messages
                    WHERE conversation_id = %s
                    ORDER BY created_at ASC
                    LIMIT %s OFFSET %s
                """, (conversation_id, page_size, offset))
                rows = cur.fetchall()
                messages = [Message(**dict(row)) for row in rows]

                return messages, total

    def get_conversation_with_messages(
        self,
        conversation_id: str,
        user_id: str,
        message_limit: int = 50
    ) -> Optional[ConversationWithMessages]:
        """
        获取会话及其最近的消息

        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            message_limit: 消息数量限制

        Returns:
            Optional[ConversationWithMessages]: 会话及消息或None
        """
        conversation = self.get_conversation_by_id(conversation_id, user_id)
        if not conversation:
            return None

        messages, _ = self.list_messages(conversation_id, page=1, page_size=message_limit)

        return ConversationWithMessages(
            **conversation.model_dump(),
            messages=messages
        )


# 创建单例实例
conversation_repository = ConversationRepository()
