from django.db import models
from django.contrib.auth.models import User
from public.models import Profile

# Create your models here.
class Cliente(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cliente"
    )

    nome = models.CharField(max_length=100)

    telefone = models.CharField(
        max_length=20,
        unique=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)

class ClienteProfissional(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="relacoes_profissionais"
    )

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="relacoes_clientes"
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    ativo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cliente", "profile"],
                name="cliente_profissional_unico"
            )
        ]