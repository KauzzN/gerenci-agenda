import json
from django.http import JsonResponse


from .models import Agendamento, ItemAgendamento
from cliente.models import Cliente, ClienteProfissional
from servicos.models import Servico
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.utils  import timezone
from django.db import transaction

# Import validações, utils e services
from users.decorators import jwt_required
from .validators import validar_horario, validar_data_consulta
from .utils.agendamento_utils import parse_json_body
from .services import atualizar_agendamento_vencido

# Create your views here.

@csrf_exempt
@jwt_required
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
        novo_agendamento = {
            "id": agendamento.id,
            "cliente": agendamento.cliente.nome,
            "horario_inicio": agendamento.horario_inicio,
            "horario_fim": agendamento.horario_fim,
            "status": agendamento.status
        }
        
        lista_agendamentos.append(novo_agendamento)
        
    return JsonResponse({
        "historico": lista_agendamentos
    })
    

@csrf_exempt
@jwt_required
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
        proximo_json = {
            "cliente": proximo.cliente.nome,
            "horario_inicio": proximo.horario_inicio,
            "horario_fim": proximo.horario_fim,
            "status": proximo.status,
            "telefone": proximo.cliente.telefone
        }
    
    return JsonResponse({
        "total": total,
        "pendentes": pendentes,
        "atendidos": atendidos,
        "faltaram": faltaram,
        
        "proximo": proximo_json
    })

@csrf_exempt
@jwt_required
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
        }, status=404)
    
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
        novo_horario = {
            "id": agendamento.id,
            "cliente": agendamento.cliente.nome,
            "horario_inicio": agendamento.horario_inicio,
            "horario_fim": agendamento.horario_fim,
            "status": agendamento.status
        }
        
        agenda.append(novo_horario)
        
    return JsonResponse({
        "agendamentos": agenda
    })

@csrf_exempt
@jwt_required
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
        return JsonResponse({
            "detail": erro
        }, status=400)
    

    if "cliente_id" not in data:
        return JsonResponse({
            "detail": "cliente_id é obrigatório."
        }, status=400)

    if "servicos" not in data:
        return JsonResponse({
            "detail": "servicos é obrigatório."
        }, status=400)

    if "horario_inicio" not in data:
        return JsonResponse({
            "detail": "horario_inicio é obrigatório."
        }, status=400)

    id_cliente = data["cliente_id"]
    servicos = data["servicos"]

    if (
        not isinstance(id_cliente, int)
        or isinstance(id_cliente, bool)
        or id_cliente <= 0
    ):
        return JsonResponse({
            "detail": "cliente_id inválido."
        }, status=400)

    if not isinstance(servicos, list) or not servicos:
        return JsonResponse({
            "detail": "servicos deve ser uma lista não vazia."
        }, status=400)

    if any(
        not isinstance(servico, int)
        or isinstance(servico, bool)
        or servico <= 0
        for servico in servicos
    ):
        return JsonResponse({
            "detail": "servicos deve conter apenas IDs válidos."
        }, status=400)

    if len(servicos) != len(set(servicos)):
        return JsonResponse({
            "detail": "Não é permitido repetir serviços."
        }, status=400)

    
    horario_inicio, erro = validar_horario(
        data["horario_inicio"]
    )

    if erro: 
        return JsonResponse({
            "detail": erro
        }, status=400)

    cliente = Cliente.objects.filter(
        id=id_cliente
    ).first()

    if not cliente:

        return JsonResponse({
            "detail": "cliente não encontrado"
        }, status=404)

    profile=user.profile

    relacao = ClienteProfissional.objects.filter(
        cliente=cliente,
        profile=profile
    ).first()

    if not relacao:

        return JsonResponse({
            "detail": "cliente não reconhecido"
        }, status=404)

    lista_servicos = []

    for servico in servicos:

        servico_iterado = Servico.objects.filter(
            id=servico,
            user=user
        ).first()

        if not servico_iterado:

            return JsonResponse({
                "detail": f"Servico '{servico}' não encontrado."
            }, status=400)

        if not servico_iterado.ativo:

            return JsonResponse({
                "detail": f"O serviço '{servico_iterado.nome}' está inativo."
            }, status=400)

        lista_servicos.append(servico_iterado)

    duracao_total = sum(
        servico.duracao
        for servico in lista_servicos
    )

    if duracao_total <= 0:
        return JsonResponse({
            "detail": "A duração total dos serviços deve ser maior que zero."
        }, status=400)

    horario_fim = horario_inicio + timedelta(minutes=duracao_total)

    inicio_expediente = profile.horario_inicio
    fim_expediente = profile.horario_fim

    if inicio_expediente is None or fim_expediente is None:
        return JsonResponse({
            "detail": "expediente não configurado"
        }, status=400)

    if horario_inicio.time() < inicio_expediente:
        return JsonResponse({
            "detail": "O agendamento começa antes do expediente."
        }, status=400)

    if (
        horario_fim.date() != horario_inicio.date()
        or horario_fim.time() > fim_expediente
    ):
        return JsonResponse({
            "detail": "O agendamento termina após o expediente."
        }, status=400)

    if profile.inicio_almoco and profile.fim_almoco:
        if (
            horario_inicio.time() < profile.fim_almoco
            and horario_fim.time() > profile.inicio_almoco
        ):
            return JsonResponse({
                "detail": "O horário escolhido conflita com o horário de almoço."
            }, status=400)

    conflito = Agendamento.objects.filter(
        profissional=user,
        horario_inicio__lt=horario_fim,
        horario_fim__gt=horario_inicio
    ).exists()

    if conflito:
        return JsonResponse({
            "detail": "O horário escolhido já está ocupado."
        }, status=400)

    with transaction.atomic():

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
        "teste_de_response": {
            "id_cliente": id_cliente,
            "cliente": cliente.nome,
            "telefone": relacao.cliente.telefone,
            "public_slug": relacao.profile.public_slug,
            "servicos": [
                {
                    "id": servico.id,
                    "nome": servico.nome,
                    "duracao": servico.duracao,
                    "preco": str(servico.preco),
                }
                for servico in lista_servicos
            ],
            "duracao_total": duracao_total,
            "horario_inicio": horario_inicio.isoformat(),
            "horario_fim": horario_fim.isoformat(),
        }
    }, status=200)


