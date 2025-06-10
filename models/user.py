from typing import List, Optional

from pydantic import BaseModel, EmailStr, validator


class Address(BaseModel):
    """Model for address information."""
    street: str
    city: str
    state: Optional[str] = None
    zip_code: str
    country: str
    is_primary: bool = False
    @validator('zip_code')
    def zip_code_must_be_numeric(cls, v):
        if not v.isdigit():
            raise ValueError('zip_code must be numeric')
        return v
    @validator('country')
    def country_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('country must not be empty')
        return v

class UserContact(BaseModel):
    """Model for user contact information."""
    email: EmailStr
    phone: Optional[str] = None
    addresses: List[Address] = []
    
    @validator('email')
    def email_must_contain_at(cls, v):
        if '@' not in v:
            raise ValueError('email must contain @')
        return v
    

class UserPermission(BaseModel):
    """Model for user permission details."""
    name: str
    level: int = 0

class User(BaseModel):
    """Model for user data."""
    id: int
    username: str
    full_name: str
    is_active: bool = True
    contact: UserContact
    permissions: List[UserPermission] = []
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission."""
        return any(p.name == permission_name for p in self.permissions)

    @validator('username')
    def username_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('username must not be empty')
        return v

    @validator('full_name')
    def full_name_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('full_name must not be empty')
        return v

    @validator('contact')
    def contact_must_have_email(cls, v):
        if not v.email:
            raise ValueError('contact must have an email')
        return v
