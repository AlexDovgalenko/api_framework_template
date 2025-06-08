import os

APP_DB_FILENAME: str = os.getenv("APP_DB_FILENAME", "users.db")
DB_PROTOCOL: str = os.getenv("DB_PROTOCOL", "sqlite")  # e.g. "sqlite" or "postgresql"
DATABASE_URL: str   = os.getenv("DATABASE_URL", f"{DB_PROTOCOL}:///{APP_DB_FILENAME}")
JWT_SECRET: str     = os.getenv("JWT_SECRET", "test_jwt_secret")
JWT_ALGORITHM: str  = "HS256"
ACCESS_TOKEN_TTL_MIN: int  = 60  # minutes
APP_TITLE: str  = "Users API – SQLite edition"
APP_LOGGER_NAME: str  = "demo_api"
APP_PROTOCOL: str = "http"
LOG_DIR: str = "logs"  # Directory for log files
TEST_USER_EMAIL:str = "test-user@example.com"
TEST_PASSWORD:str = "super_strong_password"  # SARCASM 😄

USER_DETAILS_LIST = [
    {"id": "1", "f_name": "Alice", "l_name": "Smith", "email": "alice.smith@example.com"},
    {"id": "2", "f_name": "Bob", "l_name": "Johnson", "email": "bob.johnson@example.com"},
    {"id": "3", "f_name": "Charlie", "l_name": "Brown", "email": "charlie.brown@example.com"},
    {"id": "4", "f_name": "Diana", "l_name": "Davis", "email": "diana.davis@example.com"},
]