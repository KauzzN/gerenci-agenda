from datetime import datetime, timedelta
from public.models import Profile

def gerar_horarios_do_dia():
    
    horarios = []
    
    horario_atual = datetime.strptime(
        "08:00",
        "%H:%M"
    )
    
    horario_final = datetime.strptime(
        "18:00",
        "%H:%M"
    )
    
    while horario_atual <= horario_final:
        
        horarios.append(
            horario_atual.strftime("%H:%M")
        )
        
        horario_atual += timedelta(minutes=30)
        
    return horarios

def atualizar_profile(profile, data):
    
    updated = False
    
    if "public_slug" in data and data["public_slug"].strip():
        conflito = Profile.objects.filter(public_slug=data["public_slug"])
        
        if conflito:
            return None, "este slug já existe"
        
        profile.public_slug = data["public_slug"]
        updated = True
        
    if "nome_negocio" in data and data["nome_negocio"].strip():
        profile.nome_negocio = data["nome_negocio"]
        updated = True
        
    if "telefone" in data and data["telefone"].strip():
        profile.telefone = data["telefone"] or ""
        updated = True
        
    if updated:
        profile.save()
        
    return updated