from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Servico(models.Model):

    nome = models.CharField(max_length=50)

    preco = models.DecimalField(
        decimal_places=2,
        max_digits=8
    )

    duracao = models.PositiveIntegerField()

    descricao = models.CharField(
        max_length=200, 
        blank=True
    )

    ativo = models.BooleanField(
        default=True
    )

    cor = models.CharField(
        max_length=7,
        default="#000000"
    )


    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="serviços"
    )