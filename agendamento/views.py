import json
from django.http import JsonResponse


from .models import Agendamento
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.utils  import timezone

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
        user=user
    ).exclude(
        status=Agendamento.Status.PENDENTE
    ).order_by("-horario")
    
    lista_agendamentos = []
    
    for agendamento in agendamentos:
        novo_agendamento = {
            "id": agendamento.id,
            "nome": agendamento.nome,
            "horario": agendamento.horario,
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
        user=user,
        horario__date=hoje
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
        horario__gte=timezone.now()
    ).order_by("horario").first()
    
    if proximo:
        proximo_json = {
            "nome": proximo.nome,
            "horario": proximo.horario,
            "status": proximo.status,
            "telefone": proximo.telefone
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
        user=user,
        horario__date=data,
        status__in=[
            Agendamento.Status.PENDENTE,
            Agendamento.Status.ATENDIDO,
            Agendamento.Status.FALTOU
        ]
    ).order_by("horario")
    
    agenda = []
    
    for agendamento in agendamentos:
        novo_horario = {
            "id": agendamento.id,
            "nome": agendamento.nome,
            "horario": agendamento.horario,
            "status": agendamento.status
        }
        
        agenda.append(novo_horario)
        
    return JsonResponse({
        "agendamentos": agenda
    })

@csrf_exempt
@jwt_required
def criar_agendamento(request):
    
    if request.method != "POST":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)
    
    user = request.user
        
    data, erro = parse_json_body(request)
    
    if erro:
        return JsonResponse({
            "error": erro
        }, status=400)

    
    nome =  data.get("nome")
    horario = data.get("horario")
    
    if not horario or not nome:
        return JsonResponse({
            "error": "nome e horario são obrigatórios"
        }, status=400)
    
    horario, erro = validar_horario(horario)
    
    if erro:
        return JsonResponse({
            "error": erro
        }, status=400)
        
    conflito = Agendamento.objects.filter(
        user=request.user,
        horario=horario
    ).exists()
    
    if conflito:
        return JsonResponse({
            "error": "já existe agendamento nesse horario"
        }, status=400)
        
    agendamento = Agendamento.objects.create(
        user=user,
        nome=nome,
        horario=horario
    )
    
    return JsonResponse({
        "message": "agendamento criado com sucesso",
        "id": agendamento.id
    }, status=201)


@csrf_exempt
@jwt_required
def update_agendamentos(request, id_agend):
    if request.method != "PUT":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)
        
    user = request.user
    
    try:
        agendamento = Agendamento.objects.get(id=id_agend,user=user)

    except Agendamento.DoesNotExist:
        return JsonResponse({
            "error": "agendamento não encontrado"
        }, status=404)
        
    data, erro = parse_json_body(request)
    
    if erro:
        return JsonResponse({
            "error": erro
        }, status=400)

    nome = data.get("nome")
    horario = data.get("horario")
    status = data.get("status")
    
    if not nome or not horario or not status:
        return JsonResponse({
            "error": "nome e horário são necessarios"
        }, status=400)
        
    horario, erro = validar_horario(horario)
    
    if erro:
        return JsonResponse({
            "error": erro
        }, status=400)
        
    conflito = Agendamento.objects.filter(user=user,horario=horario).exclude(
        id=agendamento.id
    ).exists()

    if conflito:
        return JsonResponse({
            "error": "já existe um agendamento nesse horário"
        }, status=400)
        
    agendamento.nome = nome
    agendamento.horario = horario
    agendamento.status = status
    
    agendamento.save()
    
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
        agendamento = Agendamento.objects.get(id=id_agend, user=user)
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
    
    
    status_inserido = data.get("status").upper()
    
    if status_inserido not in status_validos:
        return JsonResponse({
            "error": "status inválido"
        }, status=400)

    
    try:
        agendamento = Agendamento.objects.get(id=id_agend, user=user)

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