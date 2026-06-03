import logging
import sys

from loguru import logger

from app.core.config import settings


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        level = record.levelname
        logger.opt(exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level.upper(),
        serialize=settings.log_json,
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )

    logging.basicConfig(
        handlers=[InterceptHandler()],
        level=logging.getLevelName(settings.log_level.upper()),
        force=True,
    )

    # Route common framework logs through Loguru as well.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        framework_logger = logging.getLogger(name)
        framework_logger.handlers = [InterceptHandler()]
        framework_logger.propagate = False
