"""Run async coroutines from sync code (safe inside a running event loop)."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

T = TypeVar("T")

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="async-run")


def run_coro(coro) -> T:
    """Execute *coro* and return its result.

    Uses ``asyncio.run`` when no loop is running; otherwise runs in a worker
    thread so callers (e.g. Telegram polling) do not hit
    "asyncio.run() cannot be called from a running event loop".
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    future = _executor.submit(asyncio.run, coro)
    return future.result(timeout=300)
