import json
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import pytest
from pydantic import BaseModel, ValidationError

from .schema_validation import validate_schema

T = TypeVar("T", bound=BaseModel)


def parse_response(
    response_data: Union[Dict[str, Any], List[Any]],
    model_class: Type[T],
    schema: Dict[str, Any],
    data_path: str = "",
    validate: bool = True,
    name: Optional[str] = None,
) -> T:
    """Parse API response data into a Pydantic model with pytest integration.

    Parameters
    ----------
    response_data : Dict[str, Any] | List[Any]
        The API response data
    model_class : Type[T]
        The Pydantic model class to parse into
    schema : Dict[str, Any]
        JSON schema to validate against
    data_path : str, optional
        Path to the data in the response (e.g., "data.user")
    validate : bool, default=True
        Whether to perform schema validation
    name : str | None, optional
        Name for error messages

    Returns
    -------
    T
        Instance of model_class
    """
    context = f" for {name}" if name else ""

    if validate:
        validate_schema(response_data, schema, name)

    # Extract data from nested path
    data = response_data
    if data_path:
        for part in data_path.split("."):
            if not isinstance(data, (dict, list)):
                pytest.fail(
                    f"Cannot access '{part}' in path '{data_path}'{context}: "
                    f"parent is {type(data).__name__}, expected dict or list"
                )
            try:
                data = data.get(part) if isinstance(data, dict) else data[int(part)]
            except (KeyError, IndexError, ValueError):
                pytest.fail(f"Invalid path '{data_path}'{context}")

            if data is None:
                pytest.fail(f"Data not found at path '{data_path}'{context}")

    try:
        return model_class.model_validate(data)
    except ValidationError as e:
        error_details = json.dumps(e.errors(), indent=2)
        data_preview = json.dumps(data, indent=2)[:200] + "..."  # Truncate long output
        pytest.fail(
            f"Validation error parsing{context}:\n"
            f"Data: {data_preview}\n"
            f"Errors: {error_details}"
        )
