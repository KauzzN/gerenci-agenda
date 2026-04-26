from django import forms
from .models import Agendamento

class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['nome', 'horario']
        widgets = {
            'horario': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }
