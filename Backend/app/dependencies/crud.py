from fastapi import HTTPException, status


def get_or_404(entity, label: str = "Resource"):
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return entity
