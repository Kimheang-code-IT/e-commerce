from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import require_permission
from app.services.backup_service import backup_service

router = APIRouter(prefix="/backups/google-sheet", tags=["backups"])

@router.post("/all")
def trigger_all_backups(
    db: Session = Depends(get_db),
    _=Depends(require_permission("backup:manage"))
):
    """Manual trigger for all Google Sheets backups."""
    results = backup_service.backup_all(db)
    return {
        "message": "All Google Sheets backups completed",
        "results": results
    }

@router.post("/products")
def backup_products(db: Session = Depends(get_db), _=Depends(require_permission("backup:manage"))):
    result = backup_service.backup_products(db)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result

@router.post("/categories")
def backup_categories(db: Session = Depends(get_db), _=Depends(require_permission("backup:manage"))):
    result = backup_service.backup_categories(db)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result

@router.post("/invoices")
def backup_invoices(db: Session = Depends(get_db), _=Depends(require_permission("backup:manage"))):
    result = backup_service.backup_invoices(db)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result

@router.post("/invoice-details")
def backup_invoice_details(db: Session = Depends(get_db), _=Depends(require_permission("backup:manage"))):
    result = backup_service.backup_invoice_details(db)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result

@router.post("/deliveries")
def backup_deliveries(db: Session = Depends(get_db), _=Depends(require_permission("backup:manage"))):
    result = backup_service.backup_deliveries(db)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result

@router.post("/users")
def backup_users(db: Session = Depends(get_db), _=Depends(require_permission("backup:manage"))):
    result = backup_service.backup_users(db)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result

@router.post("/roles")
def backup_roles(db: Session = Depends(get_db), _=Depends(require_permission("backup:manage"))):
    result = backup_service.backup_roles(db)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result
