import pytest
from fastapi.testclient import TestClient
from main import app
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv('.env.test')

_test_conn = None

@pytest.fixture(scope="session")
def test_db():
    global _test_conn
    db_name = os.environ.get("DB_NAME", "lld_practice_test")
    print(f"\n=== Setting up test database: {db_name} ===")

    _test_conn = mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=db_name,
        autocommit=True
    )

    cursor = _test_conn.cursor()

    # --- Clear all tables ---
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    for (table,) in tables:
        cursor.execute(f"TRUNCATE TABLE {table}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    print("✓ Tables cleared")

    # --- Re‑seed from seed.sql using multi‑statement execution ---
    with open('db/seed.sql', 'r') as f:
        seed_sql = f.read()
        # Execute all statements in one go
        for result in cursor.execute(seed_sql, multi=True):
            # result is a cursor for each statement; we just iterate to consume
            pass
    print("✓ Data reseeded")

    cursor.close()

    # Patch db.connection.get_connection
    import db.connection
    db.connection.get_connection = lambda: _test_conn
    db.connection._pool = None

    yield _test_conn

    if _test_conn:
        _test_conn.close()

@pytest.fixture
def client(test_db):
    return TestClient(app)

@pytest.fixture
def sample_submission():
    return """
    Requirements: The system must handle multiple floors and vehicle types.
    Classes:
    - Floor: manages parking spots on one floor
    - Vehicle: base class for Car, Bike, Truck
    - ParkingSpot: represents individual spot with vehicle type
    Responsibilities:
    - Floor: assign/remove vehicles, check availability
    - Vehicle: stores license plate and type
    - ParkingSpot: holds vehicle reference
    Design Decisions:
    - Used inheritance for vehicle types
    - Strategy pattern for fee calculation
    - Singleton for parking lot manager
    """