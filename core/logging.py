import logging
from contextvars import ContextVar


_request_context = ContextVar("request_context", default={})

_FORBIDDEN_FIELDS = {
    "password",
    "access_token",
    "refresh_token",
    "jwt",
    "authorization",
    "cookie",
    "secret_key",
    "database_url",
    "request_body",
    "request_post",
    "request_get",
}


def set_request_context(**context):
    return _request_context.set(context)


def reset_request_context(token):
    _request_context.reset(token)


def get_request_id():
    return _request_context.get().get("request_id", "-")


def log_event(logger, level, event, **context):
    event_context = dict(_request_context.get())
    event_context.pop("request_id", None)
    event_context.update({
        key: value
        for key, value in context.items()
        if key.lower() not in _FORBIDDEN_FIELDS
    })
    event_context["event"] = event

    message = " ".join(
        f"{key}={value}"
        for key, value in event_context.items()
        if value is not None
    )
    logger.log(level, message)


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        return True
