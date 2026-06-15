import json
from django.http import JsonResponse


from .models import Agendamento
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.utils  import timezone

#Validações importadas
from users.decorators import jwt_required
from .validators import validar_horario
from .utils.agendamento_utils import parse_json_body

# Create your views here.

@csrf_exempt
@jwt_required
def listar_agendamentos(request):
    if request.method != "GET":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)
        
    user = request.user
    
    agendamentos = Agendamento.objects.filter(user=user).order_by("horario")
    
    agenda = []
    
    for agendamento in agendamentos:
        novo_horario = {
            "id": agendamento.id,
            "nome": agendamento.nome,
            "horario": agendamento.horario,
            "atendido": agendamento.atendido
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
    
    if not nome or not horario:
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
    
    agendamento.save()
    
    return JsonResponse({
        "message": "agendamento atualizado com sucesso"
    }, status=200)
    


