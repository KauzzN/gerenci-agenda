import json
from django.http import JsonResponse


def parse_json_body(request):
    content_type = request.content_type or ""
    if not content_type.startswith("application/json"):
        return None, JsonResponse({
            "error": "content_type deve ser application/json"
        }, status=400)

    body = request.body or b""
    if not body or body.strip() == b"":
        return None, JsonResponse({
            "error": "json inválido"
        }, status=400)

    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, JsonResponse({
            "error": "json inválido"
        }, status=400)

    if data is None or not isinstance(data, dict):
        return None, JsonResponse({
            "error": "json inválido"
        }, status=400)

    return data, None