from typing import Optional

from sqlmodel import Field, SQLModel


class InvoiceItem(SQLModel, table=True):
    __tablename__ = "invoiceitem"

    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoice.id", ondelete="CASCADE")
    name: str = Field(max_length=100)
    price: float
    quantity: int = Field(default=1)
