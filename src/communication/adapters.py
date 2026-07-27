"""
适配器模块 - 将通信层的StandardResponse转换为旧的API格式
保持前端向后兼容，实现渐进式重构
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException
from .protocol import StandardResponse
from .error_codes import ErrorCode
import logging

logger = logging.getLogger(__name__)


class LegacyAPIAdapter:
    """将StandardResponse转换为旧的API响应格式"""

    @staticmethod
    def to_chat_response(
        std_response: StandardResponse,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        转换为旧的ChatResponse格式

        旧格式:
        {
            "answer": str,
            "route": str,
            "user_id": str,
            "conversation_id": str
        }

        Args:
            std_response: 通信层的标准响应
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            旧格式的字典

        Raises:
            HTTPException: 如果响应失败
        """
        if std_response.success:
            data = std_response.data or {}

            return {
                "answer": data.get("answer", ""),
                "route": data.get("route", ""),
                "user_id": user_id,
                "conversation_id": conversation_id
            }
        else:
            # 错误情况：转换为HTTP异常（保持旧行为）
            http_status = ErrorCode.to_http_status(std_response.code)
            logger.error(
                f"[{std_response.trace_id}] Request failed: "
                f"code={std_response.code}, message={std_response.message}"
            )
            raise HTTPException(
                status_code=http_status,
                detail=std_response.message
            )

    @staticmethod
    def to_health_response(std_response: StandardResponse) -> Dict[str, Any]:
        """
        转换为旧的健康检查格式（保持向后兼容）

        旧格式:
        {
            "status": "healthy",
            "components": {...}
        }
        """
        if std_response.success:
            data = std_response.data or {}
            return {
                "status": data.get("status", "healthy"),
                "components": data.get("components", {})
            }
        else:
            return {
                "status": "unhealthy",
                "components": {}
            }
