# -*- coding: utf-8 -*-
"""
飞书 WebSocket 长连接客户端
使用 lark-oapi SDK 建立长连接接收回调
"""

import logging
import os
from typing import Optional
import lark_oapi as lark
from lark_oapi.event.callback.model.p2_card_action_trigger import (
    P2CardActionTrigger,
    P2CardActionTriggerResponse
)

from .feishu_callback_handler import FeishuCallbackHandler

logger = logging.getLogger(__name__)


class FeishuWSClient:
    """
    飞书 WebSocket 长连接客户端

    通过长连接接收卡片交互回调，无需公网IP
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        verification_token: Optional[str] = None,
        encrypt_key: Optional[str] = None,
        callback_handler: Optional[FeishuCallbackHandler] = None
    ):
        """
        初始化飞书长连接客户端

        Args:
            app_id: 飞书应用 APP_ID（可从环境变量读取）
            app_secret: 飞书应用 APP_SECRET（可从环境变量读取）
            verification_token: 事件订阅 Verification Token（可从环境变量读取）
            encrypt_key: 事件订阅 Encrypt Key（可选，可从环境变量读取）
            callback_handler: 回调处理器
        """
        self.app_id = app_id or os.getenv("FEISHU_APP_ID")
        self.app_secret = app_secret or os.getenv("FEISHU_APP_SECRET")
        self.verification_token = verification_token or os.getenv("FEISHU_VERIFICATION_TOKEN", "")
        self.encrypt_key = encrypt_key or os.getenv("FEISHU_ENCRYPT_KEY", "")
        self.callback_handler = callback_handler

        if not self.app_id or not self.app_secret:
            raise ValueError(
                "FEISHU_APP_ID 和 FEISHU_APP_SECRET 必须配置\n"
                "可通过环境变量或构造函数参数传入"
            )

        # 初始化 WebSocket 客户端（延迟创建）
        self.ws_client: Optional[lark.ws.Client] = None
        self.is_running = False

    def start(self):
        """
        启动长连接客户端

        主线程将阻塞，直到进程结束
        """
        if self.is_running:
            logger.warning("[FeishuWS] 客户端已在运行中")
            return

        logger.info("[FeishuWS] 初始化飞书长连接客户端")

        # 创建事件处理器
        event_handler = self._create_event_handler()

        # 创建 WebSocket 客户端
        self.ws_client = lark.ws.Client(
            self.app_id,
            self.app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.INFO
        )

        # 启动客户端（阻塞主线程）
        logger.info("[FeishuWS] 启动长连接，等待回调...")
        self.is_running = True

        try:
            self.ws_client.start()
        except Exception as e:
            logger.error(f"[FeishuWS] 启动失败: {e}", exc_info=True)
            self.is_running = False
            raise

    def stop(self):
        """
        停止长连接客户端
        """
        if not self.is_running:
            return

        logger.info("[FeishuWS] 停止长连接客户端")
        self.is_running = False

        # 注意：lark.ws.Client 没有提供 stop() 方法
        # 需要手动终止进程或使用异步版本

    def _create_event_handler(self) -> lark.EventDispatcherHandler:
        """
        创建事件处理器

        Returns:
            事件处理器
        """
        # 定义卡片交互回调处理函数
        def do_card_action_trigger(
            data: P2CardActionTrigger
        ) -> P2CardActionTriggerResponse:
            """处理卡片交互回调"""
            # 添加详细的调试日志
            print(f"\n{'='*80}")
            print(f"[DEBUG] 收到卡片交互回调！")
            print(f"{'='*80}")

            try:
                # 打印原始数据
                raw_data = lark.JSON.marshal(data)
                print(f"[DEBUG] 原始事件数据: {raw_data}")
                logger.debug(f"[FeishuWS] 完整事件数据: {raw_data}")
                logger.info(f"[FeishuWS] 收到卡片交互回调")

                # 调用回调处理器
                if self.callback_handler:
                    response = self.callback_handler.handle_card_action(data)
                    logger.info(f"[FeishuWS] 回调处理成功")
                    print(f"[DEBUG] 回调处理成功")
                    return response
                else:
                    logger.warning("[FeishuWS] 回调处理器未配置，返回默认响应")
                    print(f"[DEBUG] 回调处理器未配置")
                    return P2CardActionTriggerResponse({
                        "toast": {
                            "type": "info",
                            "content": "回调处理器未配置"
                        }
                    })

            except Exception as e:
                logger.error(f"[FeishuWS] 处理卡片交互失败: {e}", exc_info=True)
                print(f"[DEBUG] 处理失败: {e}")
                return P2CardActionTriggerResponse({
                    "toast": {
                        "type": "error",
                        "content": f"处理失败: {str(e)}"
                    }
                })

        # 创建事件分发器
        # 注意：长连接模式下，这两个参数必须传空字符串（根据飞书官方文档）
        logger.info(f"[FeishuWS] 创建事件处理器（长连接模式使用空字符串作为 token 和 encrypt_key）")

        event_handler = lark.EventDispatcherHandler.builder("", "") \
            .register_p2_card_action_trigger(do_card_action_trigger) \
            .build()

        logger.info(f"[FeishuWS] 事件处理器创建完成，已注册 card_action_trigger 回调")
        return event_handler
