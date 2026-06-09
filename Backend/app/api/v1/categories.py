from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import String, cast, or_, select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Category, Product, User
from app.schemas.common import CategoryCreatePayload, CategoryUpdatePayload
from app.services.auth_service import get_current_user, require_permission
from app.services.data_service import (
    apply_created_at_range,
    apply_sort,
    list_response,
    paginate_query,
    serialize_category,
    record_history,
)
from app.services.cache_service import (
    cached_response,
    invalidate_categories_and_dashboard,
    invalidate_products_and_dashboard,
    PREFIX_CATEGORIES,
)
from app.shared.api_response import error_response
from app.shared.pagination_constants import MAX_LIST_PAGE_SIZE

router = APIRouter()

@router.get("/categories")
def list_categories(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=MAX_LIST_PAGE_SIZE),
    search: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    sortBy: str | None = None,
    sortOrder: str | None = Query(None, pattern="^(asc|desc)$"),
    _: User = Depends(require_permission("category:view")),
    db: Session = Depends(get_db),
):
    cache_parts = {
        "page": page,
        "limit": limit,
        "search": search,
        "dateFrom": dateFrom,
        "dateTo": dateTo,
        "sortBy": sortBy,
        "sortOrder": sortOrder,
    }

    def _build():
        q_inner = select(Category)
        if search:
            keyword = search.strip()
            db_id = Category.from_public_id(keyword)
            predicates = [
                Category.name.ilike(f"%{keyword}%"),
                Category.description.ilike(f"%{keyword}%"),
                cast(Category.id, String).ilike(f"%{keyword}%"),
            ]
            if db_id is not None:
                predicates.append(Category.id == db_id)
            q_inner = q_inner.where(or_(*predicates))
        q_inner = apply_created_at_range(q_inner, dateFrom, dateTo, Category.created_at)
        q_inner = apply_sort(
            q_inner,
            sortBy,
            sortOrder,
            {"id": Category.id, "name": Category.name, "total": Category.product_count, "createdAt": Category.created_at},
        )
        rows_inner, total_inner = paginate_query(q_inner, db, page, limit)
        return list_response([serialize_category(row[0]) for row in rows_inner], total_inner)

    return cached_response(PREFIX_CATEGORIES, cache_parts, _build)


@router.post("/categories")
def create_category(
    body: CategoryCreatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("category:create")),
    db: Session = Depends(get_db),
):
    existing = db.execute(select(Category).where(Category.name.ilike(body.name))).scalar_one_or_none()
    if existing:
        return error_response(status.HTTP_409_CONFLICT, "Category name already exists", "CONFLICT")
    row = Category(name=body.name, description=body.description)
    db.add(row)
    db.commit()
    db.refresh(row)
    record_history(db, current_user.id, "Create", f"Created category '{row.name}'")
    db.commit()
    invalidate_categories_and_dashboard()
    invalidate_products_and_dashboard()
    return {"data": serialize_category(row)}


@router.put("/categories/{item_id}")
def update_category(
    item_id: str,
    body: CategoryUpdatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("category:update")),
    db: Session = Depends(get_db),
):
    db_id = Category.from_public_id(item_id)
    if db_id is None:
        return error_response(status.HTTP_400_BAD_REQUEST, "Invalid category id", "BAD_REQUEST")
    row = db.get(Category, db_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Not found", "NOT_FOUND")
    
    previous_name = row.name
    next_name = body.name if body.name is not None else row.name
    if body.name is not None and body.name != previous_name:
        duplicate = db.execute(select(Category).where(Category.name.ilike(body.name), Category.id != row.id)).scalar_one_or_none()
        if duplicate:
            return error_response(status.HTTP_409_CONFLICT, "Category name already exists", "CONFLICT")
        row.name = next_name
    
    if body.description is not None:
        row.description = body.description
    
    db.commit()
    db.refresh(row)
    record_history(db, current_user.id, "Update", f"Updated category '{row.name}'")
    db.commit()
    invalidate_categories_and_dashboard()
    invalidate_products_and_dashboard()
    return {"data": serialize_category(row)}


@router.delete("/categories/{item_id}")
def delete_category(
    item_id: str,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("category:delete")),
    db: Session = Depends(get_db),
):
    db_id = Category.from_public_id(item_id)
    if db_id is None:
        return error_response(status.HTTP_400_BAD_REQUEST, "Invalid category id", "BAD_REQUEST")
    row = db.get(Category, db_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Not found", "NOT_FOUND")
    
    in_use_product_id = db.scalar(select(Product.id).where(Product.category_id == row.id).limit(1))
    if in_use_product_id is not None:
        return error_response(status.HTTP_409_CONFLICT, "Cannot delete category as it has products using it", "CONFLICT")
    
    category_name = row.name
    db.delete(row)
    db.commit()
    record_history(db, current_user.id, "Delete", f"Deleted category '{category_name}'")
    db.commit()
    invalidate_categories_and_dashboard()
    invalidate_products_and_dashboard()
    return {"message": "Category deleted"}
