from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Agendamento(models.Model):
    nome = models.CharField(max_length=100)
    atendido = models.BooleanField(default=False)
    horario = models.DateTimeField()
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True
    )

    def __str__(self):
        return f"{self.nome} - {self.horario}"


