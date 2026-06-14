import logging
from typing import Any
from app.core.constants import SYSTEM_REQUEST_ID


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = SYSTEM_REQUEST_ID

        return True


def initialize_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | %(name)s "
            "| request_id=%(request_id)s | %(message)s"
        ),
    )

    logging.getLogger().addFilter(
        RequestIdFilter(),
    )


def log_extra(
    request_id: str | None,
    **kwargs: Any,
) -> dict[str, Any]:
    return {
        "request_id": request_id,
        **kwargs,
    }
