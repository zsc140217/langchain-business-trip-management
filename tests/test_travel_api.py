"""
差旅审批 API 集成测试
测试 FastAPI 端点的完整功能
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os

# 设置测试环境变量
os.environ["FEISHU_WEBHOOK_KEY"] = "test-webhook-key"
os.environ["DASHSCOPE_API_KEY"] = "test-api-key"

from src.harness.travel_approval_api import app


class TestTravelApprovalAPI:
    """测试差旅审批 API"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """测试根路径"""
        # Act
        response = self.client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "差旅审批 API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data

    def test_health_check(self):
        """测试健康检查"""
        # Act
        response = self.client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "feishu_configured" in data

    @patch('src.harness.travel_approval_api.graph')
    @patch('src.harness.travel_approval_api.feishu_client')
    def test_submit_travel_application_success(self, mock_feishu, mock_graph):
        """测试提交差旅申请成功"""
        # Arrange
        mock_graph.invoke.return_value = {
            "answer": "✅ 审批通过！您的差旅申请符合公司标准。",
            "iteration": 2
        }
        mock_feishu.send_card_message.return_value = {"StatusCode": 0}

        request_data = {
            "destination": "上海",
            "start_date": "2026-06-20",
            "end_date": "2026-06-22",
            "purpose": "客户拜访",
            "user_name": "张三"
        }

        # Act
        response = self.client.post("/api/travel/submit", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "审批通过" in data["approval_result"]
        assert data["feishu_sent"] is True
        assert data["iteration"] == 2
        assert "上海" in data["query"]

        # 验证调用
        mock_graph.invoke.assert_called_once()
        mock_feishu.send_card_message.assert_called_once()

    @patch('src.harness.travel_approval_api.graph')
    @patch('src.harness.travel_approval_api.feishu_client')
    def test_submit_travel_application_rejection(self, mock_feishu, mock_graph):
        """测试差旅申请被拒绝"""
        # Arrange
        mock_graph.invoke.return_value = {
            "answer": "❌ 申请被拒绝：出差预算超标。",
            "iteration": 1
        }
        mock_feishu.send_card_message.return_value = {"StatusCode": 0}

        request_data = {
            "destination": "纽约",
            "start_date": "2026-07-01",
            "end_date": "2026-07-10",
            "purpose": "会议",
            "user_name": "李四"
        }

        # Act
        response = self.client.post("/api/travel/submit", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "拒绝" in data["approval_result"]

        # 验证飞书卡片类型
        call_args = mock_feishu.send_card_message.call_args
        assert call_args.kwargs["card_type"] == "error"

    @patch('src.harness.travel_approval_api.graph')
    @patch('src.harness.travel_approval_api.feishu_client')
    def test_submit_travel_application_manual_approval(self, mock_feishu, mock_graph):
        """测试需要人工审批"""
        # Arrange
        mock_graph.invoke.return_value = {
            "answer": "📋 需要人工审批：出差时间较长。",
            "iteration": 1
        }
        mock_feishu.send_card_message.return_value = {"StatusCode": 0}

        request_data = {
            "destination": "深圳",
            "start_date": "2026-06-25",
            "end_date": "2026-07-05",
            "purpose": "项目调研",
            "user_name": "王五"
        }

        # Act
        response = self.client.post("/api/travel/submit", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "人工审批" in data["approval_result"]

        # 验证飞书卡片类型
        call_args = mock_feishu.send_card_message.call_args
        assert call_args.kwargs["card_type"] == "warning"

    @patch('src.harness.travel_approval_api.graph')
    @patch('src.harness.travel_approval_api.feishu_client')
    def test_submit_travel_application_feishu_failure(self, mock_feishu, mock_graph):
        """测试飞书发送失败"""
        # Arrange
        mock_graph.invoke.return_value = {
            "answer": "审批通过",
            "iteration": 1
        }
        mock_feishu.send_card_message.return_value = {"StatusCode": -1, "error": "Network error"}

        request_data = {
            "destination": "北京",
            "start_date": "2026-06-30",
            "end_date": "2026-07-02",
            "purpose": "培训",
            "user_name": "赵六"
        }

        # Act
        response = self.client.post("/api/travel/submit", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["feishu_sent"] is False  # 飞书发送失败

    @patch('src.harness.travel_approval_api.graph')
    def test_submit_travel_application_error(self, mock_graph):
        """测试处理异常"""
        # Arrange
        mock_graph.invoke.side_effect = Exception("LangGraph error")

        request_data = {
            "destination": "杭州",
            "start_date": "2026-07-10",
            "end_date": "2026-07-12",
            "purpose": "技术交流",
            "user_name": "孙七"
        }

        # Act
        response = self.client.post("/api/travel/submit", json=request_data)

        # Assert
        assert response.status_code == 500
        assert "处理失败" in response.json()["detail"]

    def test_submit_travel_application_missing_fields(self):
        """测试缺少必填字段"""
        # Arrange
        request_data = {
            "destination": "广州"
            # 缺少其他必填字段
        }

        # Act
        response = self.client.post("/api/travel/submit", json=request_data)

        # Assert
        assert response.status_code == 422  # Validation error

    @patch('src.harness.travel_approval_api.graph')
    @patch('src.harness.travel_approval_api.feishu_client')
    def test_submit_travel_application_default_user_name(self, mock_feishu, mock_graph):
        """测试默认用户名"""
        # Arrange
        mock_graph.invoke.return_value = {"answer": "通过", "iteration": 1}
        mock_feishu.send_card_message.return_value = {"StatusCode": 0}

        request_data = {
            "destination": "成都",
            "start_date": "2026-08-01",
            "end_date": "2026-08-03",
            "purpose": "市场调研"
            # 不提供 user_name，使用默认值
        }

        # Act
        response = self.client.post("/api/travel/submit", json=request_data)

        # Assert
        assert response.status_code == 200

        # 验证飞书消息标题使用了默认名称
        call_args = mock_feishu.send_card_message.call_args
        assert "员工" in call_args.kwargs["title"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.harness.travel_approval_api", "--cov-report=term-missing"])
