import json
from django.http import JsonResponse
from datetime import datetime
from django.utils import timezone


def validar_horario(horario):
    
    try:
        horario = datetime.fromisoformat(horario)
        
    except ValueError:
        return None, "formato de horário inválido"
        
    if timezone.is_naive(horario):
        horario = timezone.make_aware(
            horario,
            timezone.get_current_timezone()
        )
        
    if horario < timezone.now():
        return None, "não pode agendar no passado"
        
    if horario.minute not in [0, 30]:
        return None, "horário deve ser de 30 em 30 minutos"
        
    return horario, None