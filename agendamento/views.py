import json


from .models import Agendamento
from .forms import AgendamentoForm
from django.http import JsonResponse
from users.decorators import jwt_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .utils.agendamento_utils import parse_json_body
from datetime import datetime
from django.utils  import timezone

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
    
    if user is None:
        return JsonResponse({
            "error": "usuário inválido"
        }, status=401)
        
    data, error = parse_json_body(request)
    
    if error:
        return error
    
    
    nome =  data.get("nome")
    horario = data.get("horario")
    
    if not horario or not nome:
        return JsonResponse({
            "error": "nome e horario são obrigatórios"
        }, status=400)
    
    try:
        horario = datetime.fromisoformat(horario)
        
    except ValueError:
        return JsonResponse({
            "error": "formato de horário inválido"
        }, status=400)
        
        
    if timezone.is_naive(horario):
        horario = timezone.make_aware(
            horario,
            timezone.get_current_timezone()
        )
        
        
    if horario < timezone.now():
        return JsonResponse({
            "error": "não é possivel agendar no passado"
        }, status=400)
        
    if horario.minute not in [0, 30]:
        return JsonResponse({
            "error": "horário deve ser de 30 em 30 minutos"
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
        agendamento = Agendamento.objects.get(
            id=id_agend,
            user=user
        )

    except Agendamento.DoesNotExist:
        return JsonResponse({
            "error": "agendamento não encontrado"
        }, status=404)
        
    data, error = parse_json_body(request)
    
    if error:
        return error

    nome = data.get("nome")
    horario = data.get("horario")
    
    if not nome or not horario:
        return JsonResponse({
            "error": "nome e horário são necessarios"
        }, status=400)
        
    try:
        horario = datetime.fromisoformat(horario)
        
    except ValueError:
        return JsonResponse({
            "error": "formato de horário inválido"
        }, status=400)
        
    if timezone.is_naive(horario):
        horario = timezone.make_aware(
            horario,
            timezone.get_current_timezone()
        )
    
    if horario < timezone.now():
        return JsonResponse({
            "error": "não é possivel agendar no passado"
        }, status=400)
        
    if horario.minute not in [0, 30]:
        return JsonResponse({
            "error": "horário deve ser de 30 em 30 minutos"
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
    
    
        
        


def excluir_agendamento(request, id):
    agendamento = Agendamento.objects.get(id=id)
    agendamento.delete()
    return redirect('lista')

def marcar_atendido(request,id):
    agendamento = Agendamento.objects.get(id=id)
    agendamento.atendido = not agendamento.atendido
    agendamento.save()
    return redirect('lista')


