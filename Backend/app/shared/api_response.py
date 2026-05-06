from typing import Any

from fastapi.responses import JSONResponse


def success_response(data: Any = None, message: str = "Success"):
    return {"message": message, "data": data}


def error_response(status_code: int, message: str, code: str, errors: dict[str, list[str]] | None = None):
    return JSONResponse(
        status_code=status_code,
        content={
            "message": message,
            "code": code,
            "errors": errors or {},
        },
    )
