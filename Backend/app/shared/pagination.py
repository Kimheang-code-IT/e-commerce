def normalize_page_limit(page: int, limit: int) -> tuple[int, int]:
    return max(page, 1), max(1, min(limit, 200))
