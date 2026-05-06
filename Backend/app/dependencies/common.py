from fastapi import Query

from app.schemas.common import ListQuery


def list_query_dependency(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=200),
    sortBy: str | None = None,
    sortOrder: str | None = Query(None, pattern="^(asc|desc)$"),
    search: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
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
