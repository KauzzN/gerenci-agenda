# Erros e validação

## Semântica HTTP

| Código | Significado no sistema |
|---:|---|
| `200` | leitura ou atualização concluída |
| `201` | recurso ou booking criado |
| `400` | payload, tipo, data, horário ou regra de entrada inválida |
| `401` | autenticação ausente, inválida ou expirada |
| `403` | usuário autenticado sem o perfil/permissão exigido |
| `404` | recurso ou relação inexistente |
| `405` | método HTTP não permitido |
| `409` | conflito de recurso, especialmente horário ocupado no booking público |
| `500` | falha inesperada não representada por validação conhecida |

O formato de erro predominante é:

```json
{
  "error": "mensagem"
}
```

Não existe um envelope global adicional.

## Validação

JSON malformado, corpo vazio ou content type incorreto são rejeitados por
`parse_json_body`. Datas e horários são validados antes de serem usados nas
regras de agenda. IDs inexistentes são tratados com `404` quando representam
um recurso ausente; serviços inválidos no booking retornam `400` conforme o
contrato atual.

Erros de entrada esperada não devem resultar em `500`. Os caminhos corrigidos
no B3 incluem:

- descrição de serviço ausente;
- campos opcionais/default enviados como `null`;
- atualização parcial de expediente;
- tipos inválidos em perfil, serviço, data e horário;
- limites de tamanho e preço antes da persistência.

## Autorização versus inexistência

O backend preserva a diferença entre:

- token inválido: `401`;
- usuário sem perfil profissional ou cliente: `403`;
- recurso que não existe para aquele usuário: normalmente `404`;
- relação de cliente inativa: `403`.

## Falhas inesperadas

Não há captura ampla de exceções nas views para transformar qualquer falha em
`400`. Exceções inesperadas continuam sendo tratadas pelo Django e registradas
em `django.request`, com request ID no contexto principal.
