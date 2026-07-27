"""
告警通知管理器
接收Alertmanager Webhook，推送到飞书
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Alert(BaseModel):
    """单个告警"""
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: str
    endsAt: str = ""
    generatorURL: str = ""


class AlertmanagerWebhook(BaseModel):
    """Alertmanager Webhook格式"""
    version: str
    groupKey: str
    status: str
    receiver: str
    groupLabels: Dict[str, str]
    commonLabels: Dict[str, str]
    commonAnnotations: Dict[str, str]
    externalURL: str
    alerts: List[Alert]


class AlertManager:
    """告警管理器"""

    def __init__(self, feishu_client=None):
        self.feishu_client = feishu_client
        self.alert_history: List[Dict[str, Any]] = []

    def format_alert_message(self, webhook: AlertmanagerWebhook) -> Dict[str, Any]:
        """格式化告警消息为飞书卡片格式"""
        color_map = {"critical": "red", "warning": "orange", "info": "blue"}
        severity = webhook.commonLabels.get("severity", "info")
        color = color_map.get(severity, "grey")

        status_emoji = {"firing": "[重要]", "resolved": "[OK]"}
        emoji = status_emoji.get(webhook.status, "[WARNING]")

        content_lines = []
        for idx, alert in enumerate(webhook.alerts, 1):
            alertname = alert.labels.get("alertname", "Unknown")
            summary = alert.annotations.get("summary", "No summary")
            description = alert.annotations.get("description", "No description")
            content_lines.append(f"**告警{idx}**: {alertname}")
            content_lines.append(f"  • {summary}")
            content_lines.append(f"  • {description}")
            content_lines.append("")

        content = "\n".join(content_lines)
        alert_count = len(webhook.alerts)
        title = f"{emoji} [{severity.upper()}] {alert_count}个告警 - {webhook.status.upper()}"

        return {"title": title, "content": content, "color": color}

    async def handle_alert(self, webhook: AlertmanagerWebhook) -> Dict[str, str]:
        """处理告警webhook"""
        logger.info(f"收到告警: {webhook.status}, {len(webhook.alerts)}个告警")

        self.alert_history.append({
            "timestamp": datetime.now().isoformat(),
            "status": webhook.status,
            "severity": webhook.commonLabels.get("severity", "info"),
            "alert_count": len(webhook.alerts),
            "group_key": webhook.groupKey,
        })

        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]

        if self.feishu_client:
            try:
                message = self.format_alert_message(webhook)
                await self.feishu_client.send_card_message(**message)
                logger.info("告警已推送到飞书")
            except Exception as e:
                logger.error(f"推送告警到飞书失败: {e}")

        return {"status": "success", "message": "Alert processed"}

    def get_alert_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取告警历史"""
        return self.alert_history[-limit:]
