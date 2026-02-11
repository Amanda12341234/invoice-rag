from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
