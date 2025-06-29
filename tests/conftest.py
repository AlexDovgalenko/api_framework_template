"""Pytest fixtures for the framework."""
import base64
import contextlib
import json
import logging
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Generator, Optional

import pytest
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.db_utils import database_engine
from constants.common import (
    APP_DB_FILENAME,
    APP_PROTOCOL,
    DB_PROTOCOL,
    JWT_SECRET,
    TEST_PASSWORD,
    TEST_USER_EMAIL,
)
from constants.user import USER_DETAILS_LIST
from utils import logging_config
from utils.app_helpers import (
    find_free_tcp_port,
    retry_with_backoff,
    terminate_process,
    wait_for_server_response,
)

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

    # Let logging_config handle the log file path creation
    logging_config.configure_logging(
        level=console_level,
        enable_console=True,
    )

    # Log the configuration
    logging.getLogger(__name__).info(
        "Test session started with log level: %s", console_level
    )

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
def internal_test_server(request) -> Generator[Optional[dict], None, None]:
    external_base_url: str | None = request.config.getoption("--source")
    if external_base_url:
        yield None
        return

    server_port, host = find_free_tcp_port()
    base_url = f"{APP_PROTOCOL}://{host}:{server_port}"

    temp_dir = Path(tempfile.mkdtemp())
    database_file = temp_dir / APP_DB_FILENAME

    child_env = os.environ | {
        "DATABASE_URL": f"{DB_PROTOCOL}:///{database_file}",
        "JWT_SECRET": JWT_SECRET,
    }

    logging.info("Starting internal API test server on %s", base_url)
    server_process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--port", str(server_port), "--host", host],
        env=child_env | {"LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO")},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # Line buffered
    )

    # Start a thread to capture and log server output
    def log_server_output():
        if server_process.stdout:
            for line in iter(server_process.stdout.readline, ""):
                logging.debug(f"Server output: {line.strip()}")
        else:
            logging.error("Cannot read server output: stdout is None")

    import threading

    output_thread = threading.Thread(target=log_server_output, daemon=True)
    output_thread.start()

    # Check if process is still running before waiting for response
    time.sleep(1)
    if server_process.poll() is not None:
        exit_code = server_process.poll()
        output, _ = server_process.communicate()
        error_msg = (
            f"Server process exited immediately with code {exit_code}. Output: {output}"
        )
        logging.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        wait_for_server_response(base_url)
    except RuntimeError as e:
        # Try to capture any output from the server to help diagnose the issue
        output, _ = server_process.communicate(timeout=1)
        logging.error(f"Server failed to start. Server output: {output}")
        terminate_process(server_process, SHUTDOWN_TIMEOUT_SEC)
        raise RuntimeError(f"Server failed to start: {str(e)}. Output: {output}")

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


def create_mock_items(requests_mock, base_url, res_path: str, mock_data: list[dict[str, Any]]) -> dict:
    """Mocs API resource on given resource path, matching provided moc object data list.
    Mocks:
      GET https://example.com/users/        → 200 + full list
      GET https://example.com/users/<id>    → 200 + single object (if exists)
                                            404 + {"error":"No such item with provided id: {id}"} (otherwise)
    Returns a dict of { id: item_dict } for convenience.
    """
    base_mock_url = f"{base_url.rstrip('/')}/{res_path.strip('/')}"
    # build a lookup items map by `id` from the mock data
    # e.g. {"1": {"id": "1", "name": "Alice"}, ...}
    items_map = {str(item["id"]): item for item in mock_data}

    logging.debug(f"Mocking endpoints for {base_mock_url}")
    logging.debug(f"Available mock IDs: {list(items_map.keys())}")

    # 1) Return "list" of all endpoints
    requests_mock.get(base_mock_url, json=mock_data, status_code=200)

    # 2) All detail endpoints via a regex + callback
    def _callback(request, context) -> str:
        # request.url is e.g. "https://example.com/users/<id>"
        item_id = request.url.split("/")[-1]
        logging.debug(f"Mock received request for ID: {item_id}")

        if item_id in items_map:
            context.status_code = 200
            # important to set header if you want .json() to work !!!
            context.headers["Content-Type"] = "application/json"
            return json.dumps(items_map[item_id])
        else:
            context.status_code = 404
            context.headers["Content-Type"] = "application/json"
            return json.dumps({"error": f"No such item with provided id: '{item_id}'."})

    # register any GET on `{base_mock_url}/<something>` (but not another trailing slash e.g. `{base_mock_url}/<something>/`!!!)
    resource_url_pattern = f"{re.escape(base_mock_url)}/[^/]+"
    requests_mock.get(re.compile(resource_url_pattern), text=_callback)
    return items_map

@pytest.fixture
def mock_user_details(requests_mock, base_url):
    """Provide a sample User Details resource for mocking."""
    logging.debug(f"Setting up user details mock with base URL: {base_url}")
    return create_mock_items(
        requests_mock=requests_mock,
        base_url=base_url,
        res_path="user/details",
        mock_data=USER_DETAILS_LIST,
    )
