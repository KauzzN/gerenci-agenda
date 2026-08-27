from django.db import models
from django.contrib.auth.models import User
from servicos.models import Servico
from cliente.models import Cliente

# Create your models here.
class Agendamento(models.Model):
    
    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        ATENDIDO = "ATENDIDO", "Atendido"
        CANCELADO = "CANCELADO", "Cancelado"
        FALTOU = "FALTOU", "Faltou"

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="agendamentos"
    )
    
    profissional = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="agendamentos"
    )

    horario_inicio = models.DateTimeField()
    horario_fim = models.DateTimeField()

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDENTE
    )

    

    criado_em = models.DateTimeField(auto_now_add=True)

    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cliente.nome} - {self.horario_inicio}"

class ItemAgendamento(models.Model):

    agendamento = models.ForeignKey(
        Agendamento,
        on_delete=models.CASCADE,
        related_name="itens"
    )

    servico = models.ForeignKey(
        Servico,
        on_delete=models.PROTECT,
        related_name="itens_agendamento"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["agendamento", "servico"],
                name="servico_unico_por_agendamento"
        )
    ]