@csrf_exempt
@jwt_required
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

    id_cliente = data.get("cliente_id")
    servicos = data.get("servicos")
    horario_inicio = data.get("horario_inicio")
    status = data.get("status")
    
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

    lista_servicos = []
    for servico in servicos:
        servico_iterado = Servico.objects.filter(
            id=servico,
            user=user,
            ativo=True
        ).first()

        if not servico_iterado:
            return JsonResponse({
                "error": f"Servico '{servico}' não encontrado ou está inativo."
            }, status=400)

        lista_servicos.append(servico_iterado)

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

    if horario_inicio.time() < profile.horario_inicio:
        return JsonResponse({
            "error": "O agendamento começa antes do expediente."
        }, status=400)

    if (
        horario_fim.date() != horario_inicio.date()
        or horario_fim.time() > profile.horario_fim
    ):
        return JsonResponse({
            "error": "O agendamento termina após o expediente."
        }, status=400)

    if profile.inicio_almoco and profile.fim_almoco:
        if (
            horario_inicio.time() < profile.fim_almoco
            and horario_fim.time() > profile.inicio_almoco
        ):
            return JsonResponse({
                "error": "O horário escolhido conflita com o horário de almoço."
            }, status=400)

    status_validos = [choice.value for choice in Agendamento.Status]
    if status not in status_validos:
        return JsonResponse({
            "error": "status inválido"
        }, status=400)

    conflito = Agendamento.objects.filter(
        profissional=user,
        horario_inicio__lt=horario_fim,
        horario_fim__gt=horario_inicio
    ).exclude(
        id=agendamento.id
    ).exists()

    if conflito:
        return JsonResponse({
            "error": "já existe um agendamento nesse horário"
        }, status=400)
        
    agendamento.cliente = cliente
    agendamento.horario_inicio = horario_inicio
    agendamento.horario_fim = horario_fim
    agendamento.status = status
    
    with transaction.atomic():
        agendamento.save()
        agendamento.itens.all().delete()
        ItemAgendamento.objects.bulk_create([
            ItemAgendamento(agendamento=agendamento, servico=servico)
            for servico in lista_servicos
        ])
    
    return JsonResponse({
        "message": "agendamento atualizado com sucesso"
    }, status=200)
    
    
@csrf_exempt
@jwt_required
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
    
    agendamento.delete()
    
    return JsonResponse({
        "message": "agendamento cancelado com sucesso!"
    }, status=200)
    
    
@csrf_exempt
@jwt_required
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
        return JsonResponse({
            "erro:": error
        })
    
    
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
        
    
        
    agendamento.status = status_inserido
    
    agendamento.save(update_fields=["status"])
    
    return JsonResponse({
        "message": "status alterado com sucesso",
        "status": agendamento.status
    }, status=200)