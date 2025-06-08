import json
import re

import pytest


@pytest.fixture
def mock_items(requests_mock, base_url, resource_path, mock_data) -> dict:
    """
    Mocks:
      GET https://example.com/users/        → 200 + full list
      GET https://example.com/users/<id>    → 200 + single object (if exists)
                                            404 + {"error":"No such item with provided id: {id}"} (otherwise)
    Returns a dict of { id: user_dict } for convenience.
    """
    base_mock_url = f"{base_url.rstrip('/')}/{resource_path.strip('/')}"
    # build a lookup items map by `id` from the mock data
    # e.g. {"1": {"id": "1", "name": "Alice"}, ...}
    items_map = {d["id"]: d for d in mock_data}

    # 1) Return "list" of all endpoints
    requests_mock.get(base_mock_url, json=mock_data, status_code=200)

    # 2) All detail endpoints via a regex + callback
    def _detail_callback(request, context) -> str:
        # request.url is e.g. "https://example.com/users/<id>"
        item_id = request.url.removeprefix(base_mock_url)
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
    requests_mock.get(
        re.compile(r"{}[^/]+$".format(re.escape(base_mock_url))), text=_detail_callback
    )
    return items_map
