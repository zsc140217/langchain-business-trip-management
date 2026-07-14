"""
测试工作记忆的审批状态管理功能
Phase 3.1: Working Memory Extension
"""
import pytest
from datetime import datetime, timedelta
from src.memory.working_memory import WorkingMemory, WorkingMemoryManager


class TestWorkingMemoryApprovalExtension:
    """测试 WorkingMemory 审批功能扩展"""

    def test_add_approval_with_valid_data(self):
        """测试添加有效的审批记录"""
        memory = WorkingMemory(conversation_id="test_001")

        approval_data = {
            "approval_id": "APV20240712001",
            "user_id": "user123",
            "destination": "北京",
            "days": 3,
            "amount": 1500,
            "status": "pending",
            "submit_time": datetime.now().isoformat(),
        }

        memory.add_approval(approval_data)

        # 验证审批记录已添加
        assert "approvals" in memory.__dict__
        assert "APV20240712001" in memory.approvals
        assert memory.approvals["APV20240712001"]["destination"] == "北京"
        assert memory.approvals["APV20240712001"]["status"] == "pending"

    def test_get_approval_by_id(self):
        """测试根据 ID 获取审批记录"""
        memory = WorkingMemory(conversation_id="test_002")

        approval_data = {
            "approval_id": "APV20240712002",
            "user_id": "user456",
            "destination": "上海",
            "days": 2,
            "amount": 800,
            "status": "approved",
            "submit_time": datetime.now().isoformat(),
        }

        memory.add_approval(approval_data)

        # 获取审批记录
        result = memory.get_approval("APV20240712002")

        assert result is not None
        assert result["destination"] == "上海"
        assert result["amount"] == 800
        assert result["status"] == "approved"

    def test_get_approval_nonexistent_returns_none(self):
        """测试获取不存在的审批记录返回 None"""
        memory = WorkingMemory(conversation_id="test_003")

        result = memory.get_approval("NONEXISTENT_ID")

        assert result is None

    def test_update_approval_status(self):
        """测试更新审批状态"""
        memory = WorkingMemory(conversation_id="test_004")

        approval_data = {
            "approval_id": "APV20240712003",
            "user_id": "user789",
            "destination": "深圳",
            "days": 4,
            "amount": 2000,
            "status": "pending",
            "submit_time": datetime.now().isoformat(),
        }

        memory.add_approval(approval_data)

        # 更新状态
        memory.update_approval_status(
            "APV20240712003",
            status="approved",
            approver="manager001",
            comment="批准出差"
        )

        # 验证状态已更新
        updated = memory.get_approval("APV20240712003")
        assert updated["status"] == "approved"
        assert updated["approver"] == "manager001"
        assert updated["comment"] == "批准出差"
        assert "approval_time" in updated

    def test_update_approval_status_nonexistent_raises_error(self):
        """测试更新不存在的审批记录抛出异常"""
        memory = WorkingMemory(conversation_id="test_005")

        with pytest.raises(ValueError, match="不存在"):
            memory.update_approval_status(
                "NONEXISTENT_ID",
                status="approved"
            )

    def test_get_pending_approvals(self):
        """测试获取所有待审批记录"""
        memory = WorkingMemory(conversation_id="test_006")

        # 添加多个审批记录
        approvals = [
            {
                "approval_id": "APV001",
                "user_id": "user123",
                "destination": "北京",
                "status": "pending",
                "amount": 1000,
                "days": 3,
                "submit_time": datetime.now().isoformat(),
            },
            {
                "approval_id": "APV002",
                "user_id": "user123",
                "destination": "上海",
                "status": "approved",
                "amount": 800,
                "days": 2,
                "submit_time": datetime.now().isoformat(),
            },
            {
                "approval_id": "APV003",
                "user_id": "user123",
                "destination": "深圳",
                "status": "pending",
                "amount": 1500,
                "days": 4,
                "submit_time": datetime.now().isoformat(),
            },
        ]

        for approval in approvals:
            memory.add_approval(approval)

        # 获取待审批记录
        pending = memory.get_pending_approvals()

        assert len(pending) == 2
        assert "APV001" in pending
        assert "APV003" in pending
        assert "APV002" not in pending

    def test_get_all_approvals(self):
        """测试获取所有审批记录"""
        memory = WorkingMemory(conversation_id="test_007")

        # 添加审批记录
        approval1 = {
            "approval_id": "APV001",
            "user_id": "user123",
            "destination": "北京",
            "status": "pending",
            "amount": 1000,
            "days": 3,
            "submit_time": datetime.now().isoformat(),
        }

        approval2 = {
            "approval_id": "APV002",
            "user_id": "user123",
            "destination": "上海",
            "status": "approved",
            "amount": 800,
            "days": 2,
            "submit_time": datetime.now().isoformat(),
        }

        memory.add_approval(approval1)
        memory.add_approval(approval2)

        # 获取所有审批记录
        all_approvals = memory.get_all_approvals()

        assert len(all_approvals) == 2
        assert "APV001" in all_approvals
        assert "APV002" in all_approvals

    def test_approval_immutability(self):
        """测试审批更新使用不可变模式"""
        memory = WorkingMemory(conversation_id="test_008")

        approval_data = {
            "approval_id": "APV20240712004",
            "user_id": "user999",
            "destination": "杭州",
            "days": 3,
            "amount": 1200,
            "status": "pending",
            "submit_time": datetime.now().isoformat(),
        }

        memory.add_approval(approval_data)

        # 获取原始数据的引用
        original = memory.get_approval("APV20240712004")
        original_status = original["status"]

        # 更新状态
        memory.update_approval_status(
            "APV20240712004",
            status="approved"
        )

        # 验证原始引用未被修改（不可变模式）
        # 注意：这个测试验证我们返回的是新字典，而不是修改原字典
        assert original["status"] == original_status  # 如果是可变的，这里会失败


