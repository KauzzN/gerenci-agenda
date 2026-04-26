from django.shortcuts import render, redirect
from .models import Agendamento
from .forms import AgendamentoForm

# Create your views here.
def lista_agendamentos(request):
    agendamentos = Agendamento.objects.all().order_by('atendido', 'horario')

    return render(request, 'lista.html', {
        'agendamentos': agendamentos
    })

def criar_agendamento(request):
    form = AgendamentoForm(request.POST or None)

    if form.is_valid():
        horario = form.cleaned_data['horario']

        conflito = Agendamento.objects.filter(horario=horario).exists()

        if conflito:
            form.add_error('horario', 'Ja existe agendamento nesse horário')
        
        else:
            form.save()
            return redirect('lista')

    return render(request, 'form.html', {
    'form': form
})

def editar_agendamento(request, id):
    agendamento = Agendamento.objects.get(id=id)
    form = AgendamentoForm(request.POST or None, instance=agendamento)

    if form.is_valid():
        horario = form.cleaned_data['horario']

        conflito = Agendamento.objects.filter(horario=horario).exclude(id=id).exists()

        if conflito:
            form.add_error('horario', 'Já existe agendamento nesse horário')
        
        else:
            form.save()
            return redirect('lista')

    return render(request, 'form.html', {'form': form})


def excluir_agendamento(request, id):
    agendamento = Agendamento.objects.get(id=id)
    agendamento.delete()
    return redirect('lista')

def marcar_atendido(request,id):
    agendamento = Agendamento.objects.get(id=id)
    agendamento.atendido = not agendamento.atendido
    agendamento.save()
    return redirect('lista')


