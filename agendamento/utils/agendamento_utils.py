import json
from django.http import JsonResponse

def parse_json_body(request):
    if not request.content_type.startswith("application/json"):
        return None, JsonResponse({
            "error": "content_type deve ser application/json"
        }, status=400)
        
    try:
        data = json.loads(request.body.decode("utf-8"))
        return data, None
    
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, JsonResponse({
            "error": "json inválido"
        }, status=400)