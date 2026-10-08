# Testes e validação

## Backend

O backend usa `django.test.TestCase` e o cliente de testes do Django.

Comandos principais:

```bash
python manage.py test
python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
```

Os testes cobrem autenticação, request ID, logging, perfil, expediente,
serviços, disponibilidade, booking, conflito, clientes e estados de
agendamento. Após B3, a suíte local registrada tinha 44 testes aprovados.

## Frontend

O frontend usa Vitest, Testing Library, jsdom e Oxlint:

```bash
npm test
npm run lint
npm run build
```

O teste de autenticação cobre o contexto do cliente e a invalidação da sessão.
As páginas e serviços também são validados por build e lint.

## Histórico de QA

- **UX-14:** execução E2E dos fluxos principais, com limitações explícitas para
  cenários não reproduzidos manualmente.
- **B1:** auditoria de production readiness, banco e configuração de build.
- **B2.0:** inventário de logging.
- **B2.1:** implementação da fundação de observabilidade.
- **B2.2:** QA HTTP real de request ID, eventos, segurança dos logs e concorrência
  de contexto.
- **B3:** tratamento de entradas inválidas e prevenção de `500` esperados.

Esses registros são histórico técnico, não garantia de disponibilidade do
ambiente de produção.
