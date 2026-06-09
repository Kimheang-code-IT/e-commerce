from fastapi import Query

from app.schemas.common import ListQuery
from app.shared.pagination_constants import MAX_LIST_PAGE_SIZE


def list_query_dependency(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=MAX_LIST_PAGE_SIZE),
    sortBy: str | None = Query(None, max_length=80),
    sortOrder: str | None = Query(None, pattern="^(asc|desc)$"),
    search: str | None = Query(None, max_length=200),
    dateFrom: str | None = Query(None, max_length=40),
    dateTo: str | None = Query(None, max_length=40),
) -> ListQuery:
    return ListQuery(
        page=page,
        limit=limit,
        sortBy=sortBy,
        sortOrder=sortOrder,
        search=search,
        dateFrom=dateFrom,
        dateTo=dateTo,
    )
