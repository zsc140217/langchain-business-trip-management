"""
快速启动脚本
启动差旅审批 API 服务
"""

import os
import sys

# 设置环境变量（确保测试环境可用）
os.environ.setdefault("FEISHU_WEBHOOK_KEY", "557e5b9b-e431-486f-a26c-2b0509b73437")

# 启动 API
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 启动差旅审批 API 服务")
    print("=" * 60)
    print()
    print("📍 服务地址: http://localhost:8000")
    print("📖 API 文档: http://localhost:8000/docs")
    print("💚 健康检查: http://localhost:8000/health")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    print()

    # 导入并运行
    from src.harness.travel_approval_api import app
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
