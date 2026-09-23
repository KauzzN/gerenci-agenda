from django.http import JsonResponse


class ApiMiddleware:
    """Apply API-specific request handling without changing Admin CSRF."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/"):
            request._dont_enforce_csrf_checks = True

            if request.method == "OPTIONS":
                return JsonResponse({}, status=200)

        return self.get_response(request)
