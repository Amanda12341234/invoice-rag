from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AuthRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6)


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
