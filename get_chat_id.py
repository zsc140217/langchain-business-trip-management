"""
获取飞书群聊ID工具

使用此脚本获取机器人所在群聊的chat_id，用于发送交互卡片
"""
import os
import sys
sys.path.insert(0, '.')

import lark_oapi as lark
from lark_oapi.api.im.v1 import ListChatRequest

# 设置环境变量
os.environ['FEISHU_APP_ID'] = 'cli_aa8759bff078dcbd'
os.environ['FEISHU_APP_SECRET'] = 'ralUiiVIL2ryfvDxeR9Bhd67DEiGPyGC'

# 创建客户端
client = lark.Client.builder() \
    .app_id(os.getenv('FEISHU_APP_ID')) \
    .app_secret(os.getenv('FEISHU_APP_SECRET')) \
    .build()

print("=" * 80)
print("获取机器人所在的群聊列表")
print("=" * 80)

# 列出群聊
request = ListChatRequest.builder().build()

try:
    response = client.im.v1.chat.list(request)

    if response.success():
        print(f"\n找到 {len(response.data.items)} 个群聊:\n")

        for idx, chat in enumerate(response.data.items, 1):
            print(f"{idx}. 群聊名称: {chat.name}")
            print(f"   Chat ID: {chat.chat_id}")
            print(f"   描述: {chat.description or '无'}")
            print()

        if response.data.items:
            print("=" * 80)
            print("请复制上面的 Chat ID 用于发送审批卡片")
            print("=" * 80)
        else:
            print("没有找到群聊。请确保:")
            print("1. 机器人已被添加到群聊中")
            print("2. 应用已开通 im:chat 权限")
    else:
        print(f"[ERROR] 获取群聊列表失败:")
        print(f"  Code: {response.code}")
        print(f"  Msg: {response.msg}")

except Exception as e:
    print(f"[ERROR] 请求失败: {e}")
    print("\n可能的原因:")
    print("1. APP_ID 或 APP_SECRET 不正确")
    print("2. 缺少权限: im:chat")
    print("3. 网络连接问题")
