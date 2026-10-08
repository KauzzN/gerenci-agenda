import logging

from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.db import transaction

from agendamento.utils.agendamento_utils import parse_json_body
from core.logging import log_event
from public.models import Profile
from public.services.public_services import atualizar_profile, atualizar_horario
from users.decorators import jwt_required
from django.contrib.auth.models import User
from .services.token_services import generate_tokens, validate_refresh_token


logger = logging.getLogger(__name__)


def _refresh_failure_reason(error):
    if "expirado" in error:
        return "expired"
    if "revogado" in error:
        return "revoked"
    return "invalid"


def register(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "m?todo n?o permitido"
        }, status=405)

    data, error = parse_json_body(request)
    if error:
        return error

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return JsonResponse({
            "error": "username, email e password s?o obrigat?rios"
        }, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({
            "error": "username j? existe"
        }, status=400)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )

    Profile.objects.create(user=user)

    user = authenticate(username=username, password=password)
    if not user:
        log_event(
            logger,
            logging.WARNING,
            "auth.register_failed",
            reason="authentication_failed",
            status_code=404,
        )
        return JsonResponse({
            "error": "usuario n?o encontrado"
        }, status=404)

    tokens = generate_tokens(user)
    log_event(
        logger,
        logging.INFO,
        "auth.register_success",
        user_id=user.id,
        status_code=200,
    )

    return JsonResponse({
        "message": "usu?rio criado com sucesso",
        "tokens": tokens
    }, status=200)


def login_user(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "m?todo n?o permitido"
        }, status=405)

    data, error = parse_json_body(request)
    if error:
        return error

    username = data.get("username")
    password = data.get("password")

    if not username:
        log_event(
            logger,
            logging.WARNING,
            "auth.login_failed",
            reason="missing_username",
            status_code=401,
        )
        return JsonResponse({
            "error": "usuario inv?lido"
        }, status=401)

    if not password:
        log_event(
            logger,
            logging.WARNING,
            "auth.login_failed",
            reason="missing_password",
            status_code=401,
        )
        return JsonResponse({
            "error": "password inv?lido"
        }, status=401)

    user = authenticate(username=username, password=password)
    if not user:
        log_event(
            logger,
            logging.WARNING,
            "auth.login_failed",
            reason="invalid_credentials",
            status_code=404,
        )
        return JsonResponse({
            "error": "usuario n?o encontrado"
        }, status=404)

    tokens = generate_tokens(user)
    log_event(
        logger,
        logging.INFO,
        "auth.login_success",
        user_id=user.id,
        status_code=200,
    )

    return JsonResponse({
        "message": "autentica??o concluida",
        "tokens": tokens
    }, status=200)


@jwt_required
def me_user(request):
    if request.method != "GET":
        return JsonResponse({
            "error": "m?todo n?o permitido"
        }, status=405)

    user = request.user

    return JsonResponse({
        "id": user.id,
        "username": user.username,
        "email": user.email
    })


@jwt_required
def update_profile(request):
    if request.method != "PATCH":
        return JsonResponse({
            "error": "met?do n?o permitido"
        }, status=405)

    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return JsonResponse({
            "error": "barbearia n?o encontrada"
        }, status=404)

    data, error = parse_json_body(request)
    if error:
        return error

    profile_fields = (
        "public_slug",
        "nome_negocio",
        "telefone",
        "endereco",
        "instagram",
        "descricao",
    )
    schedule_fields = (
        "dias_funcionando",
        "horario_inicio",
        "horario_fim",
        "inicio_almoco",
        "fim_almoco",
    )
    original_values = {
        field: getattr(profile, field)
        for field in profile_fields + schedule_fields
    }

    with transaction.atomic():
        updated_profile, error = atualizar_profile(profile, data)
        if error:
            status = 409 if error == "esse slug já existe" else 400
            return JsonResponse({
                "error": error
            }, status=status)

        updated_schedule, error = atualizar_horario(profile, data)
        if error:
            transaction.set_rollback(True)
            return JsonResponse({
                "error": error
            }, status=400)

        updated = updated_profile or updated_schedule

    if not updated:
        return JsonResponse({
            "message": "nenhuma altera??o realizada"
        }, status=200)

    changed_profile_fields = [
        field
        for field in profile_fields
        if getattr(profile, field) != original_values[field]
    ]
    changed_schedule_fields = [
        field
        for field in schedule_fields
        if getattr(profile, field) != original_values[field]
    ]
    if changed_profile_fields:
        log_event(
            logger,
            logging.INFO,
            "profile.updated",
            user_id=request.user.id,
            changed_fields=changed_profile_fields,
            status_code=200,
        )
    if changed_schedule_fields:
        log_event(
            logger,
            logging.INFO,
            "schedule.updated",
            user_id=request.user.id,
            changed_fields=changed_schedule_fields,
            status_code=200,
        )

    return JsonResponse({
        "message": "profile atualizada",
        "profile": {
            "user": str(profile.user),
            "public_slug": profile.public_slug,
            "nome_negocio": profile.nome_negocio,
            "telefone": profile.telefone,
            "endereco": profile.endereco,
            "instagram": profile.instagram,
            "descricao": profile.descricao,
            "inicio expediente": profile.horario_inicio,
            "fim expediente": profile.horario_fim,
            "inicio almo?o": profile.inicio_almoco,
            "fim almo?o": profile.fim_almoco,
            "dias_funcionando": profile.dias_funcionando,
        }
    })


def refresh_session(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "m?todo n?o permitido"
        }, status=405)

    data, error = parse_json_body(request)
    if error:
        return error

    token = data.get("refresh_token")
    if not token:
        log_event(
            logger,
            logging.WARNING,
            "auth.refresh_failed",
            reason="missing",
            status_code=400,
        )
        return JsonResponse({
            "error": "refresh_token n?o inserido"
        }, status=400)

    refresh_token, error = validate_refresh_token(token)
    if error:
        log_event(
            logger,
            logging.WARNING,
            "auth.refresh_failed",
            reason=_refresh_failure_reason(error),
            status_code=400,
        )
        return JsonResponse({
            "error": error
        }, status=400)

    if refresh_token.user is None:
        refresh_token.revoked = True
        log_event(
            logger,
            logging.WARNING,
            "auth.refresh_failed",
            reason="invalid",
            status_code=400,
        )
        return JsonResponse({
            "error": "refresh_token inv?lido"
        }, status=400)

    user = refresh_token.user
    return JsonResponse(generate_tokens(user))


@jwt_required
def meu_profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return JsonResponse({
            "error": "barbearia n?o encontrada"
        }, status=404)

    return JsonResponse({
        "public_slug": profile.public_slug,
        "nome_negocio": profile.nome_negocio,
        "telefone": profile.telefone,
        "endereco": profile.endereco,
        "instagram": profile.instagram,
        "descricao": profile.descricao,
        "horario_inicio": profile.horario_inicio.isoformat() if profile.horario_inicio else None,
        "horario_fim": profile.horario_fim.isoformat() if profile.horario_fim else None,
        "inicio_almoco": profile.inicio_almoco.isoformat() if profile.inicio_almoco else None,
        "fim_almoco": profile.fim_almoco.isoformat() if profile.fim_almoco else None,
        "dias_funcionando": profile.dias_funcionando,
    })
