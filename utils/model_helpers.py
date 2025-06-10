from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel

from .schema_validation import validate_schema

T = TypeVar('T', bound=BaseModel)


def parse_response(
    response_data: Dict[str, Any],
    model_class: Type[T],
    schema: Dict[str, Any],
    data_path: str,
    validate: bool = True,
    name: Optional[str] = None
) -> Optional[T]:
    """
    Parse an optional response from API data into a Pydantic model.
    
    Args:
        response_data: The API response data
        model_class: The Pydantic model class to parse into
        schema: JSON schema to validate against
        data_path: Path to the optional item in the response (e.g., "data.user")
        validate: Whether to perform schema validation
        name: Optional name for error messages
        
    Returns:
        Instance of model_class or None if not present
    """
    if validate:
        validate_schema(response_data, schema, name)
    
    # Extract optional data from nested path
    parts = data_path.split('.')
    data = response_data
    for part in parts:
        data = data.get(part)
    
    return model_class.parse_obj(data) if data is not None else None

def parse_response_list(
    response_data: Dict[str, Any],
    model_class: Type[T],
    schema: Dict[str, Any],
    data_path: str,
    validate: bool = True,
    name: Optional[str] = None
) -> Optional[list[T]]:
    """
    Parse an optional list from API response data into a list of Pydantic models.
    
    Args:
        response_data: The API response data
        model_class: The Pydantic model class to parse items into
        schema: JSON schema to validate against
        data_path: Path to the optional list in the response (e.g., "data.users")
        validate: Whether to perform schema validation
        name: Optional name for error messages
        
    Returns:
        List of model_class instances or None if not present
    """
    if validate:
        validate_schema(response_data, schema, name)
    
    # Extract optional list data from nested path
    parts = data_path.split('.')
    data = response_data
    for part in parts:
        data = data.get(part)
    
    return [model_class.parse_obj(item) for item in data] if isinstance(data, list) else None

def parse_response_dict(
    response_data: Dict[str, Any],
    model_class: Type[T],
    schema: Dict[str, Any],
    data_path: str,
    validate: bool = True,
    name: Optional[str] = None
) -> Optional[Dict[str, T]]:
    """
    Parse an optional dictionary from API response data into a dict of Pydantic models.
    
    Args:
        response_data: The API response data
        model_class: The Pydantic model class to parse items into
        schema: JSON schema to validate against
        data_path: Path to the optional dict in the response (e.g., "data.users")
        validate: Whether to perform schema validation
        name: Optional name for error messages
        
    Returns:
        Dictionary of model_class instances or None if not present
    """
    if validate:
        validate_schema(response_data, schema, name)
    
    # Extract optional dict data from nested path
    parts = data_path.split('.')
    data = response_data
    for part in parts:
        data = data.get(part)
    
    return {key: model_class.parse_obj(value) for key, value in data.items()} if isinstance(data, dict) else None


def parse_response_dict_list(
    response_data: Dict[str, Any],
    model_class: Type[T],
    schema: Dict[str, Any],
    data_path: str,
    validate: bool = True,
    name: Optional[str] = None
) -> Optional[Dict[str, Optional[list[T]]]]:
    """
    Parse an optional dictionary of optional lists from API response data into a dict of optional lists of Pydantic models.
    
    Args:
        response_data: The API response data
        model_class: The Pydantic model class to parse items into
        schema: JSON schema to validate against
        data_path: Path to the optional dict of optional lists in the response (e.g., "data.users")
        validate: Whether to perform schema validation
        name: Optional name for error messages
        
    Returns:
        Dictionary of optional lists of model_class instances or None if not present
    """
    if validate:
        validate_schema(response_data, schema, name)
    
    # Extract optional dict of optional lists data from nested path
    parts = data_path.split('.')
    data = response_data
    for part in parts:
        data = data.get(part)
    
    if not isinstance(data, dict):
        return None
    
    return {key: ([model_class.parse_obj(item) for item in value] if value is not None else None) for key, value in data.items()}


def parse_response_dict_dict(
    response_data: Dict[str, Any],
    model_class: Type[T],
    schema: Dict[str, Any],
    data_path: str,
    validate: bool = True,
    name: Optional[str] = None
) -> Optional[Dict[str, Optional[T]]]:
    """
    Parse an optional dictionary of optional items from API response data into a dict of optional Pydantic models.
    
    Args:
        response_data: The API response data
        model_class: The Pydantic model class to parse items into
        schema: JSON schema to validate against
        data_path: Path to the optional dict of optional items in the response (e.g., "data.users")
        validate: Whether to perform schema validation
        name: Optional name for error messages
        
    Returns:
        Dictionary of optional model_class instances or None if not present
    """
    if validate:
        validate_schema(response_data, schema, name)
    
    # Extract optional dict of optional items data from nested path
    parts = data_path.split('.')
    data = response_data
    for part in parts:
        data = data.get(part)
    
    return {key: (model_class.parse_obj(value) if value is not None else None) for key, value in data.items()} if isinstance(data, dict) else None

def parse_response_list_list(
    response_data: Dict[str, Any],
    model_class: Type[T],
    schema: Dict[str, Any],
    data_path: str,
    validate: bool = True,
    name: Optional[str] = None
) -> Optional[list[Optional[T]]]:
    """
    Parse an optional list of optional items from API response data into a list of optional Pydantic models.
    
    Args:
        response_data: The API response data
        model_class: The Pydantic model class to parse items into
        schema: JSON schema to validate against
        data_path: Path to the optional list of optional items in the response (e.g., "data.users")
        validate: Whether to perform schema validation
        name: Optional name for error messages
        
    Returns:
        List of optional model_class instances or None if not present
    """
    if validate:
        validate_schema(response_data, schema, name)
    
    # Extract optional list of optional items data from nested path
    parts = data_path.split('.')
    data = response_data
    for part in parts:
        data = data.get(part)
    
    return [model_class.parse_obj(item) if item is not None else None for item in data] if isinstance(data, list) else None
