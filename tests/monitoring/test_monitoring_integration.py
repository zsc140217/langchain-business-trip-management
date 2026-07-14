"""
监控系统集成测试
"""
import pytest
from unittest.mock import Mock
from src.monitoring import get_metrics_collector, initialize_langsmith
from src.monitoring.prometheus_exporter import track_request_metric, track_llm_call_metric
from src.monitoring.alert_manager import AlertManager, AlertmanagerWebhook, Alert


class TestLangSmithIntegration:
    """LangSmith集成测试"""

    def test_initialize_langsmith(self):
        """测试初始化LangSmith"""
        config = initialize_langsmith(project_name="test-project", tags=["test"])
        assert config is not None

class TestPrometheusMetrics:
    """Prometheus指标测试"""

    def test_track_request_metric(self):
        """测试追踪请求指标"""
        track_request_metric(0.5, success=True)
        track_request_metric(1.2, success=False)

    def test_track_llm_call_metric(self):
        """测试追踪LLM调用指标"""
        track_llm_call_metric("embedding", 0.3, cached=False)
        track_llm_call_metric("llm", 1.5, cached=True)


class TestAlertManager:
    """告警管理器测试"""

    @pytest.fixture
    def mock_feishu_client(self):
        """Mock飞书客户端"""
        client = Mock()
        return client

    @pytest.fixture
    def alert_manager(self, mock_feishu_client):
        """创建告警管理器"""
        return AlertManager(feishu_client=mock_feishu_client)

    def test_format_alert_message(self, alert_manager):
        """测试格式化告警消息"""
        webhook = AlertmanagerWebhook(
            version="4",
            groupKey="test-group",
            status="firing",
            receiver="feishu-webhook",
            groupLabels={"alertname": "HighErrorRate"},
            commonLabels={"severity": "critical"},
            commonAnnotations={"summary": "High error rate"},
            externalURL="http://alertmanager:9093",
            alerts=[
                Alert(
                    status="firing",
                    labels={"alertname": "HighErrorRate", "severity": "critical"},
                    annotations={"summary": "高错误率", "description": "错误率超标"},
                    startsAt="2024-01-01T00:00:00Z",
                )
            ],
        )
        message = alert_manager.format_alert_message(webhook)
        assert "CRITICAL" in message["title"]
        assert message["color"] == "red"

    def test_handle_alert(self, alert_manager, mock_feishu_client):
        """测试处理告警（同步版本）"""
        import asyncio
        webhook = AlertmanagerWebhook(
            version="4",
            groupKey="test",
            status="firing",
            receiver="feishu-webhook",
            groupLabels={},
            commonLabels={"severity": "warning"},
            commonAnnotations={},
            externalURL="http://localhost:9093",
            alerts=[
                Alert(
                    status="firing",
                    labels={"alertname": "Test"},
                    annotations={"summary": "Test", "description": "Test"},
                    startsAt="2024-01-01T00:00:00Z",
                )
            ],
        )
        result = asyncio.run(alert_manager.handle_alert(webhook))
        assert result["status"] == "success"
        # 验证告警历史已添加
        assert len(alert_manager.alert_history) > 0
        assert alert_manager.alert_history[0]["status"] == "firing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

class TestPhase4P1Metrics:
    """Phase 4 P1 新增指标测试"""

    def test_set_pending_approval_max_hours_manual(self):
        """测试设置人工审批超时 Gauge"""
        from src.monitoring.prometheus_exporter import (
            set_pending_approval_max_hours,
            pending_approval_max_hours,
            registry,
        )
        set_pending_approval_max_hours("manual", 25.5)
        from prometheus_client import generate_latest
        output = generate_latest(registry)
        assert b'manual' in output
        assert b'pending_approval_max_hours' in output
        pending_approval_max_hours.labels(type="manual").set(0)

    def test_set_pending_approval_max_hours_auto(self):
        """测试设置自动审批用时 Gauge"""
        from src.monitoring.prometheus_exporter import (
            set_pending_approval_max_hours,
            pending_approval_max_hours,
            registry,
        )
        set_pending_approval_max_hours("auto", 2.0)
        from prometheus_client import generate_latest
        output = generate_latest(registry)
        assert b'auto' in output
        pending_approval_max_hours.labels(type="auto").set(0)
