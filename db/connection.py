import os
import mysql.connector.pooling
from dotenv import load_dotenv

load_dotenv()

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="lld_pool",
            pool_size=5,
            host=os.environ.get("DB_HOST", "127.0.0.1"),   # force IPv4
            port=int(os.environ.get("DB_PORT", 3306)),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_NAME", "lld_practice"),
            use_pure=True,   # avoid C-extension edge cases on Windows
        )
    return _pool


def get_connection():
    # Test override (set by tests/conftest.py)
    global _test_conn
    if "_test_conn" in globals() and _test_conn is not None:
        return _test_conn
    return get_pool().get_connection()


def reset_pool():
    """Debug helper: drop the cached pool so it's rebuilt on next request."""
    global _pool
    _pool = None