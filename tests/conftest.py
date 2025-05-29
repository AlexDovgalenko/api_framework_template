"""Pytest fixtures for the framework."""
import base64
import contextlib
import logging
import os
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Generator

import pytest
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

import logging_config
from app.db_utils import database_engine
from utils.app_helpers import (
    find_free_tcp_port,
    wait_for_server_response, terminate_process, retry_with_backoff,
)
from utils.constants import APP_PROTOCOL, APP_DB_FILENAME, DB_PROTOCOL, LOG_DIR, JWT_SECRET, TEST_USER_EMAIL, \
    TEST_PASSWORD

SHUTDOWN_TIMEOUT_SEC: int = 5  # Seconds to wait for the internal server to shut down gracefully


### Pytest command-line options and session-wide logging ###
def pytest_addoption(parser):
    parser.addoption(
        "--source",
        help="Base URL of an already running API. "
             "If omitted an internal FastAPI mock is started.",
    )
    parser.addini("log-level", default="INFO", help="Console log level (DEBUG, INFO, WARNING, ERROR)")

def pytest_configure(config):
    """Create logs/ dir and configure root logger once for the test session."""
    console_level = config.option.log_level or "INFO"
    logs_dir = Path(LOG_DIR)  # Ensure logs are written to the correct directory
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session_log_file = logs_dir / f"test_{timestamp}.log"

    logging_config.configure_logging(
        level=console_level,
        logfile_path=str(session_log_file),
        enable_console=True,
    )
    logging.getLogger(__name__).info("Logging to %s", session_log_file)
    # Pass logging configuration to FastAPI mock application
    os.environ["LOG_LEVEL"] = console_level


### API client with base_url awareness and logging capabilities ###
class APIClient(requests.Session):
    """Class describes APIClient, based on requests.Session.

    • prefixes all URLs starting with "/" by .base_url
    • logs every request/response at DEBUG level
    """

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url.rstrip("/")

    # override the original request method so every verb benefits
    def request(self, method, url, *args, **kwargs):
        if url.startswith("/"):
            url = self.base_url + url

        start_time = time.perf_counter()
        logging.debug("HTTP %-6s %s", method.upper(), url)
        response = super().request(method, url, *args, **kwargs)
        duration_ms = (time.perf_counter() - start_time) * 1_000
        logging.debug("-> %s in %.1f ms", response.status_code, duration_ms)
        return response

### Internal FastAPI server (spawned when `--source` CLI argument not supplied.) ###
@pytest.fixture(scope="session")
def internal_test_server(request) -> Optional[dict]:
    external_base_url: str | None = request.config.getoption("--source")
    if external_base_url:
        yield None
        return

    server_port, host = find_free_tcp_port()
    base_url    = f"{APP_PROTOCOL}://{host}:{server_port}"

    temp_dir      = Path(tempfile.mkdtemp())
    database_file = temp_dir / APP_DB_FILENAME

    child_env = os.environ | {
        "DATABASE_URL": f"{DB_PROTOCOL}:///{database_file}",
        "JWT_SECRET":   JWT_SECRET,
    }

    logging.info("Starting internal API test server on %s", base_url)
    server_process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--port", str(server_port)],
        env=child_env | {"LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO")},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    wait_for_server_response(base_url)

    # Pass control to test session
    logging.debug(
        f"Internal test server started at {base_url} with database file {database_file}",
    )
    yield {"base_url": base_url, "database_file": database_file}

    # Graceful target App shutdown + cleanup
    logging.debug("Shutting down internal API test server ...")
    terminate_process(server_process, SHUTDOWN_TIMEOUT_SEC)

    logging.debug("Cleaning up all DB connections and temporary files ...")
    database_engine.dispose()  # Close all connections

    # Allow a brief moment for file handles to be released
    time.sleep(0.5)
    # Use retry_with_backoff for file deletion
    try:
        def delete_files():
            with contextlib.suppress(FileNotFoundError):
                database_file.unlink()
                temp_dir.rmdir()

        retry_with_backoff(
            delete_files,
            max_attempts=3,
            initial_delay=1.0,
            exception_types=(PermissionError,),
            description="Database file cleanup"
        )
    except PermissionError:
        logging.warning(f"Could not delete database file: {database_file} - it may still be locked")


### Automatic DB cleanup for the internal mock ###
@pytest.fixture(autouse=True)
def reset_database_between_tests(internal_test_server):
    """Truncate the users table after every test when we own the DB."""
    if not internal_test_server:
        return
    engine = create_engine(
        f"{DB_PROTOCOL}:///{internal_test_server['database_file']}",
        connect_args={"check_same_thread": False},
    )
    with engine.begin() as connection:
        try:
            connection.execute(text("DELETE FROM users"))
            logging.debug("Database cleaned - deleted all users")
        except OperationalError as e:
            logging.debug(f"Table reset skipped: {e}")

### Session-wide client fixture ###
@pytest.fixture(scope="session")
def base_url(request, internal_test_server) -> str:
    """Return the base URL that all tests should call."""
    return request.config.getoption("--source") or internal_test_server["base_url"]


@pytest.fixture(scope="session")
def client(base_url) -> Generator[APIClient, None, None]:
    """Provide a shared API client for the entire test session."""
    session_client = APIClient(base_url)
    yield session_client
    session_client.close()


### Authentication helpers ###
@pytest.fixture(scope="session")
def bearer_token(client) -> str:
    """Create demo user (idempotent) and obtain a JWT token."""
    client.post("/users",
                json={"email": TEST_USER_EMAIL, "password": TEST_PASSWORD})

    token_response = client.post(
        "/login",
        data={"username": TEST_USER_EMAIL, "password": TEST_PASSWORD},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )

    if token_response.status_code != 200:
        pytest.skip("Bearer token endpoint not available")

    return token_response.json()["access_token"]


@pytest.fixture(params=["none", "basic", "bearer"])
def auth_headers(request, client, bearer_token):
    """Return request headers for the desired authentication option."""
    option = request.param

    # Check if the user exists before creating it
    user_check_response = client.get(f"/users/{TEST_USER_EMAIL}")
    if user_check_response.status_code == 404:  # User does not exist
        client.post("/users", json={"email": TEST_USER_EMAIL, "password": TEST_PASSWORD})

    if option == "none":
        return {}

    if option == "basic":
        raw_credentials = f"{TEST_USER_EMAIL}:{TEST_PASSWORD}".encode()
        encoded = base64.b64encode(raw_credentials).decode()
        return {"Authorization": f"Basic {encoded}"}
    return {"Authorization": f"Bearer {bearer_token}"}
