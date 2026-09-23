from datetime import datetime, timedelta
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from agendamento.utils.agendamento_utils import parse_json_body
from agendamento.validators import validar_data, validar_horario
from agendamento.booking_rules import (
    has_schedule_conflict,
    load_active_services,
    parse_service_ids,
    within_business_hours,
)
from agendamento.models import Agendamento, ItemAgendamento
from cliente.models import ClienteProfissional
from servicos.models import Servico
from users.decorators import client_required
from .models import Profile


@client_required
def horarios_disponiveis(request, slug_barber):
    if request.method != "GET":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    try:
        profile = Profile.objects.get(public_slug=slug_barber)

    except Profile.DoesNotExist:
        return JsonResponse({
            "error": "barbearia não encontrada"
        }, status=404)

    data_inserida = request.GET.get("data")

    data_formatada, erro = validar_data(data_inserida)

    if erro:
        return JsonResponse({
            "error": erro
        }, status=400)

    service_ids = parse_service_ids(request.GET.getlist("servicos"))
    if service_ids is None:
        return JsonResponse({
            "error": "servicos deve conter uma lista de IDs válidos"
        }, status=400)

    services = load_active_services(profile.user, service_ids)
    if services is None:
        return JsonResponse({
            "error": "serviço não encontrado ou está inativo"
        }, status=400)

    if profile.horario_inicio is None or profile.horario_fim is None:
        return JsonResponse({
            "error": "expediente não configurado"
        }, status=400)

    duracao_total = sum(service.duracao for service in services)
    inicio_dia = timezone.make_aware(
        datetime.combine(data_formatada, profile.horario_inicio)
    )
    fim_dia = timezone.make_aware(
        datetime.combine(data_formatada, profile.horario_fim)
    )
    passo = timedelta(minutes=30)
    duracao = timedelta(minutes=duracao_total)
    horarios_livres = []
    horario_atual = inicio_dia

    while horario_atual + duracao <= fim_dia:
        horario_fim = horario_atual + duracao
        if (
            horario_atual > timezone.now()
            and within_business_hours(profile, horario_atual, horario_fim)
            and not has_schedule_conflict(
                profile.user,
                horario_atual,
                horario_fim,
            )
        ):
            horarios_livres.append({
                "horario": timezone.localtime(horario_atual).strftime("%H:%M")
            })
        horario_atual += passo

    return JsonResponse({
        "barbearia": profile.nome_negocio,
        "slug": profile.public_slug,
        "data": str(data_formatada),
        "horarios": horarios_livres
    }, status=200)


@client_required
def agendar_horario(request, slug_barber):

    if request.method != "POST":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    try:
        profile = Profile.objects.get(public_slug=slug_barber)
    except Profile.DoesNotExist:
        return JsonResponse({
            "error": "barbearia não encontrada"
        }, status=404)

    data, error = parse_json_body(request)

    if error:
        return error

    if not isinstance(data, dict):
        return JsonResponse({
            "error": "json inválido"
        }, status=400)

    service_ids = data.get("servicos")
    if not isinstance(service_ids, list):
        return JsonResponse({
            "error": "servicos deve ser uma lista"
        }, status=400)

    service_ids = parse_service_ids(service_ids)
    if service_ids is None:
        return JsonResponse({
            "error": "servicos deve conter uma lista de IDs válidos"
        }, status=400)

    services = load_active_services(profile.user, service_ids)
    if services is None:
        return JsonResponse({
            "error": "serviço não encontrado ou está inativo"
        }, status=400)

    horario_inicio = data.get("horario_inicio")
    if not horario_inicio:
        return JsonResponse({
            "error": "horario_inicio não inserido"
        }, status=400)

    horario_inicio, error = validar_horario(horario_inicio)
    if error:
        return JsonResponse({
            "error": error
        }, status=400)

    relacao = ClienteProfissional.objects.filter(
        cliente=request.cliente,
        profile=profile,
        ativo=True
    ).exists()
    if not relacao:
        return JsonResponse({
            "error": "cliente não reconhecido para este profissional"
        }, status=403)

    duracao_total = sum(service.duracao for service in services)
    horario_fim = horario_inicio + timedelta(minutes=duracao_total)

    if not within_business_hours(profile, horario_inicio, horario_fim):
        return JsonResponse({
            "error": "horário fora do expediente ou em conflito com o almoço"
        }, status=400)

    with transaction.atomic():
        if has_schedule_conflict(
            profile.user,
            horario_inicio,
            horario_fim,
        ):
            return JsonResponse({
                "error": "horário já agendado"
            }, status=409)

        agendamento = Agendamento.objects.create(
            cliente=request.cliente,
            profissional=profile.user,
            horario_inicio=horario_inicio,
            horario_fim=horario_fim
        )
        ItemAgendamento.objects.bulk_create([
            ItemAgendamento(
                agendamento=agendamento,
                servico=service
            )
            for service in services
        ])

    return JsonResponse({
        "message": "horário agendado com sucesso",
        "agendamento": {
            "id": agendamento.id,
            "cliente_id": agendamento.cliente_id,
            "cliente": agendamento.cliente.nome,
            "servicos": [
                {
                    "id": service.id,
                    "nome": service.nome,
                    "duracao": service.duracao,
                    "preco": str(service.preco),
                }
                for service in services
            ],
            "horario_inicio": horario_inicio.isoformat(),
            "horario_fim": horario_fim.isoformat(),
            "status": agendamento.status,
        }
    }, status=201)


def read_profile(request, slug_barber):
    if request.method != "GET":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    # Buscar e validar profile no banco
    try:
        profile = Profile.objects.get(public_slug=slug_barber)
    except Profile.DoesNotExist:
        return JsonResponse({
            "error": "barbearia não encontrada"
        }, status=404)

    services = Servico.objects.filter(
        user=profile.user,
        ativo=True,
    ).order_by("id")

    return JsonResponse({
        "nome": profile.nome_negocio,
        "barbearia": profile.public_slug,
        "telefone": profile.telefone,
        "servicos": [
            {
                "id": service.id,
                "nome": service.nome,
                "preco": str(service.preco),
                "duracao": service.duracao,
                "descricao": service.descricao or "",
                "ativo": service.ativo,
            }
            for service in services
        ],
    })
