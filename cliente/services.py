from django.contrib.auth.models import User
from public.models import Profile
from .models import Cliente, ClienteProfissional


def validar_telefone(telefone):
    if not isinstance(telefone, str):
        return None, "telefone deve ser uma string"

    telefone = "".join(
        caractere for caractere in telefone
        if caractere not in "()-. "
    )

    if not telefone.isdigit():
        return None, "o telefone deve conter apenas números"

    if len(telefone) not in [10, 11]:
        return None, "formato de telefone inválido"

    if len(set(telefone)) == 1:
        return None, "telefone inválido"

    return telefone, None


def validar_cliente(data):
    if not isinstance(data, dict):
        return None, "dados inválidos"

    nome = data.get("nome")
    if not isinstance(nome, str) or not nome.strip():
        return None, "nome é obrigatório"
    nome = nome.strip()
    if len(nome) > 100:
        return None, "nome deve ter no máximo 100 caracteres"

    if "telefone" not in data:
        return None, "telefone é obrigatório"
    telefone, erro = validar_telefone(data["telefone"])
    if erro:
        return None, erro

    cliente = Cliente.objects.filter(telefone=telefone).first()
    return cliente, None
