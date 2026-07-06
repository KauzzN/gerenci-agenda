from agendamento.models import Agendamento
from django.utils import timezone
from datetime import timedelta

def atualizar_agendamento_vencido(user):
    
    limite = timezone.now() - timedelta(minutes=15)
    
    try:
        agendamentos = Agendamento.objects.filter(
            user=user,
            status=Agendamento.Status.PENDENTE,
            horario__lt=limite    
        ).update(status=Agendamento.Status.FALTOU)
    
    except Agendamento.DoesNotExist:
        return None, "nenhum agendamento encontrado"
    