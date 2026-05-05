from django import forms
from django.utils import timezone
from .models import Agendamento



class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['nome', 'horario']
        widgets = {
            'horario': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'step': '1800'
            })
        }

    def clean_horario(self):
        horario = self.cleaned_data.get('horario')

        if horario:
            if timezone.is_naive(horario):
                horario = timezone.make_aware(horario, timezone.get_current_timezone())

            if horario < timezone.localtime():
                raise forms.ValidationError('Não pode agendar no passado.')

            if horario.minute not in [0, 30]:
                raise forms.ValidationError('Escolha horários de 30 em 30 minutos (ex: 14:00, 14:30)')

            conflito = Agendamento.objects.filter(horario=horario)

            if self.instance.pk:
                conflito = conflito.exclude(pk=self.instance.pk)

            if conflito.exists():
                raise forms.ValidationError('Já existe um agendamento nesse horário.')

        return horario
