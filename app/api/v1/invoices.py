from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlmodel import Session, select, and_

from app.auth import get_current_user
from app.database import get_session
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.user import User
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceDetailResponse,
    InvoiceResponse,
    InvoiceUpdate,
    ItemResponse,
    ParsedInvoice,
)
from app.services.ai_parser import parse_invoice as ai_parse_invoice
from app.services.validators import validate_invoice
from app.services.vector_store import get_vector_store

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("/parse", response_model=ParsedInvoice)
async def parse_invoice_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=422, detail="Invalid image file")

    image_bytes = await file.read()
    try:
        result = await ai_parse_invoice(image_bytes)
    except Exception:
        raise HTTPException(status_code=503, detail="AI service unavailable")
    del image_bytes

    validation_errors = validate_invoice(result)
    result["validation_errors"] = validation_errors
    return result


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    data: InvoiceCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    vector_store=Depends(get_vector_store),
):
    # Duplicate detection
    if not data.force_save and data.invoice_number:
        existing = session.exec(
            select(Invoice).where(
                and_(
                    Invoice.user_id == current_user.id,
                    Invoice.invoice_number == data.invoice_number,
                )
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Duplicate invoice number",
                    "duplicate_info": {"id": existing.id, "invoice_number": existing.invoice_number},
                },
            )

    # Fallback duplicate check: store_name + total_amount + date
    if not data.force_save and not data.invoice_number:
        existing = session.exec(
            select(Invoice).where(
                and_(
                    Invoice.user_id == current_user.id,
                    Invoice.store_name == data.store_name,
                    Invoice.total_amount == data.total_amount,
                    Invoice.date == data.date,
                )
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail={"message": "Possible duplicate invoice (same store, amount, date)"},
            )

    invoice = Invoice(
        user_id=current_user.id,
        invoice_number=data.invoice_number,
        store_name=data.store_name,
        total_amount=data.total_amount,
        date=data.date,
        category=data.category.value,
        raw_text=data.raw_text,
        ai_raw_output=data.ai_raw_output,
    )
    session.add(invoice)
    session.commit()
    session.refresh(invoice)

    items_for_vector = []
    for item_data in data.items:
        item = InvoiceItem(
            invoice_id=invoice.id,
            name=item_data.name,
            price=item_data.price,
            quantity=item_data.quantity,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        items_for_vector.append({"id": item.id, "name": item.name, "price": item.price})

    try:
        vector_store.add_items(
            items=items_for_vector,
            user_id=current_user.id,
            invoice_id=invoice.id,
            store_name=invoice.store_name,
            invoice_date=invoice.date.isoformat(),
            category=invoice.category,
        )
    except Exception:
        pass  # Vector store failure is non-blocking

    return invoice


@router.get("", response_model=list[InvoiceResponse])
def list_invoices(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = select(Invoice).where(Invoice.user_id == current_user.id)
    if start_date:
        query = query.where(Invoice.date >= start_date)
    if end_date:
        query = query.where(Invoice.date <= end_date)
    query = query.order_by(Invoice.date.desc())
    return session.exec(query).all()


@router.get("/calendar")
def get_calendar(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import func, extract

    query = (
        select(
            Invoice.date,
            func.count(Invoice.id).label("count"),
            func.sum(Invoice.total_amount).label("total_amount"),
        )
        .where(Invoice.user_id == current_user.id)
        .where(extract("year", Invoice.date) == year)
        .where(extract("month", Invoice.date) == month)
        .group_by(Invoice.date)
        .order_by(Invoice.date)
    )
    results = session.exec(query).all()
    return [
        {"date": row[0].isoformat(), "count": row[1], "total_amount": float(row[2])}
        for row in results
    ]


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
def get_invoice(
    invoice_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    invoice = session.exec(
        select(Invoice).where(
            and_(Invoice.id == invoice_id, Invoice.user_id == current_user.id)
        )
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    items = session.exec(
        select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id)
    ).all()

    return InvoiceDetailResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        store_name=invoice.store_name,
        date=invoice.date,
        total_amount=invoice.total_amount,
        category=invoice.category,
        created_at=invoice.created_at,
        items=[ItemResponse(id=i.id, name=i.name, price=i.price, quantity=i.quantity) for i in items],
        raw_text=invoice.raw_text,
        ai_raw_output=invoice.ai_raw_output,
    )


@router.put("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    vector_store=Depends(get_vector_store),
):
    invoice = session.exec(
        select(Invoice).where(
            and_(Invoice.id == invoice_id, Invoice.user_id == current_user.id)
        )
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    update_data = data.model_dump(exclude_unset=True)
    if "category" in update_data and update_data["category"] is not None:
        update_data["category"] = update_data["category"].value

    items_data = update_data.pop("items", None)

    for key, value in update_data.items():
        setattr(invoice, key, value)
    session.add(invoice)
    session.commit()
    session.refresh(invoice)

    if items_data is not None:
        # Delete old items
        old_items = session.exec(
            select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id)
        ).all()
        for item in old_items:
            session.delete(item)
        session.commit()

        # Create new items
        items_for_vector = []
        for item_data in items_data:
            item = InvoiceItem(
                invoice_id=invoice.id,
                name=item_data["name"],
                price=item_data["price"],
                quantity=item_data.get("quantity", 1),
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            items_for_vector.append({"id": item.id, "name": item.name, "price": item.price})

        try:
            vector_store.delete_by_invoice(invoice.id)
            vector_store.add_items(
                items=items_for_vector,
                user_id=current_user.id,
                invoice_id=invoice.id,
                store_name=invoice.store_name,
                invoice_date=invoice.date.isoformat(),
                category=invoice.category,
            )
        except Exception:
            pass

    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    vector_store=Depends(get_vector_store),
):
    invoice = session.exec(
        select(Invoice).where(
            and_(Invoice.id == invoice_id, Invoice.user_id == current_user.id)
        )
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Delete items
    items = session.exec(
        select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id)
    ).all()
    for item in items:
        session.delete(item)

    session.delete(invoice)
    session.commit()

    try:
        vector_store.delete_by_invoice(invoice_id)
    except Exception:
        pass
