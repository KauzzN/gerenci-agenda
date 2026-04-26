from django.db import models

# Create your models here.
class Agendamento(models.Model):
    nome = models.CharField(max_length=100)
    atendido = models.BooleanField(default=False)
    horario = models.DateTimeField()

    def __str__(self):
        return f"{self.nome} - {self.horario}"


