"""Shared utilities: logging, retries, temp cleanup."""

import functools
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Callable, TypeVar

T = TypeVar("T")

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure root logger and return a named logger."""
    logging.basicConfig(
        format=LOG_FORMAT,
        level=getattr(logging, level.upper(), logging.INFO),
        stream=sys.stdout,
    )
    return logging.getLogger("clipper")


log = setup_logging()


# ── Retry with exponential backoff ───────────────────────────────────


def retry(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator: retry on specified exceptions with exponential backoff."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        log.error(
                            "All %d attempts failed for %s: %s",
                            max_attempts, fn.__name__, exc,
                        )
                        raise
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    log.warning(
                        "Attempt %d/%d for %s failed (%s), retrying in %.1fs",
                        attempt, max_attempts, fn.__name__, exc, delay,
                    )
                    time.sleep(delay)
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


# ── Temp directory management ────────────────────────────────────────


class TempDir:
    """Context manager that creates and cleans a temp working directory."""

    def __init__(self, base: str | None = None, prefix: str = "clipper_"):
        import tempfile

        self.path = Path(tempfile.mkdtemp(prefix=prefix, dir=base))

    def __enter__(self) -> Path:
        return self.path

    def __exit__(self, *_: Any) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        if self.path.exists():
            shutil.rmtree(self.path, ignore_errors=True)
            log.info("Cleaned temp dir: %s", self.path)


# ── Free-tier limit detection ────────────────────────────────────────


class FreeTierLimitError(Exception):
    """Raised when a free-tier API limit is hit."""

    pass

