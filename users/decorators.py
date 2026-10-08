import logging

import jwt

from functools import wraps
from django.conf import settings
from django.http import JsonResponse

from core.logging import log_event
from users.models import User
from public.models import Profile
from cliente.models import Cliente


logger = logging.getLogger(__name__)


def authenticate_request(request):
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        log_event(
            logger,
            logging.WARNING,
            "auth.unauthorized",
            reason="missing_token",
            status_code=401,
        )
        return None, JsonResponse({
            "error": "token não fornecido"
        }, status=401)

    if not auth_header.startswith("Bearer "):
        log_event(
            logger,
            logging.WARNING,
            "auth.unauthorized",
            reason="invalid_scheme",
            status_code=401,
        )
        return None, JsonResponse({
            "error": "formato de token inválido"
        }, status=401)

    try:
        token = auth_header.split(" ", 1)[1]

        if not token:
            log_event(
                logger,
                logging.WARNING,
                "auth.unauthorized",
                reason="empty_token",
                status_code=401,
            )
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
            log_event(
                logger,
                logging.WARNING,
                "auth.unauthorized",
                reason="missing_subject",
                status_code=401,
            )
            return None, JsonResponse({
                "error": "token inválido"
            }, status=401)

        user = User.objects.get(id=user_id)
        return user, None

    except jwt.ExpiredSignatureError:
        log_event(
            logger,
            logging.WARNING,
            "auth.unauthorized",
            reason="expired_token",
            status_code=401,
        )
        return None, JsonResponse({
            "error": "token expirado"
        }, status=401)

    except (jwt.InvalidTokenError, User.DoesNotExist):
        log_event(
            logger,
            logging.WARNING,
            "auth.unauthorized",
            reason="invalid_token",
            status_code=401,
        )
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

        try:
            profile = user.profile
        except Profile.DoesNotExist:
            log_event(
                logger,
                logging.WARNING,
                "auth.forbidden",
                user_id=user.id,
                reason="professional_profile_required",
                status_code=403,
            )
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

        try:
            cliente = user.cliente
        except Cliente.DoesNotExist:
            log_event(
                logger,
                logging.WARNING,
                "auth.forbidden",
                user_id=user.id,
                reason="client_profile_required",
                status_code=403,
            )
            return JsonResponse({
                "error": "acesso permitido apenas para clientes"
            }, status=403)

        request.user = user
        request.cliente = cliente
        return view_func(request, *args, **kwargs)

    return wrapper