class TestWorkingMemoryManagerApprovalIntegration:
    """测试 WorkingMemoryManager 与审批功能的集成"""

    def test_get_context_includes_approvals(self):
        """测试获取上下文时包含审批信息"""
        manager = WorkingMemoryManager()

        memory = manager.get_or_create("test_conv_001")

        approval_data = {
            "approval_id": "APV001",
            "user_id": "user123",
            "destination": "北京",
            "days": 3,
            "amount": 1500,
            "status": "pending",
            "submit_time": datetime.now().isoformat(),
        }

        memory.add_approval(approval_data)

        # 获取上下文
        context = memory.get_context()

        # 验证上下文包含审批信息
        assert "approvals" in context
        assert context["approvals"]["APV001"]["destination"] == "北京"

    def test_multi_user_approval_isolation(self):
        """测试多用户审批隔离"""
        manager = WorkingMemoryManager()

        # 用户1的审批
        memory1 = manager.get_or_create("conv_user1")
        approval1 = {
            "approval_id": "APV001",
            "user_id": "user1",
            "destination": "北京",
            "status": "pending",
            "amount": 1000,
            "days": 3,
            "submit_time": datetime.now().isoformat(),
        }
        memory1.add_approval(approval1)

        # 用户2的审批
        memory2 = manager.get_or_create("conv_user2")
        approval2 = {
            "approval_id": "APV002",
            "user_id": "user2",
            "destination": "上海",
            "status": "approved",
            "amount": 800,
            "days": 2,
            "submit_time": datetime.now().isoformat(),
        }
        memory2.add_approval(approval2)

        # 验证隔离
        user1_approvals = memory1.get_all_approvals()
        user2_approvals = memory2.get_all_approvals()

        assert len(user1_approvals) == 1
        assert len(user2_approvals) == 1
        assert "APV001" in user1_approvals
        assert "APV002" in user2_approvals
        assert "APV002" not in user1_approvals
        assert "APV001" not in user2_approvals

    def test_approval_survives_access_time_update(self):
        """测试审批记录在更新访问时间后仍然保留"""
        manager = WorkingMemoryManager()

        memory = manager.get_or_create("test_conv_002")

        approval_data = {
            "approval_id": "APV003",
            "user_id": "user123",
            "destination": "深圳",
            "days": 4,
            "amount": 2000,
            "status": "pending",
            "submit_time": datetime.now().isoformat(),
        }

        memory.add_approval(approval_data)

        # 更新访问时间
        memory.update_access_time()

        # 验证审批记录仍然存在
        result = memory.get_approval("APV003")
        assert result is not None
        assert result["destination"] == "深圳"

    def test_cleanup_expired_preserves_approvals(self):
        """测试清理过期记忆时审批记录被正确删除"""
        manager = WorkingMemoryManager(ttl_minutes=1)

        # 创建过期的记忆
        memory = manager.get_or_create("test_conv_003")

        approval_data = {
            "approval_id": "APV004",
            "user_id": "user123",
            "destination": "广州",
            "days": 3,
            "amount": 1200,
            "status": "pending",
            "submit_time": datetime.now().isoformat(),
        }

        memory.add_approval(approval_data)

        # 设置为过期（在添加审批后，因为add_approval会更新访问时间）
        memory.last_accessed = datetime.now() - timedelta(minutes=5)

        # 清理过期记忆
        manager.cleanup_expired()

        # 验证过期记忆已被删除（包括审批记录）
        assert "test_conv_003" not in manager.memory_store


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
