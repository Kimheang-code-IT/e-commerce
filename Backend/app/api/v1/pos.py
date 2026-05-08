import json
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import User
from app.schemas.common import PosCheckoutPayload, PosPreviewSessionCreatePayload
from app.services.auth_service import get_current_user, require_permission
from app.services.pos_service import (
    calculate_totals_service,
    complete_checkout_service,
    decode_preview,
    encode_preview,
    invoice_preview_by_no,
)
from app.shared.api_response import error_response

router = APIRouter(prefix="/invoices", tags=["invoices"], dependencies=[Depends(get_current_user)])
pos_router = APIRouter(prefix="/pos", tags=["pos"], dependencies=[Depends(get_current_user)])


@router.post("/preview-sessions")
@pos_router.post("/preview")
def create_preview_session(
    payload: PosPreviewSessionCreatePayload,
    _=Depends(require_permission("pos:view")),
):
    return encode_preview(payload)


@router.get("/preview-sessions/{preview_key}")
@pos_router.get("/preview/{preview_key}")
def get_preview_session(
    preview_key: str,
    _=Depends(require_permission("pos:view")),
):
    try:
        invoices = decode_preview(preview_key)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return error_response(status.HTTP_400_BAD_REQUEST, "Invalid preview key", "BAD_REQUEST")
    return {"invoices": invoices}


@router.post("/calculate-totals")
@pos_router.post("/calculate-totals")
def calculate_totals(
    payload: PosCheckoutPayload,
    _=Depends(require_permission("pos:view")),
    db: Session = Depends(get_db),
):
    return calculate_totals_service(db=db, payload=payload)


@router.post("/checkout")
@pos_router.post("/checkout")
def complete_checkout(
    payload: PosCheckoutPayload,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("pos:create")),
    db: Session = Depends(get_db),
):
    return complete_checkout_service(
        db=db, 
        payload=payload, 
        current_user=current_user, 
        background_tasks=background_tasks
    )


@pos_router.get("/invoice/{invoice_no}")
def get_invoice_preview_by_no(
    invoice_no: str,
    _=Depends(require_permission("pos:view")),
    db: Session = Depends(get_db),
):
    return invoice_preview_by_no(db=db, invoice_no=invoice_no)
