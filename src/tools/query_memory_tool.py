# -*- coding: utf-8 -*-
"""
QueryMemoryTool - 记忆查询工具

用途：
- 查询用户的对话历史
- 查询当前会话上下文（实体、意图）
- 查询用户画像（常去城市、常见客户）
- 查询审批记录

对应架构文档：
- 工具系统：query_memory
- 记忆层：跨三层查询（ChatMemory + WorkingMemory + LongTermMemory）
"""
from typing import Optional
from src.tools.base_tool import BaseTool
from src.memory.memory_service import MemoryService
import logging

logger = logging.getLogger(__name__)


class QueryMemoryTool(BaseTool):
    """
    记忆查询工具

    功能：
    - 查询对话历史
    - 查询工作记忆（实体、意图、审批状态）
    - 查询长期记忆（用户画像）
    """

    name: str = "query_memory"
    description: str = """查询用户的记忆信息，包括：
    - 对话历史：最近的聊天记录
    - 当前上下文：涉及的城市、客户、日期、酒店、意图
    - 审批记录：当前会话中的审批单状态
    - 用户画像：历史对话数、常去城市、常见客户

参数：
- query: 查询内容（可选，用于过滤）
- user_id: 用户ID（必需）
- conversation_id: 会话ID（必需）

示例：
- query_memory(query="审批", user_id="user_001", conversation_id="conv_001")
- query_memory(query="北京", user_id="user_001", conversation_id="conv_001")
"""

    # 工具配置
    cache_enabled: bool = False  # 记忆查询不缓存，保证实时性
    max_retries: int = 1  # 记忆查询失败不重试

    def __init__(self, memory_service: MemoryService, **kwargs):
        """
        初始化记忆查询工具

        Args:
            memory_service: 记忆服务实例
        """
        super().__init__(**kwargs)
        self._memory_service = memory_service

    def _run(
        self,
        query: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        执行记忆查询

        Args:
            query: 查询内容（可选）
            user_id: 用户ID
            conversation_id: 会话ID
            **kwargs: 其他参数

        Returns:
            记忆查询结果

        Raises:
            ValueError: 参数缺失
        """
        # 参数验证
        if not user_id:
            return "错误：缺少 user_id 参数"

        if not conversation_id:
            return "错误：缺少 conversation_id 参数"

        # 默认查询内容
        if not query:
            query = ""

        try:
            # 调用记忆服务查询
            result = self._memory_service.query_memory(
                user_id=user_id,
                conversation_id=conversation_id,
                query=query
            )

            logger.info(f"[QueryMemoryTool] 查询成功: user_id={user_id}, conv_id={conversation_id}")
            return result

        except Exception as e:
            logger.error(f"[QueryMemoryTool] 查询失败: {e}", exc_info=True)
            return f"记忆查询失败: {str(e)}"

    def execute(
        self,
        query: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        便捷执行方法（兼容旧接口）

        Args:
            query: 查询内容
            user_id: 用户ID
            conversation_id: 会话ID
            **kwargs: 其他参数

        Returns:
            记忆查询结果
        """
        return self._run(
            query=query,
            user_id=user_id,
            conversation_id=conversation_id,
            **kwargs
        )


if __name__ == "__main__":
    # 测试代码
    from src.memory.memory_service import MemoryService

    print("=== 测试 QueryMemoryTool ===")

    # 创建记忆服务
    memory_service = MemoryService()

    # 模拟对话数据
    user_id = "test_user_001"
    conv_id = "test_conv_001"

    # 添加对话历史
    memory_service.process_user_message(user_id, conv_id, "我要去北京出差")
    memory_service.process_assistant_message(conv_id, "好的，请问您需要查询什么？")

    # 创建工具
    tool = QueryMemoryTool(memory_service=memory_service)

    # 测试查询
    print("\n1. 查询北京相关记忆")
    result = tool.execute(query="北京", user_id=user_id, conversation_id=conv_id)
    print(result)

    print("\n2. 查询所有记忆")
    result = tool.execute(user_id=user_id, conversation_id=conv_id)
    print(result)

    print("\n3. 测试参数缺失")
    result = tool.execute(query="测试")
    print(result)

    print("\n[OK] 测试完成")
