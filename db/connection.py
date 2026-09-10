import os
import mysql.connector.pooling
from dotenv import load_dotenv

load_dotenv()

# Railway injects MYSQLHOST/MYSQLPORT/etc. Locally we use DB_HOST/DB_USER/etc.
db_config = {
    "host":     os.environ.get("MYSQLHOST")     or os.environ.get("DB_HOST", "localhost"),
    "port":     int(os.environ.get("MYSQLPORT") or os.environ.get("DB_PORT", 3306)),
    "user":     os.environ.get("MYSQLUSER")     or os.environ.get("DB_USER", "root"),
    "password": os.environ.get("MYSQLPASSWORD") or os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("MYSQLDATABASE") or os.environ.get("DB_NAME", "lld_practice"),
}

pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="lld_pool",
    pool_size=5,
    **db_config,
)

def get_connection():
    return pool.get_connection()