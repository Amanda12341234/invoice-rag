import json
import logging
import time
from functools import wraps


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        for key in ("user_id", "endpoint", "duration_ms", "status"):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("invoice_rag")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = setup_logging()


def log_operation(operation: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = round((time.time() - start) * 1000)
                logger.info(
                    f"{operation} completed",
                    extra={"duration_ms": duration_ms, "status": "success"},
                )
                return result
            except Exception as e:
                duration_ms = round((time.time() - start) * 1000)
                logger.error(
                    f"{operation} failed: {e}",
                    extra={"duration_ms": duration_ms, "status": "error"},
                )
                raise
        return wrapper
    return decorator
