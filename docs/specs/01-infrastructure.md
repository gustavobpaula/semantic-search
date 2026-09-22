# Feature Specification: Infrastructure

## Goal

Disponibilizar o ambiente local necessário para executar PostgreSQL com pgVector e configurar as dependências e credenciais usadas pelas demais features.

## Functional Requirements

- **FR-1:** `docker-compose.yml` deve iniciar um banco PostgreSQL com a extensão pgVector disponível.
- **FR-2:** `requirements.txt` deve declarar as dependências necessárias para LangChain, PostgreSQL/pgVector, leitura de PDF e integração com OpenAI.
- **FR-3:** `.env.example` deve documentar, sem valores secretos reais, as configurações necessárias para conexão com o banco, chave da OpenAI e identificação dos modelos.
- **FR-4:** O README deve instruir como criar e ativar o ambiente virtual, instalar dependências, configurar as variáveis e iniciar o banco.

## Acceptance Criteria

- **AC-1 [FR-1]:** `docker compose up -d` inicia o PostgreSQL e permite utilizar a extensão pgVector.
- **AC-2 [FR-2]:** As dependências podem ser instaladas em um ambiente virtual novo a partir de `requirements.txt`.
- **AC-3 [FR-3]:** `.env.example` contém todas as configurações exigidas pela aplicação e não contém credenciais reais.
- **AC-4 [FR-4]:** O README apresenta `python3 -m venv venv`, `source venv/bin/activate`, instalação das dependências e `docker compose up -d`.

## Constraints

- Aplicam-se as tecnologias e a estrutura definidas em `docs/SPEC.md`, seção `Constraints`.
- A integração de modelos deve usar OpenAI por meio do LangChain.
- Os nomes dos modelos devem permanecer configuráveis.

## Assumptions

- Docker, Docker Compose e Python 3 estarão disponíveis no ambiente do usuário.

## Edge Cases

- Configuração ausente ou inválida da conexão com o banco.
- Chave da OpenAI ausente ou inválida.

## Out of Scope

- Nenhum item adicional foi explicitamente excluído.

## Open Questions

- Nenhuma questão permanece aberta.
