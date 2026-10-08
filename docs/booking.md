# Booking público

## Fluxo

```text
GET perfil público
      ↓
POST identificação do cliente
      ↓
seleção de serviços
      ↓
seleção de data
      ↓
GET horários disponíveis
      ↓
seleção de horário
      ↓
POST agendamento
      ↓
confirmação
```

O perfil público é carregado sem autenticação e retorna somente serviços ativos.
Antes de consultar horários ou criar o booking, o frontend identifica o cliente
e salva o token de cliente.

## Validações

O backend valida:

- slug público existente;
- relação ativa entre cliente e profissional;
- lista não vazia de IDs de serviços;
- IDs positivos, inteiros e sem duplicação;
- serviços pertencentes ao profissional e ativos;
- data em formato ISO e não passada;
- horário em formato ISO e não passado;
- expediente configurado;
- dia configurado em `dias_funcionando`;
- horário dentro do expediente e fora do almoço;
- ausência de conflito de horário.

O horário final é calculado pela soma das durações dos serviços selecionados.

## Disponibilidade

`GET /api/public/<slug>/horarios` gera horários em passos de 30 minutos. Só são
retornados horários futuros que:

1. cabem entre `horario_inicio` e `horario_fim`;
2. pertencem a um dia configurado;
3. não atravessam o intervalo de almoço;
4. não colidem com agendamentos ativos.

## Confirmação e conflito

O frontend usa `bookingRef` para impedir duplo envio enquanto a confirmação está
em andamento. Depois de sucesso, marca `bookingCompleted`, limpa o horário
selecionado e atualiza a disponibilidade.

Se a API retornar `409`:

- nenhum sucesso falso é exibido;
- o horário selecionado é limpo;
- a disponibilidade é consultada novamente;
- o cliente pode escolher outro horário.

Se a primeira tentativa ocorrer sem autenticação de cliente, o frontend apenas
identifica o cliente e retorna ao fluxo. Ele não agenda automaticamente nessa
mesma ação.

## Relação com Agenda e Histórico

Um booking público cria `Agendamento` com status inicial `PENDENTE` e os
`ItemAgendamento` correspondentes. Ele aparece na Agenda profissional. O
Histórico lista agendamentos cujo status não é `PENDENTE`.

O cancelamento profissional altera o status para `CANCELADO`; o registro
permanece disponível para o histórico.

## Limites conhecidos

O booking público não possui endpoint de cancelamento para o cliente. O
cancelamento existente é uma operação profissional da agenda.
