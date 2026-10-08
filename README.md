# GerenciAgenda

Aplicação de gestão de agenda para profissionais, com painel autenticado e booking público para clientes.

## Stack

- Backend: Django 6, Django REST por `JsonResponse`, PyJWT, PostgreSQL em beta/produção.
- Frontend: React 19, Vite, React Router, Axios, Vitest e Oxlint.
- Desenvolvimento local: SQLite no backend e Vite no frontend.

Os repositórios são separados:

- Backend: este diretório.
- Frontend: `../gerenci-agenda-frontend/gerenci-agenda-front`.

## Estrutura

```text
core/          configurações, URLs, middleware e logging
users/         autenticação, perfil profissional e refresh tokens
public/        perfil público e booking do cliente
agendamento/   agenda profissional, disponibilidade e histórico
cliente/       identificação e vínculo de clientes
servicos/      catálogo de serviços
docs/          documentação técnica
```

## Execução local

### Backend

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

O backend local usa SQLite quando `DATABASE_URL` não está definida.

### Frontend

```bash
cd ../gerenci-agenda-frontend/gerenci-agenda-front
npm install
copy .env.example .env
npm run dev
```

`VITE_API_URL` deve apontar para a API, por exemplo:
`http://127.0.0.1:8000/api`.

## Variáveis de ambiente

Os nomes e as diferenças entre desenvolvimento e produção estão em
[`.env.example`](./.env.example) e em
[docs/deployment.md](./docs/deployment.md).

Não versionar valores reais de secrets, tokens ou URLs de banco.

## Testes e qualidade

```bash
python manage.py test
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
git diff --check
```

No frontend:

```bash
npm test
npm run lint
npm run build
```

## Documentação técnica

- [Arquitetura](./docs/architecture.md)
- [API](./docs/api.md)
- [Autenticação](./docs/authentication.md)
- [Booking](./docs/booking.md)
- [Agenda e disponibilidade](./docs/scheduling.md)
- [Erros](./docs/errors.md)
- [Observabilidade](./docs/observability.md)
- [Deploy](./docs/deployment.md)
- [Testes](./docs/testing.md)
- [Decisões](./docs/decisions.md)
