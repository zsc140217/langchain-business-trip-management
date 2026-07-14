# -*- coding: utf-8 -*-
"""
测试 MemoryService 扩展功能
- query_memory() 方法
- update_approval_status() 方法
"""
import pytest
from src.memory.memory_service import MemoryService


class TestMemoryServiceExtended:
    """测试 MemoryService 扩展功能"""

    @pytest.fixture
    def memory_service(self):
        """创建记忆服务实例"""
        return MemoryService()

    @pytest.fixture
    def user_id(self):
        """测试用户ID"""
        return "test_user_001"

    @pytest.fixture
    def conversation_id(self):
        """测试会话ID"""
        return "test_conv_001"

    def test_query_memory_empty(self, memory_service, user_id, conversation_id):
        """测试空记忆查询"""
        result = memory_service.query_memory(user_id, conversation_id, "测试")
        assert "未找到相关记忆信息" in result

    def test_query_memory_with_chat_history(
        self, memory_service, user_id, conversation_id
    ):
        """测试查询对话历史"""
        # 添加对话历史
        memory_service.process_user_message(user_id, conversation_id, "我要去北京出差")
        memory_service.process_assistant_message(conversation_id, "好的，需要查询天气吗？")

        # 查询包含"北京"的记忆
        result = memory_service.query_memory(user_id, conversation_id, "北京")

        assert "对话历史" in result
        assert "北京" in result

    def test_query_memory_with_working_memory(
        self, memory_service, user_id, conversation_id
    ):
        """测试查询工作记忆"""
        # 添加对话并触发实体提取
        memory_service.process_user_message(
            user_id, conversation_id, "我要去北京出差，拜访华为公司"
        )

        # 查询记忆
        result = memory_service.query_memory(user_id, conversation_id, "北京")

        # 应该包含当前上下文
        assert "当前上下文" in result or "涉及城市" in result

    def test_query_memory_with_approval(
        self, memory_service, user_id, conversation_id
    ):
        """测试查询审批记录"""
        # 添加审批记录
        working_memory = memory_service.working_memory_manager.get_or_create(
            conversation_id
        )
        approval_data = {
            "approval_id": "APV001",
            "user_id": user_id,
            "status": "pending",
            "amount": 1500,
        }
        working_memory.add_approval(approval_data)

        # 查询记忆
        result = memory_service.query_memory(user_id, conversation_id, "审批")

        assert "当前上下文" in result
        assert "审批记录" in result or "APV001" in result

    def test_update_approval_status(self, memory_service, user_id, conversation_id):
        """测试更新审批状态"""
        # 1. 添加初始审批记录
        working_memory = memory_service.working_memory_manager.get_or_create(
            conversation_id
        )
        approval_data = {
            "approval_id": "APV002",
            "user_id": user_id,
            "status": "pending",
            "amount": 2000,
        }
        working_memory.add_approval(approval_data)

        # 2. 更新审批状态
        memory_service.update_approval_status(
            user_id=user_id,
            conversation_id=conversation_id,
            approval_id="APV002",
            status="approved",
            approver="manager_001",
            comment="审批通过",
        )

        # 3. 验证更新结果
        updated_approval = working_memory.get_approval("APV002")
        assert updated_approval is not None
        assert updated_approval["status"] == "approved"
        assert updated_approval["approver"] == "manager_001"
        assert updated_approval["comment"] == "审批通过"
        assert "approval_time" in updated_approval

    def test_update_approval_status_nonexistent(
        self, memory_service, user_id, conversation_id
    ):
        """测试更新不存在的审批记录"""
        with pytest.raises(ValueError, match="审批记录 .* 不存在"):
            memory_service.update_approval_status(
                user_id=user_id,
                conversation_id=conversation_id,
                approval_id="NONEXISTENT",
                status="approved",
            )

    def test_update_approval_status_multiple_fields(
        self, memory_service, user_id, conversation_id
    ):
        """测试更新多个审批字段"""
        # 添加初始审批记录
        working_memory = memory_service.working_memory_manager.get_or_create(
            conversation_id
        )
        approval_data = {
            "approval_id": "APV003",
            "user_id": user_id,
            "status": "pending",
            "amount": 3000,
        }
        working_memory.add_approval(approval_data)

        # 更新多个字段
        memory_service.update_approval_status(
            user_id=user_id,
            conversation_id=conversation_id,
            approval_id="APV003",
            status="rejected",
            approver="manager_002",
            comment="预算超标",
            rejection_reason="超出预算限制",
        )

        # 验证所有字段都更新了
        updated_approval = working_memory.get_approval("APV003")
        assert updated_approval["status"] == "rejected"
        assert updated_approval["approver"] == "manager_002"
        assert updated_approval["comment"] == "预算超标"
        assert updated_approval["rejection_reason"] == "超出预算限制"

    def test_query_memory_integration(
        self, memory_service, user_id, conversation_id
    ):
        """测试记忆查询的集成场景"""
        # 1. 添加对话历史
        memory_service.process_user_message(user_id, conversation_id, "我要去上海出差")
        memory_service.process_assistant_message(conversation_id, "好的，查询上海的酒店")

        # 2. 添加审批记录
        working_memory = memory_service.working_memory_manager.get_or_create(
            conversation_id
        )
        approval_data = {
            "approval_id": "APV004",
            "user_id": user_id,
            "status": "approved",
            "amount": 800,
        }
        working_memory.add_approval(approval_data)

        # 3. 查询记忆
        result = memory_service.query_memory(user_id, conversation_id, "")

        # 4. 验证包含对话历史、上下文和审批记录
        assert len(result) > 0
        # 至少应该包含当前上下文或对话历史
        has_context = "当前上下文" in result or "对话历史" in result
        assert has_context


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
