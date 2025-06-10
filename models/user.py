from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator


class Address(BaseModel):
    """Model for address information."""

    model_config = ConfigDict(strict=True, frozen=True)

    street: str
    city: str
    state: Optional[str] = None
    zip_code: str
    country: str
    is_primary: bool = False

    @field_validator("zip_code")
    @classmethod
    def zip_code_must_be_numeric(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError('zip_code must be numeric')
        return value

    @field_validator("country")
    @classmethod
    def country_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('country must not be empty')
        return value.strip()


class UserContact(BaseModel):
    """Model for user contact information."""

    model_config = ConfigDict(strict=True, frozen=True)

    email: EmailStr
    phone: Optional[str] = None
    addresses: List[Address] = []

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("email must contain @")
        return value.lower()  # Normalize emails to lowercase


class UserPermission(BaseModel):
    """Model for user permission details."""

    model_config = ConfigDict(strict=True, frozen=True)

    name: str
    level: int = 0

    @field_validator("level")
    @classmethod
    def level_must_be_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("permission level must be non-negative")
        return value


class User(BaseModel):
    """Model for user data."""

    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)

    id: str
    username: str
    full_name: str
    is_active: bool = True
    contact: UserContact
    permissions: List[UserPermission] = []

    @field_validator("username", "full_name")
    @classmethod
    def validate_non_empty_string(cls, value: str, info) -> str:
        if not value.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return value.strip()

    @model_validator(mode="after")
    def validate_contact_email(self) -> "User":
        """Validate contact email after model creation."""
        if not self.contact.email:
            raise ValueError("contact must have an email")
        return self

    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission."""
        return any(p.name == permission_name for p in self.permissions)
