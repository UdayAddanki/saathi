"""Turn model and pipeline failures into a type we can log and a message a teacher can act on."""
from __future__ import annotations

from pydantic_ai.exceptions import (
    ModelAPIError,
    ModelHTTPError,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
)

BUDGET = "budget"
AUTH = "auth"
TOO_LONG = "too_long"
INVALID_OUTPUT = "invalid_output"
TIMEOUT = "timeout"
BUSY = "busy"
UNKNOWN = "unknown"

# Failures worth one automatic retry: they usually succeed on a second attempt.
TRANSIENT = {INVALID_OUTPUT, TIMEOUT, BUSY}

MESSAGES = {
    BUDGET: "You've used today's limit. It resets at midnight.",
    AUTH: "Saathi couldn't reach the AI service: the API key is missing or was rejected.",
    TOO_LONG: "This plan came out too long to finish. Please try again, or turn off differentiation for this lesson.",
    INVALID_OUTPUT: "Saathi couldn't put this lesson into the right shape. Please try again; a shorter note can help.",
    TIMEOUT: "Saathi took too long to respond. Please try again.",
    BUSY: "The AI service is busy right now. Please try again in a minute.",
    UNKNOWN: "Something went wrong while preparing this. Please try again.",
}


def classify(error: BaseException) -> str:
    """Return one of the error types above for any exception raised during a run."""
    if isinstance(error, RuntimeError) and "today's limit" in str(error):
        return BUDGET
    if isinstance(error, UsageLimitExceeded):
        return TOO_LONG
    if isinstance(error, ModelHTTPError):
        if error.status_code in (401, 403):
            return AUTH
        if error.status_code in (408, 504):
            return TIMEOUT
        if error.status_code == 429 or error.status_code >= 500:
            return BUSY
        return UNKNOWN
    name = type(error).__name__
    if "Timeout" in name or "TimedOut" in name:
        return TIMEOUT
    if isinstance(error, UnexpectedModelBehavior):
        return INVALID_OUTPUT
    if isinstance(error, ModelAPIError):
        return BUSY
    if isinstance(error, (TimeoutError, ConnectionError)):
        return TIMEOUT
    return UNKNOWN


def teacher_message(error_type: str) -> str:
    return MESSAGES.get(error_type, MESSAGES[UNKNOWN])
