"""Utility helpers used by the test-framework."""

import contextlib
import logging
import os
import socket
import subprocess
import time
from typing import Final

import requests

MAX_ATTEMPTS: Final[int] = 10          # hard upper bound (= MAX_ATTEMPTS × SLEEP_INTERVAL_SEC)
SLEEP_INTERVAL_SEC: Final[float] = 0.5
CONTAINER_IP: Final[str] = "0.0.0.0"
LOCALHOST_IP: Final[str] = "127.0.0.1"

def find_free_tcp_port() -> tuple[str, str]:
    """Bind to port 0 to let the OS pick an unused TCP port and return it.

    In Docker, bind to all interfaces (0.0.0.0), otherwise localhost (127.0.0.1)
    """
    host = CONTAINER_IP if os.environ.get("DOCKER_CONTAINER") else LOCALHOST_IP
    with contextlib.closing(socket.socket()) as provisional_socket:
        provisional_socket.bind((host, 0))
        available_port = provisional_socket.getsockname()[1]
        logging.debug(f"Found free TCP port: {available_port} on host {host}")
        return str(available_port), host


def wait_for_server_response(base_url: str, endpoint: str = "/openapi.json") -> None:
    """Poll ``base_url + path`` until the server responds or raise RuntimeError.

    Parameters
    ----------
    base_url : str
        The scheme, host and port of the server (e.g. "http://127.0.0.1:8000").
    endpoint : str, default "/openapi.json"
        A lightweight endpoint that returns quickly; defaults to FastAPI’s
        OpenAPI doc.

    Raises
    ------
    RuntimeError
        If the server does not respond within MAX_ATTEMPTS × SLEEP_INTERVAL_SEC.
    """
    url = base_url.rstrip("/") + endpoint
    for iteration in range(1, MAX_ATTEMPTS):
        msg = f"Attempt: {iteration}: Waiting for server response on: {url}"
        logging.debug(msg)
        try:
            requests.get(url, timeout=2)
            logging.info("HTTP server started on: %s" % url)
            return                                 # success
        except requests.ConnectionError:
            logging.debug("Sleep for %d seconds before retrying...", SLEEP_INTERVAL_SEC)
            time.sleep(SLEEP_INTERVAL_SEC)
    raise RuntimeError("HTTP server did not start on: %s" % url)


def terminate_process(process: "subprocess.Popen", timeout: int):
    """Terminate a subprocess gracefully across different OS platforms."""
    # directly use terminate() which is more graceful than kill()
    process.terminate()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        logging.warning("Process did not terminate in time, killing it...")
        process.kill()


def retry_with_backoff(operation, max_attempts=3, initial_delay=1.0,
                       exception_types=(Exception,), description=None):
    """Execute an operation with retry logic and exponential backoff.

    Parameters
    ----------
    operation : callable
        The function to execute
    max_attempts : int, default 3
        Maximum number of attempts before giving up
    initial_delay : float, default 1.0
        Delay in seconds between retries, doubles after each attempt
    exception_types : tuple, default (Exception,)
        The exception types that should trigger a retry
    description : str, optional
        Description of the operation for logging

    Returns
    -------
    The result of the operation if successful

    Raises
    ------
    The last exception if all attempts fail
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except exception_types as e:
            last_exception = e
            if attempt < max_attempts:
                operation_name = description or operation.__name__
                logging.debug(f"{operation_name} failed (attempt {attempt}/{max_attempts}), "
                              f"retrying in {delay} seconds... Error: {str(e)}")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                operation_name = description or operation.__name__
                logging.warning(f"{operation_name} failed after {max_attempts} attempts. "
                                f"Last error: {str(e)}")

    if last_exception:
        raise last_exception
    return None