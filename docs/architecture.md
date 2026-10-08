# Arquitetura

## Visão geral

O produto é dividido em dois repositórios:

```text
React/Vite
    ↓ Axios/HTTP
Django
    ↓ Django ORM
PostgreSQL em beta/produção
SQLite em desenvolvimento local quando DATABASE_URL não existe
```

O frontend não é servido pelo Django neste repositório. A URL da API é
configurada no frontend por `VITE_API_URL`.

## Repositórios

| Repositório | Responsabilidade | Testes/configuração |
|---|---|---|
| Backend, diretório atual | API HTTP, autenticação, regras de agenda, persistência e logging | `*/tests.py`, `manage.py`, `core/settings.py` |
| Frontend, `../gerenci-agenda-frontend/gerenci-agenda-front` | Interface React, navegação, estado de sessão e consumo da API | `src/*.test.jsx`, `package.json`, Vite |

## Backend

### `core`

Configura o projeto Django, URLs agregadoras, CORS, segurança, banco, middleware
de request ID e logging.

### `users`

Mantém autenticação profissional, perfil do profissional, access/refresh tokens,
decorators de autorização e atualização de expediente.

### `public`

Expõe perfil público, disponibilidade e criação de booking para o cliente.
Também contém o modelo `Profile` e as regras de combinação de horário.

### `agendamento`

Mantém `Agendamento` e `ItemAgendamento`, agenda profissional, dashboard,
histórico, atualização/cancelamento e regras de disponibilidade.

### `cliente`

Identifica clientes por nome e telefone, cria a relação com o perfil profissional
e expõe os dados de clientes ao painel profissional.

### `servicos`

Mantém o catálogo do profissional: nome, preço, duração, descrição, cor e status
ativo.

## Frontend

O código está em `src/` e é organizado por responsabilidade:

- `pages/`: login, cadastro, dashboard, configurações, serviços, clientes,
  histórico e booking público;
- `components/`: shell do painel, navegação, cards, modais e componentes de UI;
- `contexts/`: `AuthContext` para profissional e `ClientAuthContext` para cliente;
- `hooks/`: hooks compartilhados;
- `routes/`: `PrivateRoute`;
- `services/`: chamadas Axios da API;
- `utils/`: tokens e links públicos;
- `styles/`: tokens e estilos globais.

As rotas `/dashboard`, `/configuracoes`, `/servicos`, `/clientes` e
`/historico` usam `PrivateRoute`. A rota `/book/:slug` fica fora do shell
autenticado profissional e usa a autenticação independente do cliente.

## Persistência principal

- `Profile` possui relação um-para-um com o usuário profissional.
- `Servico` pertence a um usuário profissional.
- `Cliente` possui um usuário próprio.
- `ClienteProfissional` liga um cliente a um perfil e possui `ativo`.
- `Agendamento` liga cliente e profissional; `ItemAgendamento` liga serviços ao
  agendamento.

As relações de agendamento para cliente e serviço usam `PROTECT`; registros
referenciados não podem ser removidos enquanto houver agendamento dependente.
