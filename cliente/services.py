from django.contrib.auth.models import User
from public.models import Profile
from .models import Cliente, ClienteProfissional


def validar_cliente(data):

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

    try:

        cliente = Cliente.objects.get(
            telefone=telefone
        )

    except Cliente.DoesNotExist:

        return None, "cliente não encontrado"

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

