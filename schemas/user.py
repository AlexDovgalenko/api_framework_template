from typing import Any, Dict

USER_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["id", "username", "full_name", "contact"],
    "properties": {
        "id": {"type": "string"},
        "username": {"type": "string", "minLength": 1},
        "full_name": {"type": "string", "minLength": 1},
        "is_active": {"type": "boolean", "default": True},
        "contact": {
            "type": "object",
            "required": ["email"],
            "properties": {
                "email": {"type": "string", "format": "email"},
                "phone": {"type": "string", "nullable": True},
                "addresses": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["street", "city", "zip_code", "country"],
                        "properties": {
                            "street": {"type": "string"},
                            "city": {"type": "string"},
                            "state": {"type": "string", "nullable": True},
                            "zip_code": {"type": "string", "pattern": "^[0-9]+$"},
                            "country": {"type": "string", "minLength": 1},
                            "is_primary": {"type": "boolean", "default": False},
                        },
                    },
                    "default": [],
                },
            },
        },
        "permissions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "level": {"type": "integer", "default": 0},
                },
            },
            "default": [],
        },
    },
    "additionalProperties": False,
}
