from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    nome_negocio = models.CharField(max_length=100, blank=True)

    telefone = models.CharField(max_length=15, blank=True)
    endereco = models.CharField(max_length=100, blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    descricao = models.CharField(max_length=200, blank=True)

    horario_inicio = models.TimeField(null=True, blank=True)
    horario_fim = models.TimeField(null=True, blank=True)

    inicio_almoco = models.TimeField(blank=True, null=True)
    fim_almoco = models.TimeField(blank=True, null=True)

    dias_funcionando = models.JSONField(default=list)

    public_slug = models.SlugField(
        unique=True,
        max_length=100,
        blank=True,
        null=True
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name="profile")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)