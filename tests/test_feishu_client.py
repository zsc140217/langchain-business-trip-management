"""
飞书客户端单元测试
测试 FeishuClient 的核心功能
"""

import pytest
from unittest.mock import Mock, patch
from src.harness.feishu_client import FeishuClient, determine_card_type


class TestFeishuClient:
    """测试 FeishuClient 类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.webhook_key = "test-webhook-key-123"
        self.client = FeishuClient(self.webhook_key)

    def test_init(self):
        """测试初始化"""
        assert self.client.webhook_url == f"https://open.feishu.cn/open-apis/bot/v2/hook/{self.webhook_key}"

    @patch('httpx.post')
    def test_send_text_message_success(self, mock_post):
        """测试发送文本消息成功"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"StatusCode": 0}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Act
        result = self.client.send_text_message("测试消息")

        # Assert
        assert result["StatusCode"] == 0
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "测试消息" in str(call_args)

    @patch('httpx.post')
    def test_send_card_message_success(self, mock_post):
        """测试发送卡片消息成功"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"StatusCode": 0}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Act
        result = self.client.send_card_message(
            title="测试标题",
            content="测试内容",
            card_type="success"
        )

        # Assert
        assert result["StatusCode"] == 0
        mock_post.assert_called_once()

        # 验证请求参数
        call_kwargs = mock_post.call_args.kwargs
        payload = call_kwargs.get('json', {})
        assert payload["msg_type"] == "interactive"
        assert payload["card"]["header"]["title"]["content"] == "测试标题"
        assert payload["card"]["header"]["template"] == "green"

    @patch('httpx.post')
    def test_send_card_message_all_types(self, mock_post):
        """测试所有卡片类型"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"StatusCode": 0}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        card_types = {
            "info": "blue",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }

        # Act & Assert
        for card_type, expected_color in card_types.items():
            self.client.send_card_message(
                title="测试",
                content="内容",
                card_type=card_type
            )

            call_kwargs = mock_post.call_args.kwargs
            payload = call_kwargs.get('json', {})
            assert payload["card"]["header"]["template"] == expected_color

    @patch('httpx.post')
    def test_send_message_http_error(self, mock_post):
        """测试 HTTP 错误处理"""
        # Arrange
        mock_post.side_effect = Exception("Network error")

        # Act
        result = self.client.send_text_message("测试")

        # Assert
        assert result["StatusCode"] == -1
        assert "error" in result
        assert "Network error" in result["error"]


class TestDetermineCardType:
    """测试 determine_card_type 函数"""

    def test_success_keywords(self):
        """测试成功关键词"""
        # Arrange & Act & Assert
        assert determine_card_type("审批通过") == "success"
        assert determine_card_type("✅ 恭喜通过") == "success"
        assert determine_card_type("恭喜您的申请已批准") == "success"

    def test_error_keywords(self):
        """测试失败关键词"""
        # Arrange & Act & Assert
        assert determine_card_type("申请被拒绝") == "error"
        assert determine_card_type("❌ 未通过审批") == "error"
        assert determine_card_type("很遗憾未通过") == "error"

    def test_warning_keywords(self):
        """测试警告关键词"""
        # Arrange & Act & Assert
        assert determine_card_type("需要人工审批") == "warning"
        assert determine_card_type("📋 待审批中") == "warning"
        assert determine_card_type("等待人工审批") == "warning"

    def test_info_default(self):
        """测试默认信息类型"""
        # Arrange & Act & Assert
        assert determine_card_type("您的申请已提交") == "info"
        assert determine_card_type("请等待处理") == "info"
        assert determine_card_type("") == "info"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.harness.feishu_client", "--cov-report=term-missing"])
