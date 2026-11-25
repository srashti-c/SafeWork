from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """What a person sends when registering."""
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    # bcrypt only uses the first 72 bytes, so we cap the length
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    """What we send back. Note: no password field at all."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    """What login returns."""
    access_token: str
    token_type: str = "bearer"

class RoleUpdate(BaseModel):
    """Body for changing a user's role."""
    role: UserRole