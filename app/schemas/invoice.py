from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.core.constants import CategoryEnum


class ParsedItem(BaseModel):
    name: str
    price: float = Field(ge=0)
    quantity: int = Field(ge=1, default=1)


class ParsedInvoice(BaseModel):
    invoice_number: Optional[str] = None
    store_name: str
    date: date
    total_amount: float
    items: list[ParsedItem]
    category: CategoryEnum
    raw_text: Optional[str] = None
    validation_errors: list[str] = []


class ItemCreate(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(ge=0)
    quantity: int = Field(ge=1, default=1)


class InvoiceCreate(BaseModel):
    invoice_number: Optional[str] = None
    store_name: str = Field(min_length=1)
    date: date
    total_amount: float = Field(ge=0)
    items: list[ItemCreate] = Field(min_length=1)
    category: CategoryEnum
    raw_text: Optional[str] = None
    ai_raw_output: Optional[Any] = None
    force_save: bool = False


class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = None
    store_name: Optional[str] = Field(default=None, min_length=1)
    date: Optional[date] = None
    total_amount: Optional[float] = Field(default=None, ge=0)
    items: Optional[list[ItemCreate]] = Field(default=None, min_length=1)
    category: Optional[CategoryEnum] = None


class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    quantity: int


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: Optional[str] = None
    store_name: str
    date: date
    total_amount: float
    category: str
    created_at: datetime


class InvoiceDetailResponse(InvoiceResponse):
    items: list[ItemResponse] = []
    raw_text: Optional[str] = None
    ai_raw_output: Optional[Any] = None


class CalendarDay(BaseModel):
    date: date
    count: int
    total_amount: float
