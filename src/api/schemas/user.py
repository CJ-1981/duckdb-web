"""
User Schemas

Pydantic schemas for user request/response validation.

@MX:SPEC: SPEC-PLATFORM-001 P2-T010
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user fields."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user profile update."""

    email: Optional[str] = Field(None, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    username: Optional[str] = Field(None, min_length=3, max_length=50)


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


class UserListResponse(BaseModel):
    """Schema for paginated user list."""

    users: list[UserResponse]
    total: int
    page: int
    page_size: int


__all__ = [
    'UserCreate',
    'UserUpdate',
    'UserResponse',
    'PasswordChange',
    'UserListResponse'
]
