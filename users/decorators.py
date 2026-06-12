import jwt
from django.conf import settings
from django.http import JsonResponse
from functools import wraps
from django.contrib.auth.models import User


def jwt_required(view_func):
    
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JsonResponse({
                "error": "token não fornecido"
            }, status=401)
            
        if not auth_header.startswith("Bearer "):
            return JsonResponse({
                "error": "formato de token inválido"
            }, status=401)

        try:
            token = auth_header.split(" ")[1]
            
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            
            print(payload)
            
            user_id = payload.get("sub")
            
            user = User.objects.get(id=user_id)
            
            request.user = user
            
        except jwt.ExpiredSignatureError:
            return JsonResponse({
                "error": "token expirado"
            }, status=401)
            
        except jwt.InvalidTokenError:
            return JsonResponse({
                "error": "token inválido"
            }, status=401)
            
        except User.DoesNotExist:
            return JsonResponse({
                "error": "token inválido"
            }, status=401)
            
        except Exception as e:
            print(e)
            raise
            
        return view_func(request, *args, **kwargs)
    
    return wrapper