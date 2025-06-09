from typing import Any, Dict, List

import jsonschema
import pytest
from jsonschema import validators


def format_validation_error(error: jsonschema.ValidationError) -> str:
    """Format a validation error with path and instance details."""
    path = "/".join(str(part) for part in error.path) if error.path else ""
    path_info = f" at path '{path}'" if path else ""
    return f"{error.message}{path_info}. Instance: {error.instance}"


class SchemaValidator:
    """Class for advanced schema validation with caching."""

    _schema_cache = {}

    @classmethod
    def get_validator(cls, schema: Dict[str, Any]) -> jsonschema.validators.Validator: # type: ignore
        """Get or create a cached validator for the schema."""
        schema_id = id(schema)
        if schema_id not in cls._schema_cache:
            validator_cls = validators.validator_for(schema)
            validator_cls.check_schema(schema)
            cls._schema_cache[schema_id] = validator_cls(schema)
        return cls._schema_cache[schema_id]

    @classmethod
    def validate(cls, instance: Any, schema: Dict[str, Any]) -> List[str]:
        """Validate instance against schema and return all errors."""
        validator = cls.get_validator(schema)
        errors = list(validator.iter_errors(instance))
        return [format_validation_error(error) for error in errors]


def validate_schema(data: Any, schema: Dict[str, Any]) -> bool:
    """
    Validate data against a schema and fail the test if validation errors exist.
    
    Args:
        data: The data to validate
        schema: The JSON schema to validate against
        
    Returns:
        True if validation passes
        
    Raises:
        pytest.fail: If validation fails
    """
    errors = SchemaValidator.validate(data, schema)
    if errors:
        pytest.fail(f"Schema validation failed: {errors}")
    return True
