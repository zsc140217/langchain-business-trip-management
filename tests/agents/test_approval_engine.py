"""
测试 ApprovalEngine - 审批域执行器
Phase 3.2: ApprovalEngine Core
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from src.agents.approval_engine import ApprovalEngine


class TestApprovalEngineAutoApproval:
    """测试自动审批流程（金额 < 1000元）"""

    def test_auto_approval_under_threshold(self):
        """测试金额低于阈值时自动审批"""
        # Mock dependencies
        mock_llm = Mock()
        mock_memory = Mock()
        mock_feishu = Mock()
        mock_graph = Mock()

        engine = ApprovalEngine(
            llm=mock_llm,
            memory_service=mock_memory,
            feishu_client=mock_feishu,
            approval_graph=mock_graph,
            auto_approval_threshold=1000
        )

        query = "我要报销去北京的出差费用，3天，花了800元"
        user_id = "user123"
        conversation_id = "conv_001"

        # Mock info extraction
        mock_info = {
            "user_id": user_id,
            "destination": "北京",
            "days": 3,
            "estimated_amount": 800,
            "query": query,
        }

        with patch.object(engine, '_extract_application_info', return_value=mock_info):
            with patch.object(engine, '_auto_approve') as mock_auto_approve:
                mock_auto_approve.return_value = {
                    "status": "approved",
                    "message": "自动审批通过",
                    "approval_id": "APV001"
                }

                result = engine.execute(query, user_id, conversation_id)

                # 验证调用了自动审批
                mock_auto_approve.assert_called_once()
                assert result["status"] == "approved"
                assert "APV001" in result["approval_id"]

    def test_auto_approval_sends_feishu_notification(self):
        """测试自动审批发送飞书通知"""
        mock_llm = Mock()
        mock_memory = Mock()
        mock_feishu = Mock()
        mock_graph = Mock()
        mock_graph.invoke.return_value = {"approval_status": "approved"}

        engine = ApprovalEngine(
            llm=mock_llm,
            memory_service=mock_memory,
            feishu_client=mock_feishu,
            approval_graph=mock_graph
        )

        approval_info = {
            "approval_id": "APV001",
            "user_id": "user123",
            "destination": "北京",
            "days": 3,
            "estimated_amount": 800,
        }

        result = engine._auto_approve(approval_info)

        # 验证飞书通知被调用
        mock_feishu.send_card_message.assert_called_once()
        call_args = mock_feishu.send_card_message.call_args
        assert "审批通过" in call_args[1]["title"] or "通过" in call_args[1]["title"]
        assert call_args[1]["card_type"] == "success"

    def test_auto_approval_updates_working_memory(self):
        """测试自动审批更新工作记忆"""
        mock_llm = Mock()
        mock_memory = Mock()
        mock_working_memory = Mock()
        mock_memory.working_memory_manager.get_or_create.return_value = mock_working_memory
        mock_feishu = Mock()
        mock_graph = Mock()
        mock_graph.invoke.return_value = {"approval_status": "approved"}

        engine = ApprovalEngine(
            llm=mock_llm,
            memory_service=mock_memory,
            feishu_client=mock_feishu,
            approval_graph=mock_graph
        )

        approval_info = {
            "approval_id": "APV001",
            "user_id": "user123",
            "destination": "北京",
            "days": 3,
            "estimated_amount": 800,
        }

        result = engine._auto_approve(approval_info)

        # 验证工作记忆被更新
        mock_memory.working_memory_manager.get_or_create.assert_called()
        mock_working_memory.add_approval.assert_called_once()


class TestApprovalEngineManualApproval:
    """测试人工审批流程（金额 >= 1000元）"""

    def test_manual_approval_over_threshold(self):
        """测试金额达到阈值时触发人工审批"""
        mock_llm = Mock()
        mock_memory = Mock()
        mock_feishu = Mock()
        mock_graph = Mock()

        engine = ApprovalEngine(
            llm=mock_llm,
            memory_service=mock_memory,
            feishu_client=mock_feishu,
            approval_graph=mock_graph,
            auto_approval_threshold=1000
        )

        query = "我要报销去上海的出差费用，5天，花了2500元"
        user_id = "user456"
        conversation_id = "conv_002"

        mock_info = {
            "user_id": user_id,
            "destination": "上海",
            "days": 5,
            "estimated_amount": 2500,
            "query": query,
        }

        with patch.object(engine, '_extract_application_info', return_value=mock_info):
            with patch.object(engine, '_manual_approval') as mock_manual:
                mock_manual.return_value = {
                    "status": "pending",
                    "message": "申请已提交，需要人工审批",
                    "approval_id": "APV002"
                }

                result = engine.execute(query, user_id, conversation_id)

                # 验证调用了人工审批
                mock_manual.assert_called_once()
                assert result["status"] == "pending"

    def test_manual_approval_sends_feishu_card_to_approver(self):
        """测试人工审批发送飞书卡片给审批人"""
        mock_llm = Mock()
        mock_memory = Mock()
        mock_feishu = Mock()
        mock_graph = Mock()

        engine = ApprovalEngine(
            llm=mock_llm,
            memory_service=mock_memory,
            feishu_client=mock_feishu,
            approval_graph=mock_graph
        )

        approval_info = {
            "approval_id": "APV002",
            "user_id": "user456",
            "destination": "上海",
            "days": 5,
            "estimated_amount": 2500,
        }

        result = engine._manual_approval(approval_info)

        # 验证飞书通知被调用
        mock_feishu.send_card_message.assert_called_once()
        call_args = mock_feishu.send_card_message.call_args
        assert "审批" in call_args[1]["title"]
        assert call_args[1]["card_type"] == "warning"

    def test_manual_approval_updates_memory_with_pending_status(self):
        """测试人工审批更新工作记忆为待审批状态"""
        mock_llm = Mock()
        mock_memory = Mock()
        mock_working_memory = Mock()
        mock_memory.working_memory_manager.get_or_create.return_value = mock_working_memory
        mock_feishu = Mock()
        mock_graph = Mock()

        engine = ApprovalEngine(
            llm=mock_llm,
            memory_service=mock_memory,
            feishu_client=mock_feishu,
            approval_graph=mock_graph
        )

        approval_info = {
            "approval_id": "APV002",
            "user_id": "user456",
            "destination": "上海",
            "days": 5,
            "estimated_amount": 2500,
        }

        result = engine._manual_approval(approval_info)

        # 验证工作记忆被更新为 pending 状态
        mock_working_memory.add_approval.assert_called_once()
        call_args = mock_working_memory.add_approval.call_args[0][0]
        assert call_args["status"] == "pending"


class TestApprovalEngineInfoExtraction:
    """测试申请信息提取"""

    def test_extract_application_info_with_complete_data(self):
        """测试从完整查询中提取申请信息"""
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"destination": "北京", "days": 3, "estimated_amount": 800}'
        )
        mock_memory = Mock()
        mock_feishu = Mock()
        mock_graph = Mock()

        engine = ApprovalEngine(
            llm=mock_llm,
            memory_service=mock_memory,
            feishu_client=mock_feishu,
            approval_graph=mock_graph
        )

        query = "我要报销去北京出差的费用，去了3天，花了800元"
        user_id = "user123"

        result = engine._extract_application_info(query, user_id)

        assert result["destination"] == "北京"
        assert result["days"] == 3
        assert result["estimated_amount"] == 800
        assert result["user_id"] == user_id
        assert "approval_id" in result

    def test_extract_application_info_with_missing_amount(self):
        """测试缺少金额时估算费用"""
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(
            content='{"destination": "上海", "days": 2, "estimated_amount": null}'
        )
        mock_memory = Mock()
        mock_feishu = Mock()
        mock_graph = Mock()

        engine = ApprovalEngine(
            llm=mock_llm,
            memory_service=mock_memory,
            feishu_client=mock_feishu,
            approval_graph=mock_graph
        )

        query = "我去上海出差了2天，要报销"
        user_id = "user456"

        with patch.object(engine, '_estimate_amount', return_value=1200):
            result = engine._extract_application_info(query, user_id)

            assert result["destination"] == "上海"
            assert result["days"] == 2
            assert result["estimated_amount"] == 1200

    def test_generate_approval_id_format(self):
        """测试审批单号生成格式"""
        mock_llm = Mock()
        mock_memory = Mock()
        mock_feishu = Mock()
        mock_graph = Mock()

        engine = ApprovalEngine(
            llm=mock_llm,
            memory_service=mock_memory,
            feishu_client=mock_feishu,
            approval_graph=mock_graph
        )

        approval_id = engine._generate_approval_id()

        # 验证格式: APV + YYYYMMDD + 序列号
        assert approval_id.startswith("APV")
        assert len(approval_id) >= 14  # APV + 8位日期 + 至少3位序列号


class TestApprovalEngineErrorHandling:
    """测试错误处理"""

    def test_feishu_notification_failure_does_not_block_approval(self):
        """测试飞书通知失败不阻塞审批流程"""
        mock_llm = Mock()
        mock_memory = Mock()
        mock_working_memory = Mock()
        mock_memory.working_memory_manager.get_or_create.return_value = mock_working_memory
        mock_feishu = Mock()
        mock_feishu.send_card_message.side_effect = Exception("Feishu API timeout")
        mock_graph = Mock()
        mock_graph.invoke.return_value = {"approval_status": "approved"}

        engine = ApprovalEngine(
            llm=mock_llm,
            memory_service=mock_memory,
            feishu_client=mock_feishu,
            approval_graph=mock_graph
        )

        approval_info = {
            "approval_id": "APV001",
            "user_id": "user123",
            "destination": "北京",
            "days": 3,
            "estimated_amount": 800,
        }

        # 应该成功返回，即使飞书通知失败
        result = engine._auto_approve(approval_info)

        assert result["status"] == "approved"
        # 工作记忆仍然被更新
        mock_working_memory.add_approval.assert_called_once()

    def test_invalid_query_extraction_returns_error(self):
        """测试无效查询提取返回错误"""
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content='invalid json')
        mock_memory = Mock()
        mock_feishu = Mock()
        mock_graph = Mock()

        engine = ApprovalEngine(
            llm=mock_llm,
            memory_service=mock_memory,
            feishu_client=mock_feishu,
            approval_graph=mock_graph
        )

        query = "一些无关的内容"
        user_id = "user789"

        with pytest.raises(ValueError, match="提取.*失败|无法.*解析"):
            engine._extract_application_info(query, user_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
