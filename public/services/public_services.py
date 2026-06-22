from datetime import datetime, timedelta
from public.models import Profile
from django.utils.text import slugify
from django.core.validators import MinLengthValidator, RegexValidator

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
        
        slug = data["public_slug"].strip().lower()
        
        novo_slug = slugify(slug)
        
        
        conflito = Profile.objects.filter(
            public_slug=novo_slug
        ).exclude(
            id=profile.id
        ).exists()
        
        if conflito:
            return None, "esse slug já existe"
        
        if novo_slug != profile.public_slug:    
            profile.public_slug = novo_slug
            updated = True
        
    if "nome_negocio" in data and data["nome_negocio"].strip():
        
        nome_negocio = data["nome_negocio"].strip()
        
        if not nome_negocio:
            return None, "nome é obrigatorio"
        
        if len(nome_negocio) < 3:
            return None, "nome deve ter mais de 3 caracteres"
        
        if nome_negocio != profile.nome_negocio:
            profile.nome_negocio = data["nome_negocio"]
            updated = True
        
    if "telefone" in data and data["telefone"].strip():
        
        telefone = data["telefone"]
        
        telefone = (
            telefone
            .replace("(", "")
            .replace(")", "")
            .replace("-", "")
            .replace(" ", "")
        )
        
        if not telefone.isdigit():
            return None, "o telefone deve conter apenás números"
        
        if len(telefone) not in [10, 11]:
            return None, "formato de telefone inválido"
        
        if telefone != profile.telefone:
            profile.telefone = telefone
            updated = True
        
    if updated:
        profile.save()
        
    return updated, None