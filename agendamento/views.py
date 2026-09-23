import json
from django.http import JsonResponse


from .models import Agendamento, ItemAgendamento
from cliente.models import Cliente, ClienteProfissional
from servicos.models import Servico
from datetime import datetime, timedelta
from django.utils  import timezone
from django.db import transaction

# Import validações, utils e services
from users.decorators import professional_required
from .validators import validar_horario, validar_data_consulta
from .utils.agendamento_utils import parse_json_body
from .services import atualizar_agendamento_vencido
from .booking_rules import (
    has_schedule_conflict,
    load_active_services,
    within_business_hours,
)

def _serialize_agendamento(agendamento):
    return {
        "id": agendamento.id,
        "cliente_id": agendamento.cliente_id,
        "cliente": agendamento.cliente.nome,
        "servicos": [
            {
                "id": item.servico_id,
                "nome": item.servico.nome,
                "duracao": item.servico.duracao,
                "preco": str(item.servico.preco),
            }
            for item in agendamento.itens.select_related("servico").all()
        ],
        "horario_inicio": agendamento.horario_inicio.isoformat(),
        "horario_fim": agendamento.horario_fim.isoformat(),
        "status": agendamento.status,
    }

# Create your views here.

@professional_required
def historico_view(request):
    if request.method != "GET":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    user = request.user

    agendamentos = Agendamento.objects.filter(
        profissional=user
    ).exclude(
        status=Agendamento.Status.PENDENTE
    ).order_by("-horario_inicio")
    
    lista_agendamentos = []
    
    for agendamento in agendamentos:
        lista_agendamentos.append(_serialize_agendamento(agendamento))
        
    return JsonResponse({
        "historico": lista_agendamentos
    })
    

@professional_required
def dashboard_view(request):
    if request.method != "GET":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    user = request.user
    
    atualizar_agendamento_vencido(user)
        
    hoje = timezone.localdate()
    

    agendamentos_hoje = Agendamento.objects.filter(
        profissional=user,
        horario_inicio__date=hoje
    ).exclude(
        status=Agendamento.Status.CANCELADO
    )
    
    
    total = agendamentos_hoje.count()
    
    pendentes = agendamentos_hoje.filter(
        status=Agendamento.Status.PENDENTE
    ).count()
    
    atendidos = agendamentos_hoje.filter(
        status=Agendamento.Status.ATENDIDO
    ).count()
    
    faltaram = agendamentos_hoje.filter(
        status=Agendamento.Status.FALTOU
    ).count()
    
    proximo_json = None
    
    proximo = agendamentos_hoje.filter(
        status=Agendamento.Status.PENDENTE,
        horario_inicio__gte=timezone.now()
    ).order_by("horario_inicio").first()
    
    if proximo:
        proximo_json = _serialize_agendamento(proximo)
        proximo_json["telefone"] = proximo.cliente.telefone
    
    return JsonResponse({
        "total": total,
        "pendentes": pendentes,
        "atendidos": atendidos,
        "faltaram": faltaram,
        
        "proximo": proximo_json
    })

@professional_required
def listar_agendamentos(request):
    if request.method != "GET":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)
        
    user = request.user
    
    data_str = request.GET.get("data")
    
    if not data_str:
        data = timezone.localdate()
    
    else:
        
        data, error =  validar_data_consulta(data_str)
        
        if error:
            return JsonResponse({
                "error": error
        }, status=400)
    
    atualizar_agendamento_vencido(user)
    
    agendamentos = Agendamento.objects.filter(
        profissional=user,
        horario_inicio__date=data,
        status__in=[
            Agendamento.Status.PENDENTE,
            Agendamento.Status.ATENDIDO,
            Agendamento.Status.FALTOU
        ]
    ).order_by("horario_inicio")
    
    agenda = []
    
    for agendamento in agendamentos:
        agenda.append(_serialize_agendamento(agendamento))
        
    return JsonResponse({
        "agendamentos": agenda
    })

