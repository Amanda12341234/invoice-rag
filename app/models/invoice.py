from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlmodel import Column, Field, JSON, SQLModel, UniqueConstraint


class Invoice(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "invoice_number", name="uq_user_invoice_number"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    invoice_number: Optional[str] = Field(default=None, max_length=20, index=True)
    store_name: str = Field(max_length=100)
    total_amount: float
    date: date
    category: str = Field(max_length=10)
    raw_text: Optional[str] = None
    ai_raw_output: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
