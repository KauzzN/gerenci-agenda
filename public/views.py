from datetime import datetime, timedelta
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from agendamento.utils.agendamento_utils import parse_json_body
from agendamento.validators import validar_data, validar_horario
from agendamento.models import Agendamento, ItemAgendamento
from cliente.models import ClienteProfissional
from servicos.models import Servico
from users.decorators import client_required
from .models import Profile
from django.views.decorators.csrf import csrf_exempt


def _parse_service_ids(values):
    raw_values = values
    if (
        len(raw_values) == 1
        and isinstance(raw_values[0], str)
        and "," in raw_values[0]
    ):
        raw_values = raw_values[0].split(",")

    try:
        service_ids = [int(value) for value in raw_values]
    except (TypeError, ValueError):
        return None

    if (
        not service_ids
        or any(service_id <= 0 for service_id in service_ids)
        or len(service_ids) != len(set(service_ids))
    ):
        return None

    return service_ids


def _load_services(profile, service_ids):
    services = list(
        Servico.objects.filter(
            id__in=service_ids,
            user=profile.user,
            ativo=True
        )
    )
    services_by_id = {service.id: service for service in services}
    if len(services) != len(service_ids):
        return None

    return [services_by_id[service_id] for service_id in service_ids]


def _overlaps_lunch(profile, inicio, fim):
    return bool(
        profile.inicio_almoco
        and profile.fim_almoco
        and inicio.time() < profile.fim_almoco
        and fim.time() > profile.inicio_almoco
    )


def _within_business_hours(profile, inicio, fim):
    if profile.horario_inicio is None or profile.horario_fim is None:
        return False

    return (
        inicio.date() == fim.date()
        and inicio.time() >= profile.horario_inicio
        and fim.time() <= profile.horario_fim
        and not _overlaps_lunch(profile, inicio, fim)
    )


def _has_conflict(profile, inicio, fim):
    return Agendamento.objects.filter(
        profissional=profile.user,
        horario_inicio__lt=fim,
        horario_fim__gt=inicio
    ).exclude(
        status=Agendamento.Status.CANCELADO
    ).exists()


@csrf_exempt
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

    service_ids = _parse_service_ids(request.GET.getlist("servicos"))
    if service_ids is None:
        return JsonResponse({
            "error": "servicos deve conter uma lista de IDs válidos"
        }, status=400)

    services = _load_services(profile, service_ids)
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
            and _within_business_hours(profile, horario_atual, horario_fim)
            and not _has_conflict(profile, horario_atual, horario_fim)
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


@csrf_exempt
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
        return JsonResponse({
            "error": error
        }, status=400)

    if not isinstance(data, dict):
        return JsonResponse({
            "error": "json inválido"
        }, status=400)

    service_ids = data.get("servicos")
    if not isinstance(service_ids, list):
        return JsonResponse({
            "error": "servicos deve ser uma lista"
        }, status=400)

    service_ids = _parse_service_ids(service_ids)
    if service_ids is None:
        return JsonResponse({
            "error": "servicos deve conter uma lista de IDs válidos"
        }, status=400)

    services = _load_services(profile, service_ids)
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

    if not _within_business_hours(profile, horario_inicio, horario_fim):
        return JsonResponse({
            "error": "horário fora do expediente ou em conflito com o almoço"
        }, status=400)

    with transaction.atomic():
        Profile.objects.select_for_update().get(pk=profile.pk)
        if _has_conflict(profile, horario_inicio, horario_fim):
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
            "horario_inicio": horario_inicio.isoformat(),
            "horario_fim": horario_fim.isoformat()
        }
    }, status=201)


@csrf_exempt
@client_required
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

    # Retornar profile
    return JsonResponse({
        "nome": profile.nome_negocio,
        "barbearia": profile.public_slug,
        "telefone": profile.telefone
    })
