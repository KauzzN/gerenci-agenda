import json
from datetime import date

from django.http import JsonResponse
from  django.utils import timezone
from agendamento.utils.agendamento_utils import parse_json_body
from agendamento.validators import validar_data, validar_horario
from agendamento.models import Agendamento
from .models import Profile
from .services.public_services import gerar_horarios_do_dia, atualizar_profile
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
@csrf_exempt
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
        
    todos_horarios = gerar_horarios_do_dia()
    
    agendamentos = Agendamento.objects.filter(
        user=profile.user,
        horario__date=data_formatada
    )
    
    horarios_ocupados = set()
    
    for agendamento in agendamentos:
        
        horario_local = timezone.localtime(
            agendamento.horario
        )
        
        horario_formatado = horario_local.strftime(
            "%H:%M"
        )
        
        horarios_ocupados.add(
            horario_formatado
        )
        
    horarios_livres = []
    
    for horario in todos_horarios:
        
        if horario not in horarios_ocupados:
            
            horarios_livres.append({
                "horario": horario
            })
    
    return JsonResponse({
        "barbearia": profile.nome_negocio,
        "slug": profile.public_slug,
        "data": str(data_formatada),
        "horarios": horarios_livres
    }, status=200)
    
@csrf_exempt
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
    
    # Receber nome e horario
    data, error = parse_json_body(request)
    
    if error:
        return JsonResponse({
            "error": error
        }, status=400)
        
    nome = data.get("nome")
    
    if not nome:
        return JsonResponse({
            "error": "nome não inserido"
        }, status=400)
    
    # Valida horario
    horario = data.get("horario")

    if not horario:
        return JsonResponse({
            "error": "horário não inserido"
        }, status=400)
        
    horario_formatado, error = validar_horario(horario)
    
    if error:
        return JsonResponse({
            "error": error
        }, status=400)
    
    # Validar duplicidade
    conflito = Agendamento.objects.filter(
        horario=horario_formatado,
        user=profile.user
    ).exists()
    
    if conflito:
        return JsonResponse({
            "error": "horario já agendado"
        }, status=400)
    
    # Cria agendamento
    agendamento = Agendamento.objects.create(
        horario=horario_formatado,
        user=profile.user,
        nome=nome
    )
    
    # Retorna sucesso
    return JsonResponse({
        "message": "horario agendado com sucesso"
    }, status=201)
    
@csrf_exempt
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
        "barberaria": profile.public_slug,
        "telefone": profile.telefone
    })
    