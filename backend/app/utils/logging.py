# Logging setup.
import logging
import sys

from app.config import settings

_CONFIGURED = False


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]
    for noisy in ("uvicorn.access", "uvicorn.error"):
        logging.getLogger(noisy).handlers = []
    for module in (
        "python_multipart",
        "PIL",
        "matplotlib",
        "urllib3",
        "watchfiles",
        "asyncio",
    ):
        logging.getLogger(module).setLevel(logging.WARNING)
    _CONFIGURED = True


logger = logging.getLogger("app")
