"""
启动统一RAG-Agent架构 API
架构v2 - 集成飞书真实接入
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 检查必需的环境变量
required_vars = ["DASHSCOPE_API_KEY"]
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"[ERROR] Missing required environment variables: {', '.join(missing_vars)}")
    print("Please configure them in .env file")
    sys.exit(1)

# 检查可选的环境变量
if not os.getenv("FEISHU_WEBHOOK_KEY"):
    print("[WARN] FEISHU_WEBHOOK_KEY not configured, Feishu notification will use Mock client")
    print("       To enable Feishu notification, add FEISHU_WEBHOOK_KEY in .env file")

# 启动FastAPI应用
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")

    print("\n" + "=" * 80)
    print("Starting Unified RAG-Agent Architecture API v2.0")
    print("=" * 80)
    print(f"Service: http://{host}:{port}")
    print(f"API Docs: http://{host}:{port}/docs")
    print(f"Health Check: http://{host}:{port}/health")
    print(f"Test Feishu: http://{host}:{port}/api/test/feishu")
    print("=" * 80)
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(
        "src.api.unified_api:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
