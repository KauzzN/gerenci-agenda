import re
import time
import uuid

from django.http import JsonResponse

from .logging import reset_request_context, set_request_context


_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._~-]{1,64}$")


class ApiMiddleware:
    """Apply API-specific request handling without changing Admin CSRF."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming_request_id = request.headers.get("X-Request-ID", "")
        request_id = (
            incoming_request_id
            if _REQUEST_ID_PATTERN.fullmatch(incoming_request_id)
            else str(uuid.uuid4())
        )
        context_token = set_request_context(
            request_id=request_id,
            method=request.method,
            path=request.path,
        )
        request.request_id = request_id
        started_at = time.perf_counter()

        try:
            if request.path.startswith("/api/"):
                request._dont_enforce_csrf_checks = True

                if request.method == "OPTIONS":
                    response = JsonResponse({}, status=200)
                else:
                    response = self.get_response(request)
            else:
                response = self.get_response(request)

            request.duration_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )
            response["X-Request-ID"] = request_id
            return response
        finally:
            reset_request_context(context_token)
