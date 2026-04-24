"""
Pydantic schemas for authentication.
"""
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    created_at: datetime
    api_key: Optional[str] = None

    class Config:
        from_attributes = True
