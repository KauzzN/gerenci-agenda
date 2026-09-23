from django.contrib.auth.models import User
from public.models import Profile
from .models import Cliente, ClienteProfissional


def validar_cliente(data):
    if not isinstance(data, dict) or "telefone" not in data:
        return None, "telefone é obrigatório"

    telefone = data["telefone"]
    if not isinstance(telefone, str):
        return None, "telefone deve ser uma string"

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

    cliente = Cliente.objects.filter(telefone=telefone).first()
    return cliente, None

def validar_telefone(telefone):

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

    return telefone, None

