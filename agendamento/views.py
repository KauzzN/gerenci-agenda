import json

from .models import Agendamento
from .forms import AgendamentoForm
from django.http import JsonResponse
from users.decorators import jwt_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .utils.agendamento_utils import parse_json_body
from datetime import timezone, datetime

# Create your views here.

@csrf_exempt
@jwt_required
def lista_agendamentos(request):
    
    user = request.user
    
    agendamentos = Agendamento.objects.all(user_id=user).order_by('atendido', 'horario')

    return render(request, 'lista.html', {
        'agendamentos': agendamentos
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


def editar_agendamento(request, id):
    agendamento = Agendamento.objects.get(id=id)
    form = AgendamentoForm(request.POST or None, instance=agendamento)

    if form.is_valid():
        horario = form.cleaned_data['horario']

        conflito = Agendamento.objects.filter(horario=horario).exclude(id=id).exists()

        if conflito:
            form.add_error('horario', 'Já existe agendamento nesse horário')
        
        else:
            form.save()
            return redirect('lista')

    return render(request, 'form.html', {'form': form})


def excluir_agendamento(request, id):
    agendamento = Agendamento.objects.get(id=id)
    agendamento.delete()
    return redirect('lista')

def marcar_atendido(request,id):
    agendamento = Agendamento.objects.get(id=id)
    agendamento.atendido = not agendamento.atendido
    agendamento.save()
    return redirect('lista')


