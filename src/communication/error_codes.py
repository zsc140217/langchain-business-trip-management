# -*- coding: utf-8 -*-
"""
统一错误码体系
定义标准化的错误码和HTTP状态码映射
"""
from typing import Dict


class ErrorCode:
    """统一错误码

    错误码命名规范：
    - OK: 成功
    - 客户端错误 (4xx): BAD_REQUEST, UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INVALID_INPUT
    - 服务端错误 (5xx): INTERNAL_ERROR, SERVICE_UNAVAILABLE, TIMEOUT
    - 业务错误: LLM_CALL_FAILED, TOOL_CALL_FAILED 等

    使用示例:
        from src.communication import ErrorCode, StandardResponse

        response = StandardResponse.error_response(
            code=ErrorCode.UNAUTHORIZED,
            message="Token已过期"
        )
    """

    # 成功
    OK = "OK"

    # 客户端错误 (4xx)
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    INVALID_INPUT = "INVALID_INPUT"

    # 服务端错误 (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"

    # LLM相关错误
    LLM_CALL_FAILED = "LLM_CALL_FAILED"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"

    # 工具相关错误
    TOOL_CALL_FAILED = "TOOL_CALL_FAILED"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"

    # 记忆相关错误
    MEMORY_ERROR = "MEMORY_ERROR"
    MEMORY_NOT_FOUND = "MEMORY_NOT_FOUND"

    # 审批相关错误
    APPROVAL_NOT_FOUND = "APPROVAL_NOT_FOUND"
    APPROVAL_ALREADY_PROCESSED = "APPROVAL_ALREADY_PROCESSED"
    APPROVAL_INSUFFICIENT_INFO = "APPROVAL_INSUFFICIENT_INFO"

    # 飞书相关错误
    FEISHU_SEND_FAILED = "FEISHU_SEND_FAILED"
    FEISHU_WEBHOOK_ERROR = "FEISHU_WEBHOOK_ERROR"

    # 认证相关错误
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_USER_NOT_FOUND = "AUTH_USER_NOT_FOUND"
    AUTH_PASSWORD_INCORRECT = "AUTH_PASSWORD_INCORRECT"

    # 数据库相关错误
    DB_CONNECTION_FAILED = "DB_CONNECTION_FAILED"
    DB_QUERY_FAILED = "DB_QUERY_FAILED"

    # HTTP状态码映射
    HTTP_STATUS_MAP: Dict[str, int] = {
        OK: 200,
        BAD_REQUEST: 400,
        UNAUTHORIZED: 401,
        FORBIDDEN: 403,
        NOT_FOUND: 404,
        INVALID_INPUT: 422,
        INTERNAL_ERROR: 500,
        SERVICE_UNAVAILABLE: 503,
        TIMEOUT: 504,
        LLM_CALL_FAILED: 500,
        LLM_TIMEOUT: 504,
        LLM_RATE_LIMIT: 429,
        TOOL_CALL_FAILED: 500,
        TOOL_NOT_FOUND: 404,
        TOOL_TIMEOUT: 504,
        MEMORY_ERROR: 500,
        MEMORY_NOT_FOUND: 404,
        APPROVAL_NOT_FOUND: 404,
        APPROVAL_ALREADY_PROCESSED: 409,
        APPROVAL_INSUFFICIENT_INFO: 422,
        FEISHU_SEND_FAILED: 500,
        FEISHU_WEBHOOK_ERROR: 500,
        AUTH_TOKEN_EXPIRED: 401,
        AUTH_TOKEN_INVALID: 401,
        AUTH_USER_NOT_FOUND: 404,
        AUTH_PASSWORD_INCORRECT: 401,
        DB_CONNECTION_FAILED: 503,
        DB_QUERY_FAILED: 500,
    }

    @classmethod
    def to_http_status(cls, code: str) -> int:
        """将错误码转换为HTTP状态码"""
        return cls.HTTP_STATUS_MAP.get(code, 500)

    @classmethod
    def get_user_message(cls, code: str) -> str:
        """获取用户友好的错误消息（中文）"""
        messages = {
            cls.OK: "操作成功",
            cls.BAD_REQUEST: "请求参数错误",
            cls.UNAUTHORIZED: "未授权，请先登录",
            cls.FORBIDDEN: "无权访问该资源",
            cls.NOT_FOUND: "资源不存在",
            cls.INVALID_INPUT: "输入验证失败",
            cls.INTERNAL_ERROR: "服务器内部错误",
            cls.SERVICE_UNAVAILABLE: "服务暂时不可用",
            cls.TIMEOUT: "请求超时",
            cls.LLM_CALL_FAILED: "AI服务调用失败",
            cls.LLM_TIMEOUT: "AI服务响应超时",
            cls.LLM_RATE_LIMIT: "AI服务请求过于频繁",
            cls.TOOL_CALL_FAILED: "工具调用失败",
            cls.TOOL_NOT_FOUND: "工具不存在",
            cls.TOOL_TIMEOUT: "工具调用超时",
            cls.MEMORY_ERROR: "记忆服务错误",
            cls.MEMORY_NOT_FOUND: "记忆不存在",
            cls.APPROVAL_NOT_FOUND: "审批单不存在",
            cls.APPROVAL_ALREADY_PROCESSED: "审批单已处理",
            cls.APPROVAL_INSUFFICIENT_INFO: "审批信息不足",
            cls.FEISHU_SEND_FAILED: "飞书消息发送失败",
            cls.FEISHU_WEBHOOK_ERROR: "飞书回调处理错误",
            cls.AUTH_TOKEN_EXPIRED: "登录已过期，请重新登录",
            cls.AUTH_TOKEN_INVALID: "登录凭证无效",
            cls.AUTH_USER_NOT_FOUND: "用户不存在",
            cls.AUTH_PASSWORD_INCORRECT: "密码错误",
            cls.DB_CONNECTION_FAILED: "数据库连接失败",
            cls.DB_QUERY_FAILED: "数据库查询失败",
        }
        return messages.get(code, "未知错误")
