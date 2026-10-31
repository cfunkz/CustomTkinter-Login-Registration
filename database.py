import importlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime
import config

# One place for every database connection, so the app works with SQLite, PostgreSQL or MySQL.
# Queries in functions.py are written once with "?" placeholders and plain SQL that all three understand.

DATABASE_TYPE = config.database_type

# Python package for each database type
DRIVERS = {
    "sqlite": "sqlite3",
    "postgres": "psycopg2",  # pip install psycopg2-binary
    "mysql": "pymysql",  # pip install PyMySQL
}

def load_driver():
    # Import the driver for the configured database type
    if DATABASE_TYPE not in DRIVERS:
        raise ValueError(f"Unknown DATABASE_TYPE '{DATABASE_TYPE}'. Use sqlite, postgres or mysql.")
    try:
        return importlib.import_module(DRIVERS[DATABASE_TYPE])
    except ImportError:
        package = {"postgres": "psycopg2-binary", "mysql": "PyMySQL"}[DATABASE_TYPE]
        raise ImportError(f"DATABASE_TYPE is {DATABASE_TYPE}, install the driver with: pip install {package}")

driver = load_driver()

# Error classes of the active driver, used in except blocks
DatabaseError = driver.Error
IntegrityError = driver.IntegrityError

class Cursor:
    # Small cursor wrapper that turns "?" placeholders into "%s" for PostgreSQL and MySQL
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=()):
        if DATABASE_TYPE != "sqlite":
            query = query.replace("?", "%s")
        self.cursor.execute(query, params)

    def __getattr__(self, name):
        # fetchone, fetchall, rowcount, description... come from the real cursor
        return getattr(self.cursor, name)

def get_database_connection():
    # Open a database connection and return the connection and cursor
    if DATABASE_TYPE == "postgres":
        db = driver.connect(host=config.database_host, port=config.database_port, dbname=config.database_name,
                            user=config.database_user, password=config.database_password, connect_timeout=10)
    elif DATABASE_TYPE == "mysql":
        db = driver.connect(host=config.database_host, port=config.database_port, database=config.database_name,
                            user=config.database_user, password=config.database_password, connect_timeout=10, charset="utf8mb4")
    else:
        db = sqlite3.connect(config.database_file)
    return db, Cursor(db.cursor())

def close_database_connection(db):
    # Close the database connection
    if db:
        db.close()

@contextmanager
def database():
    # Open a connection, commit on success, roll back on error and always close it
    db, cursor = get_database_connection()
    try:
        yield cursor
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        close_database_connection(db)

def now():
    # Current time as text, the same on every database ("2024-01-31 12:00:00")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def init_database():
    # Create the Users table once on app start and add any missing columns from older versions
    with database() as cursor:
        # VARCHAR and INTEGER work the same on SQLite, PostgreSQL and MySQL
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                country VARCHAR(100),
                username VARCHAR(50) UNIQUE,
                email VARCHAR(255) UNIQUE,
                password VARCHAR(255),
                security_question VARCHAR(255),
                security_answer VARCHAR(255),
                failed_attempts INTEGER DEFAULT 0,
                locked_until DOUBLE PRECISION DEFAULT 0,
                must_change_password INTEGER DEFAULT 0,
                created_at VARCHAR(20),
                last_login VARCHAR(20),
                oauth_provider VARCHAR(20),
                oauth_id VARCHAR(100),
                password_set INTEGER DEFAULT 1,
                UNIQUE (oauth_provider, oauth_id)
            )
        ''')

        if DATABASE_TYPE == "sqlite":
            upgrade_sqlite_database(cursor)
        if DATABASE_TYPE in ("sqlite", "postgres"):
            # Case-insensitive usernames and emails ("Bob" and "bob" are the same user)
            # MySQL compares text case-insensitively by default, so it doesn't need these
            try:
                cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_lower ON Users (LOWER(username))")
                cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON Users (LOWER(email))")
            except IntegrityError:
                # An old database already has names that only differ by case, keep the original UNIQUE rules
                print("Skipping case-insensitive indexes: duplicate usernames or emails found.")

def upgrade_sqlite_database(cursor):
    # Add columns that older versions of user_database.db don't have
    cursor.execute("PRAGMA table_info(Users)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    new_columns = {
        "failed_attempts": "INTEGER DEFAULT 0",
        "locked_until": "REAL DEFAULT 0",
        "must_change_password": "INTEGER DEFAULT 0",
        "created_at": "TEXT",
        "last_login": "TEXT",
        "oauth_provider": "TEXT",
        "oauth_id": "TEXT",
        "password_set": "INTEGER DEFAULT 1",  # 0 for accounts created with a social login
    }
    for column, column_type in new_columns.items():
        if column not in existing_columns:
            cursor.execute(f"ALTER TABLE Users ADD COLUMN {column} {column_type}")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_oauth ON Users (oauth_provider, oauth_id)")
