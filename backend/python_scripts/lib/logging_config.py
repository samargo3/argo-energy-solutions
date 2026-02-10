import json
import logging
import sys
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Attach extra fields (if any)
        for key, value in record.__dict__.items():
            if key in ("args", "msg", "levelname", "levelno", "name",
                       "pathname", "filename", "module", "exc_info",
                       "exc_text", "stack_info", "lineno", "funcName",
                       "created", "msecs", "relativeCreated", "thread",
                       "threadName", "processName", "process"):
                continue
            payload.setdefault("extra", {})[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


_configured = False


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger once with JSON output to stdout."""
    global _configured
    if _configured:
        return

    root = logging.getLogger()
    root.setLevel(level.upper())

    # Remove default handlers that some deps may have added
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)