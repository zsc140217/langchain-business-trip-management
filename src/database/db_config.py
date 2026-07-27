# -*- coding: utf-8 -*-
"""
数据库配置和连接池管理
P0-2: 统一数据库连接
创建日期: 2026-07-15
"""

import os
from typing import Optional
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor


class DatabaseConfig:
    """数据库配置单例"""

    _instance: Optional['DatabaseConfig'] = None
    _connection_pool: Optional[pool.SimpleConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化数据库连接配置"""
        if not hasattr(self, 'initialized'):
            self.config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'database': os.getenv('DB_NAME', 'business_trip'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', '')
            }
            self.initialized = True

    def get_connection_pool(self) -> pool.SimpleConnectionPool:
        """
        获取连接池实例（懒加载）

        Returns:
            pool.SimpleConnectionPool: 数据库连接池
        """
        if self._connection_pool is None:
            min_conn = int(os.getenv('DB_POOL_MIN', '2'))
            max_conn = int(os.getenv('DB_POOL_MAX', '10'))

            self._connection_pool = pool.SimpleConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                **self.config
            )
        return self._connection_pool

    @contextmanager
    def get_connection(self, dict_cursor: bool = True):
        """
        获取数据库连接（上下文管理器）

        Args:
            dict_cursor: 是否使用字典游标（默认True）

        Yields:
            connection: 数据库连接对象
        """
        conn_pool = self.get_connection_pool()
        conn = conn_pool.getconn()

        try:
            if dict_cursor:
                conn.cursor_factory = RealDictCursor
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn_pool.putconn(conn)

    def close_all_connections(self):
        """关闭所有连接（应用退出时调用）"""
        if self._connection_pool is not None:
            self._connection_pool.closeall()
            self._connection_pool = None


# 全局单例实例
db_config = DatabaseConfig()


# ============================================================
# 便捷函数：用于Repository层的简单连接管理
# ============================================================

def get_db_connection():
    """
    获取数据库连接（用于Repository层）

    注意：调用者负责关闭连接

    Returns:
        connection: 数据库连接对象

    Example:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                result = cursor.fetchall()
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            return_db_connection(conn)
    """
    conn_pool = db_config.get_connection_pool()
    return conn_pool.getconn()


def return_db_connection(conn):
    """
    归还数据库连接到连接池

    Args:
        conn: 数据库连接对象

    Example:
        conn = get_db_connection()
        try:
            # ... use connection
            pass
        finally:
            return_db_connection(conn)
    """
    conn_pool = db_config.get_connection_pool()
    conn_pool.putconn(conn)
