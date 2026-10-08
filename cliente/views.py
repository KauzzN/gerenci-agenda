import logging

from django.http import JsonResponse

from core.logging import log_event
from users.decorators import client_required, professional_required
from django.contrib.auth.models import User
from .services import validar_cliente, validar_telefone
from agendamento.utils.agendamento_utils import parse_json_body
from .models import Cliente, ClienteProfissional
from public.models import Profile
from users.services.token_services import generate_tokens


logger = logging.getLogger(__name__)


def cliente_entry(request, slug_barber):
    if request.method != "POST":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    try:
        profile = Profile.objects.get(public_slug=slug_barber)
    except Profile.DoesNotExist:
        return JsonResponse({
            "error": "profissional não encontrado"
        }, status=404)

    data, error = parse_json_body(request)
    if error:
        return error

    cliente, erro = validar_cliente(data)
    if erro:
        return JsonResponse({
            "error": str(erro)
        }, status=400)

    client_created = cliente is None
    if client_created:
        telefone, error = validar_telefone(data["telefone"])
        if error:
            return JsonResponse({
                "error": str(error)
            }, status=400)

        user = User.objects.create(username=telefone)
        user.set_unusable_password()
        user.save()

        cliente = Cliente.objects.create(
            user=user,
            telefone=telefone,
            nome=data["nome"].strip()
        )
    else:
        user = cliente.user

    _, relation_created = ClienteProfissional.objects.get_or_create(
        cliente=cliente,
        profile=profile
    )

    tokens = generate_tokens(user)
    if client_created:
        log_event(
            logger,
            logging.INFO,
            "client.created",
            client_id=cliente.id,
            professional_id=profile.user_id,
            user_id=user.id,
            status_code=201,
        )
    elif relation_created:
        log_event(
            logger,
            logging.INFO,
            "client.professional_linked",
            client_id=cliente.id,
            professional_id=profile.user_id,
            user_id=user.id,
            status_code=201,
        )

    return JsonResponse({
        "message": "cliente autenticado",
        "cliente": {
            "user": user.id,
            "nome": cliente.nome,
            "telefone": cliente.telefone,
            "profissional": profile.nome_negocio
        },
        "tokens": tokens
    }, status=201)


@client_required
def read_own_profile(request):
    if request.method != "GET":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    cliente = request.cliente

    return JsonResponse({
        "cliente": {
            "id": cliente.id,
            "nome": cliente.nome,
            "telefone": cliente.telefone,
        }
    })


@professional_required
def read_profile_clients(request):
    if request.method != "GET":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    user = request.user

    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return JsonResponse({
            "error": "profissional não encontrado"
        }, status=404)

    clientes = Cliente.objects.filter(relacoes_profissionais__profile=profile).distinct()
    lista_clientes = []

    for cliente in clientes:
        lista_clientes.append({
            "id": cliente.id,
            "nome": cliente.nome,
            "telefone": cliente.telefone,
        })

    return JsonResponse({
        "clientes": lista_clientes
    }, status=200)