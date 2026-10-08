from datetime import datetime, timedelta, time
from django.http import JsonResponse
from public.models import Profile
from django.utils.text import slugify
from django.core.validators import MinLengthValidator, RegexValidator
from agendamento.validators import validar_horario_expediente
import re

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

    schedule_fields = (
        "horario_inicio",
        "horario_fim",
        "inicio_almoco",
        "fim_almoco",
    )
    if not any(field in data for field in schedule_fields):
        return False, None

    inicio_expediente = data.get("horario_inicio", profile.horario_inicio)
    fim_expediente = data.get("horario_fim", profile.horario_fim)
    inicio_almoco = data.get("inicio_almoco", profile.inicio_almoco)
    fim_almoco = data.get("fim_almoco", profile.fim_almoco)

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

    if "dias_funcionando" in data:
        dias_funcionando = data["dias_funcionando"]
        dias_validos = {
            "domingo",
            "segunda",
            "terca",
            "quarta",
            "quinta",
            "sexta",
            "sabado",
        }
        if (
            not isinstance(dias_funcionando, list)
            or any(
                not isinstance(dia, str) or dia not in dias_validos
                for dia in dias_funcionando
            )
            or len(dias_funcionando) != len(set(dias_funcionando))
        ):
            return None, "dias_funcionando inválidos"

        if dias_funcionando != profile.dias_funcionando:
            profile.dias_funcionando = dias_funcionando
            updated = True
    
    if "public_slug" in data:
        slug = data["public_slug"]

        if not isinstance(slug, str):
            return None, "slug inválido"

        novo_slug = slug.strip().lower()
        if (
            len(novo_slug) > 100
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", novo_slug)
        ):
            return None, "slug inválido"

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
        
    if "nome_negocio" in data:
        if not isinstance(data["nome_negocio"], str):
            return None, "nome inválido"

        if data["nome_negocio"].strip():
            nome_negocio = data["nome_negocio"].strip()

            if len(nome_negocio) < 3:
                return None, "nome deve ter mais de 3 caracteres"
            if len(nome_negocio) > 100:
                return None, "nome inválido"

            if nome_negocio != profile.nome_negocio:
                profile.nome_negocio = nome_negocio
                updated = True

    if "telefone" in data:
        if not isinstance(data["telefone"], str):
            return None, "telefone inválido"

        if data["telefone"].strip():
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

    if "endereco" in data:
        if not isinstance(data["endereco"], str):
            return None, "endereço inválido"

        endereco = data["endereco"].strip()

        if endereco and (len(endereco) < 5 or len(endereco) > 100):
            return None, "endereço inválido"

        if endereco != profile.endereco:
            profile.endereco = endereco
            updated = True

    if "instagram" in data:
        if not isinstance(data["instagram"], str):
            return None, "instagram inválido"

        instagram = data["instagram"].strip()

        if len(instagram) > 100:
            return None, "instagram inválido"

        if instagram != profile.instagram:
            profile.instagram = instagram
            updated = True

    if "descricao" in data:
        if not isinstance(data["descricao"], str):
            return None, "descrição inválida"

        descricao = data["descricao"].strip()

        if len(descricao) > 200:
            return None, "Descrição muito longa"

        if descricao != profile.descricao:

            profile.descricao = descricao
            updated = True
        
    if updated:
        profile.save()
        
    return updated, None