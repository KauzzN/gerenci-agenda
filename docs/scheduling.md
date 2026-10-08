# Agenda e disponibilidade

## Configuração do perfil

O `Profile` possui:

- `horario_inicio`;
- `horario_fim`;
- `inicio_almoco`;
- `fim_almoco`;
- `dias_funcionando`.

Atualizações de expediente são parciais. Quando somente parte do expediente é
enviada, a validação combina o payload com os valores já persistidos. Uma
combinação incompleta sem expediente existente retorna `400`.

## Dias de funcionamento

`dias_funcionando` é uma lista de nomes validados pelo endpoint de perfil:

```json
["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]
```

Uma lista vazia significa agenda não configurada. Ela **não** significa
funcionamento todos os dias.

Domingo não possui tratamento especial: pode estar ausente (OFF) ou presente
(ON), como qualquer outro dia.

## Expediente e almoço

O início deve ser anterior ao fim. Se o almoço for configurado, início e fim
devem ser enviados juntos, o fim deve ser posterior ao início e o intervalo
deve estar dentro do expediente.

Horários fora do expediente, que atravessem o almoço ou cujo dia não esteja
configurado não são disponíveis.

## Agenda profissional

`GET /api/agendar/read` usa a data atual quando nenhum parâmetro é informado.
Com `data=YYYY-MM-DD`, lista somente os registros daquela data.

A Agenda exibe agendamentos `PENDENTE`, `ATENDIDO` e `FALTOU`. Registros
`CANCELADO` não aparecem na lista principal, mas continuam no histórico.

O dashboard considera os registros do dia e exclui cancelados. O histórico
ordena registros não pendentes pelo horário decrescente.

## Status

| Status | Significado | Transições permitidas |
|---|---|---|
| `PENDENTE` | agendamento criado e ainda não concluído | `PENDENTE`, `ATENDIDO`, `CANCELADO`, `FALTOU` |
| `ATENDIDO` | atendimento realizado | `ATENDIDO`, `CANCELADO` |
| `FALTOU` | cliente não compareceu | `FALTOU`, `CANCELADO` |
| `CANCELADO` | agendamento cancelado | `CANCELADO` |

As transições são definidas em `Agendamento.STATUS_TRANSITIONS`.

## Conflitos

Existe conflito quando outro agendamento do mesmo profissional se sobrepõe ao
intervalo solicitado. Agendamentos cancelados não bloqueiam o horário.

O booking público retorna `409` para conflito. A atualização profissional usa o
contrato atual do endpoint e retorna `400` quando encontra conflito durante a
edição.
