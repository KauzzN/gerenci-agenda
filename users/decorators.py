import jwt

from functools import wraps
from django.conf import settings
from django.http import JsonResponse

from users.models import User
from public.models import Profile
from cliente.models import Cliente

def authenticate_request(request):

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None, JsonResponse({
            "error": "token não fornecido"
        }, status=401)

    if not auth_header.startswith("Bearer "):
        return None, JsonResponse({
            "error": "formato de token inválido"
        }, status=401)

    try:
        token = auth_header.split(" ", 1)[1]

        if not token:
            return None, JsonResponse({
                "error": "token inválido"
            }, status=401)

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )

        user_id = payload.get("sub")

        if not user_id:
            return None, JsonResponse({
                "error": "token inválido"
            }, status=401)

        user = User.objects.get(id=user_id)

        return user, None

    except jwt.ExpiredSignatureError:
        return None, JsonResponse({
            "error": "token expirado"
        }, status=401)

    except (jwt.InvalidTokenError, User.DoesNotExist):
        return None, JsonResponse({
            "error": "token inválido"
        }, status=401)

def jwt_required(view_func):
    
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user, error = authenticate_request(request)

        if error:
            return error

        request.user = user

        return view_func(request, *args, **kwargs)
    
    return wrapper

def professional_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user, error = authenticate_request(request)

        if error:
            return error

        profile = Profile.objects.filter(
            user=user
        ).first()

        if not profile:
            return JsonResponse({
                "error": "acesso permitido apenas para profissionais"
            }, status=403)

        request.user = user
        request.profile = profile

        return view_func(request, *args, **kwargs)

    return wrapper

def client_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user, error = authenticate_request(request)

        if error:
            return error

        cliente = Cliente.objects.filter(
            user=user
        ).first()

        if not cliente:
            return JsonResponse({
                "error": "acesso permitido apenas para clientes"
            }, status=403)

        request.user = user
        request.cliente = cliente

        return view_func(request, *args, **kwargs)

    return wrapper