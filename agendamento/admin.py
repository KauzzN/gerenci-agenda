from django.contrib import admin
from .models import Agendamento, ItemAgendamento


# Register your models here.
@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = (
        "cliente",
        "profissional",
        "horario_inicio",
        "horario_fim",
        "status",
    )

    list_filter = (
        "status",
        "horario_inicio",
    )

    search_fields = (
        "cliente__nome",
        "profissional__username",
    )

    ordering = ("horario_inicio",)

@admin.register(ItemAgendamento)
class ItemAgendamentoAdmin(admin.ModelAdmin):
    list_display = (
        "agendamento",
        "servico",
    )