@professional_required
def criar_agendamento(request):

    # Retorno esperado
    #{
    #   "cliente_id": 12,
    #   "servicos": [2, 5],
    #   "horario_inicio": "2026-08-27T14:00:00",
    #}

    if request.method != "POST":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    user = request.user

    data, erro = parse_json_body(request)

    if erro:
        return erro

    if not isinstance(data, dict):
        return JsonResponse({
            "error": "json inválido"
        }, status=400)

    if "cliente_id" not in data:
        return JsonResponse({
            "error": "cliente_id é obrigatório."
        }, status=400)

    if "servicos" not in data:
        return JsonResponse({
            "error": "servicos é obrigatório."
        }, status=400)

    if "horario_inicio" not in data:
        return JsonResponse({
            "error": "horario_inicio é obrigatório."
        }, status=400)

    id_cliente = data["cliente_id"]
    servicos = data["servicos"]

    if (
        not isinstance(id_cliente, int)
        or isinstance(id_cliente, bool)
        or id_cliente <= 0
    ):
        return JsonResponse({
            "error": "cliente_id inválido."
        }, status=400)

    if not isinstance(servicos, list) or not servicos:
        return JsonResponse({
            "error": "servicos deve ser uma lista não vazia."
        }, status=400)

    if any(
        not isinstance(servico, int)
        or isinstance(servico, bool)
        or servico <= 0
        for servico in servicos
    ):
        return JsonResponse({
            "error": "servicos deve conter apenas IDs válidos."
        }, status=400)

    if len(servicos) != len(set(servicos)):
        return JsonResponse({
            "error": "Não é permitido repetir serviços."
        }, status=400)

    
    horario_inicio, erro = validar_horario(
        data["horario_inicio"]
    )

    if erro: 
        return JsonResponse({
            "error": erro
        }, status=400)

    cliente = Cliente.objects.filter(
        id=id_cliente
    ).first()

    if not cliente:
        return JsonResponse({
            "error": "cliente não encontrado"
        }, status=404)

    profile=user.profile

    relacao = ClienteProfissional.objects.filter(
        cliente=cliente,
        profile=profile
    ).first()

    if not relacao:
        return JsonResponse({
            "error": "cliente não reconhecido"
        }, status=404)

    if not relacao.ativo:
        return JsonResponse({
            "error": "cliente não está ativo para este profissional"
        }, status=403)

    lista_servicos = load_active_services(user, servicos)
    if lista_servicos is None:
        return JsonResponse({
            "error": "serviço não encontrado ou está inativo"
        }, status=400)

    duracao_total = sum(
        servico.duracao
        for servico in lista_servicos
    )

    if duracao_total <= 0:
        return JsonResponse({
            "error": "A duração total dos serviços deve ser maior que zero."
        }, status=400)

    horario_fim = horario_inicio + timedelta(minutes=duracao_total)

    inicio_expediente = profile.horario_inicio
    fim_expediente = profile.horario_fim

    if inicio_expediente is None or fim_expediente is None:
        return JsonResponse({
            "error": "expediente não configurado"
        }, status=400)

    if not within_business_hours(profile, horario_inicio, horario_fim):
        return JsonResponse({
            "error": "horário fora do expediente ou em conflito com o almoço"
        }, status=400)

    with transaction.atomic():
        if has_schedule_conflict(user, horario_inicio, horario_fim):
            return JsonResponse({
                "error": "O horário escolhido já está ocupado."
            }, status=409)

        agendamento = Agendamento.objects.create(
            profissional=user,
            cliente=cliente,
            horario_inicio=horario_inicio,
            horario_fim=horario_fim,
        )

        for servico in lista_servicos:
            ItemAgendamento.objects.create(
                agendamento=agendamento,
                servico=servico
            )


    return JsonResponse({
        "message": "Agendamento criado com sucesso",
        "agendamento": _serialize_agendamento(agendamento),
    }, status=201)


