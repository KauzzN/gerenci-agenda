from datetime import datetime, timedelta
from django.http import JsonResponse
from public.models import Profile
from django.utils.text import slugify
from django.core.validators import MinLengthValidator, RegexValidator
from agendamento.validators import validar_horario_expediente

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

def atualizar_horario(profile, data):

    updated = False

    inicio_expediente = data.get("horario_inicio")
    fim_expediente = data.get("horario_fim")
    inicio_almoco = data.get("inicio_almoco")
    fim_almoco = data.get("fim_almoco")
    

    horario_inicio, horario_fim, comeco_almoco, final_almoco, erro = validar_horario_expediente(
        inicio_expediente,
        fim_expediente, 
        inicio_almoco, 
        fim_almoco)

    if erro:
        return False, erro

    if horario_inicio is not None:

        if horario_inicio != profile.horario_inicio:
            profile.horario_inicio = horario_inicio
            updated = True

    if horario_fim is not None:

        if horario_fim != profile.horario_fim:
            profile.horario_fim = horario_fim
            updated = True

    if comeco_almoco is not None:

        if comeco_almoco != profile.inicio_almoco:
            profile.inicio_almoco = comeco_almoco
            updated = True

    if final_almoco is not None:

        if final_almoco != profile.fim_almoco:
            profile.fim_almoco = final_almoco
            updated = True

    if updated:
        profile.save()

    return updated, None
    


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

    if "endereco" in data and data["endereco"].strip():

        endereco = data["endereco"].strip()

        if len(endereco) < 5:
            return None, "endereço inválido"

        if endereco != profile.endereco:
            profile.endereco = endereco
            updated = True

    if "instagram" in data and data["instagram"].strip():

        instagram = data["instagram"].strip()

        if instagram != profile.instagram:
            profile.instagram = instagram
            updated = True

    if "descricao" in data and data["descricao"].strip():

        descricao = data["descricao"].strip()

        if len(descricao) > 200:
            return None, "Descrição muito longa"

        if descricao != profile.descricao:

            profile.descricao = descricao
            updated = True
        
    if updated:
        profile.save()
        
    return updated, None