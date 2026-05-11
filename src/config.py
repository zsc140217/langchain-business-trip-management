"""
配置文件
加载环境变量和全局配置
"""
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# API配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
QWEATHER_API_KEY = os.getenv("QWEATHER_API_KEY")

# 服务配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# 模型配置
DEFAULT_MODEL = "qwen-plus"
DEFAULT_TEMPERATURE = 0.7
EMBEDDING_MODEL = "text-embedding-v1"

# RAG配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5

# 数据路径
DATA_DIR = "data"
TRAVEL_POLICY_PATH = os.path.join(DATA_DIR, "travel_policy.txt")
