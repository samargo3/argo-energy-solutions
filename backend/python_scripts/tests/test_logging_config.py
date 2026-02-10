"""
Unit tests for lib/logging_config.py

Runs offline — no database or network required.
"""

import json
import logging
import sys
from pathlib import Path

# Allow imports from the package root
_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from lib.logging_config import JsonFormatter, get_logger


class TestJsonFormatter:
    def test_output_is_valid_json(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello world", args=None, exc_info=None,
        )
        output = formatter.format(record)
        payload = json.loads(output)
        assert payload["msg"] == "hello world"
        assert payload["level"] == "INFO"
        assert payload["logger"] == "test"

    def test_includes_exception_info(self):
        formatter = JsonFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys as _sys
            exc_info = _sys.exc_info()

        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="error occurred", args=None, exc_info=exc_info,
        )
        output = formatter.format(record)
        payload = json.loads(output)
        assert "exc_info" in payload
        assert "ValueError" in payload["exc_info"]


class TestGetLogger:
    def test_returns_logger_with_name(self):
        logger = get_logger("my.module")
        assert logger.name == "my.module"
        assert isinstance(logger, logging.Logger)
