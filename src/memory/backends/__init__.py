"""
后端工厂 - 根据配置创建后端实例
"""

import os
from typing import Tuple
from .base import ShortTermBackend, LongTermBackend
from .file_backend import FileShortTermBackend, FileLongTermBackend


def create_backends(backend_type: str = None) -> Tuple[ShortTermBackend, LongTermBackend]:
    """
    创建记忆系统后端

    Args:
        backend_type: 后端类型，可选值：
            - "file": 文件存储（默认，零依赖）
            - "production": Redis + PostgreSQL（生产级）
            - None: 从环境变量读取 MEMORY_BACKEND

    Returns:
        (短期记忆后端, 长期记忆后端)

    Environment Variables:
        MEMORY_BACKEND: "file" | "production"
        REDIS_URL: Redis连接URL（默认：redis://localhost:6379/0）
        POSTGRES_URL: PostgreSQL连接URL（默认：postgresql://dev:dev123@localhost:5432/travel_agent）
    """
    if backend_type is None:
        backend_type = os.getenv("MEMORY_BACKEND", "file")

    if backend_type == "file":
        print("[FILE] 使用文件存储后端（开发模式）")
        short_term = FileShortTermBackend()
        long_term = FileLongTermBackend()
        return short_term, long_term

    elif backend_type == "production":
        print("[PRODUCTION] 使用生产级后端（Redis + PostgreSQL）")

        try:
            from .redis_backend import RedisShortTermBackend
            from .postgres_backend import PostgresLongTermBackend

            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            postgres_url = os.getenv("POSTGRES_URL", "postgresql://dev:dev123@localhost:5432/travel_agent")

            short_term = RedisShortTermBackend(redis_url)
            long_term = PostgresLongTermBackend(postgres_url)

            return short_term, long_term

        except ImportError as e:
            print(f"⚠️ 缺少依赖: {e}")
            print("请安装: pip install redis psycopg2-binary")
            print("回退到文件存储后端...")
            short_term = FileShortTermBackend()
            long_term = FileLongTermBackend()
            return short_term, long_term

        except ConnectionError as e:
            print(f"⚠️ 连接失败: {e}")
            print("请确保Redis和PostgreSQL服务已启动")
            print("回退到文件存储后端...")
            short_term = FileShortTermBackend()
            long_term = FileLongTermBackend()
            return short_term, long_term

    else:
        raise ValueError(f"不支持的后端类型: {backend_type}")


if __name__ == "__main__":
    print("=== 测试后端工厂 ===\n")

    # 测试文件后端
    print("1. 测试文件后端")
    short, long = create_backends("file")
    print(f"   短期记忆: {type(short).__name__}")
    print(f"   长期记忆: {type(long).__name__}")

    # 测试生产后端
    print("\n2. 测试生产后端（如果可用）")
    short, long = create_backends("production")
    print(f"   短期记忆: {type(short).__name__}")
    print(f"   长期记忆: {type(long).__name__}")

    print("\n✅ 测试完成")