@professional_required
def update_agendamentos(request, id_agend):
    if request.method != "PUT":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    user = request.user

    try:
        agendamento = Agendamento.objects.get(
            id=id_agend,
            profissional=user
        )

    except Agendamento.DoesNotExist:
        return JsonResponse({
            "error": "agendamento não encontrado"
        }, status=404)
        
    data, erro = parse_json_body(request)
    
    if erro:
        return JsonResponse({
            "error": erro
        }, status=400)

    if not isinstance(data, dict):
        return JsonResponse({
            "error": "json inválido"
        }, status=400)

    id_cliente = data.get("cliente_id")
    servicos = data.get("servicos")
    horario_inicio = data.get("horario_inicio")
    status = data.get("status").upper()
    
    if (
        not isinstance(id_cliente, int)
        or isinstance(id_cliente, bool)
        or id_cliente <= 0
        or not isinstance(servicos, list)
        or not servicos
        or not horario_inicio
        or not isinstance(status, str)
        or not status
    ):
        return JsonResponse({
            "error": "cliente_id, servicos, horario_inicio e status são necessários"
        }, status=400)

    if any(
        not isinstance(servico, int)
        or isinstance(servico, bool)
        or servico <= 0
        for servico in servicos
    ):
        return JsonResponse({
            "error": "servicos deve conter apenas IDs válidos."
        }, status=400)

    if len(servicos) != len(set(servicos)):
        return JsonResponse({
            "error": "Não é permitido repetir serviços."
        }, status=400)

    horario_inicio, erro = validar_horario(horario_inicio)
    
    if erro:
        return JsonResponse({
            "error": erro
        }, status=400)
        
    cliente = Cliente.objects.filter(id=id_cliente).first()

    if not cliente:
        return JsonResponse({
            "error": "cliente não encontrado"
        }, status=404)

    profile = user.profile

    relacao = ClienteProfissional.objects.filter(
        cliente=cliente,
        profile=profile
    ).first()

    if not relacao:
        return JsonResponse({
            "error": "cliente não reconhecido"
        }, status=404)

    if not relacao.ativo:
        return JsonResponse({
            "error": "cliente não está ativo para este profissional"
        }, status=403)

    lista_servicos = load_active_services(user, servicos)
    if lista_servicos is None:
        return JsonResponse({
            "error": "serviço não encontrado ou está inativo"
        }, status=400)

    duracao_total = sum(servico.duracao for servico in lista_servicos)

    if duracao_total <= 0:
        return JsonResponse({
            "error": "A duração total dos serviços deve ser maior que zero."
        }, status=400)

    horario_fim = horario_inicio + timedelta(minutes=duracao_total)

    if (
        profile.horario_inicio is None
        or profile.horario_fim is None
    ):
        return JsonResponse({
            "error": "expediente não configurado"
        }, status=400)

    if not within_business_hours(profile, horario_inicio, horario_fim):
        return JsonResponse({
            "error": "horário fora do expediente ou em conflito com o almoço"
        }, status=400)

    status_validos = [choice.value for choice in Agendamento.Status]
    if status not in status_validos:
        return JsonResponse({
            "error": "status inválido"
        }, status=400)

    if not agendamento.can_transition_to(status):
        return JsonResponse({
            "error": "transição de status inválida para esse agendamento"
        }, status=400)

    with transaction.atomic():
        if has_schedule_conflict(
            user,
            horario_inicio,
            horario_fim,
            exclude_id=agendamento.id,
        ):
            return JsonResponse({
                "error": "já existe um agendamento nesse horário"
            }, status=400)

        agendamento.cliente = cliente
        agendamento.horario_inicio = horario_inicio
        agendamento.horario_fim = horario_fim
        agendamento.status = status
        agendamento.save()
        agendamento.itens.all().delete()
        ItemAgendamento.objects.bulk_create([
            ItemAgendamento(agendamento=agendamento, servico=servico)
            for servico in lista_servicos
        ])
    
    return JsonResponse({
        "message": "agendamento atualizado com sucesso",
        "agendamento": _serialize_agendamento(agendamento),
    }, status=200)
    
    
@professional_required
def delete_agendamento(request, id_agend):

    if request.method != "DELETE":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    user = request.user
    
    try:
        agendamento = Agendamento.objects.get(
            id=id_agend,
            profissional=user
        )

    except Agendamento.DoesNotExist:
        return JsonResponse({
            "error": "agendamento não encontrado"
        }, status=404)

    if agendamento.status == agendamento.Status.CANCELADO:
        return JsonResponse({
            "error": "agendamento já está cancelado"
        }, status=400)
    
    agendamento.status =  Agendamento.Status.CANCELADO
    agendamento.save(update_fields=["status", "atualizado_em"])
    
    return JsonResponse({
        "message": "agendamento cancelado com sucesso!",
        "status": agendamento.status
    }, status=200)
    
    
@professional_required
def atualizar_status(request, id_agend):
    
    if request.method != "PATCH": 
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    status_validos = [
        Agendamento.Status.PENDENTE,
        Agendamento.Status.CANCELADO,
        Agendamento.Status.ATENDIDO,
        Agendamento.Status.FALTOU
    ]
    
    user = request.user

    data, error = parse_json_body(request)
    
    if error:
        return error
    
    
    status_inserido = data.get("status")

    if not isinstance(status_inserido, str):
        return JsonResponse({
            "error": "status inválido"
        }, status=400)

    status_inserido = status_inserido.upper()
    
    if status_inserido not in status_validos:
        return JsonResponse({
            "error": "status inválido"
        }, status=400)

    
    try:
        agendamento = Agendamento.objects.get(
            id=id_agend,
            profissional=user
        )

    except Agendamento.DoesNotExist:
        return JsonResponse({
            "error": "agendamento não encontrado"
        }, status=404)

    if not agendamento.can_transition_to(status_inserido):
        return JsonResponse({
            "error": "transição de status inválida para esse agendamento"
        }, status=400)
    
    agendamento.status = status_inserido
    
    agendamento.save(update_fields=["status", "atualizado_em"])
    
    return JsonResponse({
        "message": "status alterado com sucesso",
        "status": agendamento.status
    }, status=200)