import json
from django.http import JsonResponse
from datetime import datetime, date, time
from django.utils import timezone


def validar_horario(horario):
    
    try:
        horario = datetime.fromisoformat(horario)
        
    except (TypeError, ValueError):
        return None, "formato de horário inválido"
        
    if timezone.is_naive(horario):
        horario = timezone.make_aware(
            horario,
            timezone.get_current_timezone()
        )
        
    if horario < timezone.now():
        return None, "não pode agendar no passado"
        
    return horario, None

def validar_data(data_str):
    
    if not data_str:
        return None, "data não informada"
    
    try:
        data = date.fromisoformat(data_str)
        
    except (TypeError, ValueError):
        return None, "formato de data inválido"
    
    if data < timezone.localdate():
        return None, "não é possivel consultar datas passadas"
    
    return data, None

def validar_data_consulta(data_str):
    
    if not data_str:
        return None, "data não informada"
    
    try:
        data = date.fromisoformat(data_str)
        
    except (TypeError, ValueError):
        return None, "formato de data inválido"
    
    return data, None

def validar_horario_expediente(inicio_expediente, fim_expediente, inicio_almoco=None, fim_almoco=None):

    try:
        horario_inicio = _parse_horario_expediente(inicio_expediente)
        horario_fim = _parse_horario_expediente(fim_expediente)

    except (TypeError, ValueError):
        return None,None,None,None, "horário inválido"
        
    if horario_inicio >= horario_fim:
        return None,None,None,None, "horário de fim deve ser posterior ao horário de início"

    if inicio_almoco is None and fim_almoco is None:
        return horario_inicio, horario_fim, None, None, None

    if inicio_almoco is None or fim_almoco is None:
        return None,None,None,None, "informe o início e o fim de almoço"


    try:
        comeco_almoco = _parse_horario_expediente(inicio_almoco)
        final_almoco = _parse_horario_expediente(fim_almoco)

    except (TypeError, ValueError):
        return None,None,None,None, "horário inválido"

    if final_almoco <= comeco_almoco:
        return None,None,None,None, "horário de fim do almoço deve ser posterior ao horário de inicio"

    if comeco_almoco < horario_inicio or final_almoco > horario_fim:
        return None,None,None,None, "horário de almoço deve estar dentro do expediente"

    return horario_inicio, horario_fim, comeco_almoco, final_almoco, None


def _parse_horario_expediente(value):
    if isinstance(value, time):
        return value

    if not isinstance(value, str):
        raise TypeError

    return datetime.strptime(value, "%H:%M").time()