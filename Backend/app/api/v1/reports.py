from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import get_current_user, require_permission
from app.services.data_service import export_payload, list_response
from app.services.filter_options_service import report_filter_options
from app.services.report_service import export_report_invoices, list_report_invoices

router = APIRouter(prefix="/reports-view", tags=["reports-view"], dependencies=[Depends(get_current_user)])


@router.get("")
def list_reports_view(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    search: str | None = None,
    product: str | None = None,
    province: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    sortBy: str | None = None,
    sortOrder: str | None = Query(None, pattern="^(asc|desc)$"),
    _=Depends(require_permission("report:view")),
    db: Session = Depends(get_db),
):
    result, total = list_report_invoices(
        db,
        page=page,
        limit=limit,
        search=search,
        product=product,
        province=province,
        date_from=dateFrom,
        date_to=dateTo,
        sort_by=sortBy,
        sort_order=sortOrder,
    )
    return list_response(result, total)


@router.get("/export")
def export_reports_view(
    search: str | None = None,
    product: str | None = None,
    province: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    format: str = Query("json", pattern="^(json|csv)$"),
    _=Depends(require_permission("report:view")),
    db: Session = Depends(get_db),
):
    result = export_report_invoices(
        db,
        search=search,
        product=product,
        province=province,
        date_from=dateFrom,
        date_to=dateTo,
    )
    return export_payload(result, "reports-view", format)


@router.get("/filter-options")
def reports_filter_options(
    dateFrom: str | None = None,
    dateTo: str | None = None,
    _=Depends(require_permission("report:view")),
    db: Session = Depends(get_db),
):
    return {"data": report_filter_options(db, date_from=dateFrom, date_to=dateTo)}
