from servicos.models import Servico
from decimal import Decimal, InvalidOperation

def atualizar_servico(request, servico, data):

    updated = False

    if "nome" in data and data["nome"] not in (None, ""):
        if not isinstance(data["nome"], str):
            return None, "nome deve ser texto"

        nome = data["nome"].strip()
        if not nome:
            return None, "nome não pode ser vazio"
        if len(nome) > 50:
            return None, "nome deve ter no máximo 50 caracteres"

        if nome != servico.nome:

            servico.nome = nome
            updated = True

    if "preco" in data and data["preco"] not in (None, ""):

        preco = data["preco"]

        try:
            preco = Decimal(str(preco))

        except (InvalidOperation, TypeError, ValueError):
            return None, "preço deve ser um número válido"

        if not preco.is_finite():
            return None, "preço deve ser um número válido"

        if preco.as_tuple().exponent < -2:
            return None, "preço deve ter no máximo duas casas decimais"

        if abs(preco) >= Decimal("1000000"):
            return None, "preço fora do limite permitido"

        if preco < 0:
            return None, "preço não pode ser negativo"

        if preco != servico.preco:

            servico.preco = preco
            updated = True


    if "duracao" in data and data["duracao"] not in (None, ""):

        duracao = data["duracao"]

        if isinstance(duracao, bool):
            return None, "duração precisa ser número"

        if isinstance(duracao, str):
            duracao = duracao.strip()

        if isinstance(duracao, str) and not duracao.isdigit():
            return None, "duração precisa ser número"

        try:
            duracao = int(duracao)
        except (TypeError, ValueError):
            return None, "duração precisa ser número"

        if duracao <= 0:
            return None, "duração deve ser maior que zero"

        if duracao != servico.duracao:
             
            servico.duracao = duracao
            updated = True

    if "descricao" in data and data["descricao"] not in (None, ""):
        if not isinstance(data["descricao"], str):
            return None, "descrição deve ser texto"

        descricao = data["descricao"].strip()

        if len(descricao) > 200:
            return None, "Descrição muito longa"

        if descricao != servico.descricao:

            servico.descricao = descricao
            updated = True

    if "cor" in data and data["cor"] not in (None, ""):
        if not isinstance(data["cor"], str):
            return None, "cor inválida"

        cor = data["cor"].strip()

        if (
            len(cor) not in (4, 7)
            or not cor.startswith("#")
            or any(character not in "0123456789abcdefABCDEF" for character in cor[1:])
        ):
            return None, "cor inválida"

        if cor != servico.cor:

            servico.cor = cor
            updated = True

    if "ativo" in data:
        ativo = data["ativo"]
        if not isinstance(ativo, bool):
            return None, "ativo deve ser booleano"

        if ativo != servico.ativo:

            servico.ativo = ativo
            updated = True

    if updated:
        servico.save()

    return updated, None
        

        