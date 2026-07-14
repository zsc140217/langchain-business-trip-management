"""
测试 submit_reimbursement 工具
Phase 3.3: Tool Layer
"""
import pytest
from unittest.mock import Mock, patch
from src.tools.submit_reimbursement_tool import SubmitReimbursementTool


class TestSubmitReimbursementTool:
    """测试提交报销工具"""

    def test_tool_basic_properties(self):
        """测试工具基本属性"""
        tool = SubmitReimbursementTool()

        assert tool.name == "submit_reimbursement"
        assert "报销" in tool.description
        assert "申请" in tool.description

    def test_submit_with_complete_parameters(self):
        """测试使用完整参数提交报销"""
        mock_engine = Mock()
        mock_engine.execute.return_value = {
            "status": "approved",
            "approval_id": "APV20260712001",
            "message": "自动审批通过"
        }

        tool = SubmitReimbursementTool(approval_engine=mock_engine)

        result = tool._run(
            user_id="user123",
            query="我去北京出差3天，花了800元",
            conversation_id="conv_001"
        )

        # 验证调用了 ApprovalEngine
        mock_engine.execute.assert_called_once_with(
            query="我去北京出差3天，花了800元",
            user_id="user123",
            conversation_id="conv_001"
        )

        # 验证返回结果
        assert "审批通过" in result or "APV20260712001" in result

    def test_submit_with_missing_user_id_raises_error(self):
        """测试缺少 user_id 抛出错误"""
        tool = SubmitReimbursementTool()

        with pytest.raises(ValueError, match="user_id.*不能为空|必需"):
            tool._run(
                user_id="",
                query="报销申请",
                conversation_id="conv_001"
            )

    def test_submit_with_missing_query_raises_error(self):
        """测试缺少 query 抛出错误"""
        tool = SubmitReimbursementTool()

        with pytest.raises(ValueError, match="query.*不能为空|必需"):
            tool._run(
                user_id="user123",
                query="",
                conversation_id="conv_001"
            )

    def test_submit_with_missing_conversation_id_uses_default(self):
        """测试缺少 conversation_id 使用默认值"""
        mock_engine = Mock()
        mock_engine.execute.return_value = {
            "status": "approved",
            "approval_id": "APV001",
            "message": "成功"
        }

        tool = SubmitReimbursementTool(approval_engine=mock_engine)

        result = tool._run(
            user_id="user123",
            query="报销申请",
            conversation_id=None
        )

        # 应该使用默认的 conversation_id
        call_args = mock_engine.execute.call_args
        assert call_args[1]["conversation_id"] is not None

    def test_approval_engine_execution_failure(self):
        """测试 ApprovalEngine 执行失败"""
        mock_engine = Mock()
        mock_engine.execute.side_effect = Exception("Engine error")

        tool = SubmitReimbursementTool(approval_engine=mock_engine)

        with pytest.raises(Exception, match="Engine error|执行失败"):
            tool._run(
                user_id="user123",
                query="报销申请",
                conversation_id="conv_001"
            )

    def test_lazy_initialization_of_approval_engine(self):
        """测试 ApprovalEngine 延迟初始化"""
        tool = SubmitReimbursementTool()

        # 初始状态未初始化
        assert not tool._initialized

        # 模拟执行（会触发延迟初始化）
        with patch.object(tool, '_lazy_init') as mock_init:
            try:
                tool._run(
                    user_id="user123",
                    query="报销",
                    conversation_id="conv_001"
                )
            except:
                pass  # 忽略错误，只测试初始化

            # 验证延迟初始化被调用
            mock_init.assert_called()

    def test_format_result_approved(self):
        """测试格式化审批通过结果"""
        mock_engine = Mock()
        mock_engine.execute.return_value = {
            "status": "approved",
            "approval_id": "APV20260712001",
            "message": "您的报销申请已自动通过！金额：¥800"
        }

        tool = SubmitReimbursementTool(approval_engine=mock_engine)

        result = tool._run(
            user_id="user123",
            query="报销800元",
            conversation_id="conv_001"
        )

        # 验证格式化后的结果包含关键信息
        assert "APV20260712001" in result
        assert "通过" in result or "approved" in result.lower()

    def test_format_result_pending(self):
        """测试格式化待审批结果"""
        mock_engine = Mock()
        mock_engine.execute.return_value = {
            "status": "pending",
            "approval_id": "APV20260712002",
            "message": "申请已提交，需要人工审批"
        }

        tool = SubmitReimbursementTool(approval_engine=mock_engine)

        result = tool._run(
            user_id="user456",
            query="报销2000元",
            conversation_id="conv_002"
        )

        # 验证格式化后的结果包含待审批信息
        assert "APV20260712002" in result
        assert "待" in result or "pending" in result.lower()

    def test_tool_inheritance_from_base_tool(self):
        """测试工具继承自 BaseTool"""
        from src.tools.base_tool import BaseTool

        tool = SubmitReimbursementTool()

        assert isinstance(tool, BaseTool)
        assert hasattr(tool, 'name')
        assert hasattr(tool, 'description')
        assert hasattr(tool, '_run')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
