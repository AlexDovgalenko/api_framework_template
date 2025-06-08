import pytest

from mock.constants import USERS_LIST


@pytest.fixture
def mock_users(mock_items) -> list[dict]:
    """Provide a sample data set for mocking."""
    return mock_items(resource_path="users", mock_data=USERS_LIST)
