import os
from typing import Optional

import sentry_sdk


_sentry_initialized = False


def init_sentry(service_name: str) -> None:
    """Initialize Sentry if SENTRY_DSN is set; otherwise no-op."""
    global _sentry_initialized
    if _sentry_initialized:
        return

    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return

    env = os.getenv("ENVIRONMENT", "development")

    sentry_sdk.init(
        dsn=dsn,
        environment=env,
        release=os.getenv("GIT_SHA"),
        traces_sample_rate=0.0,  # turn on later if you want performance traces
    )
    sentry_sdk.set_tag("service", service_name)
    _sentry_initialized = True


def capture_exception(exc: BaseException) -> None:
    """Capture an exception without ever crashing the app if Sentry breaks."""
    try:
        if _sentry_initialized:
            sentry_sdk.capture_exception(exc)
    except Exception:
        # Never let Sentry failures crash the pipeline
        pass
