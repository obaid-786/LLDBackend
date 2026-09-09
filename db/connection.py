import os
import mysql.connector.pooling
from dotenv import load_dotenv

load_dotenv()

pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="lld_pool",
    pool_size=5,
    host=os.environ.get("DB_HOST", "localhost"),
    user=os.environ.get("DB_USER", "root"),
    password=os.environ.get("DB_PASSWORD", ""),
    database=os.environ.get("DB_NAME", "lld_practice")
)

def get_connection():
    return pool.get_connection()      