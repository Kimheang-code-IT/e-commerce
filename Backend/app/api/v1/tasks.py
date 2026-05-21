import re

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, status

from app.core.celery_app import celery_app
from app.models import User
from app.services.auth_service import get_current_user, require_permission
from app.shared.api_response import error_response

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(get_current_user)])

_CHECKOUT_TASK_ID = re.compile(
    r"^checkout-(pdf|print|notify|cache)-\d+$"
)


@router.get("/{task_id}")
def get_task_status(
    task_id: str,
    _: User = Depends(require_permission("pos:view")),
):
    """Poll Celery task state for checkout follow-up jobs."""
    if not _CHECKOUT_TASK_ID.match(task_id):
        return error_response(status.HTTP_400_BAD_REQUEST, "Invalid task id", "BAD_REQUEST")

    result = AsyncResult(task_id, app=celery_app)
    payload: dict = {
        "taskId": task_id,
        "status": result.status,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
    }
    if result.ready():
        if result.successful():
            payload["result"] = result.result
        else:
            payload["error"] = str(result.result) if result.result else "Task failed"
    elif result.info and isinstance(result.info, dict):
        payload["meta"] = result.info
    return {"data": payload}
