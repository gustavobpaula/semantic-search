# Feature Specification: Infrastructure

## Goal

Disponibilizar o ambiente local necessário para executar PostgreSQL com pgVector e configurar as dependências e credenciais usadas pelas demais features.

## Functional Requirements

- **FR-1:** O `docker-compose.yml` fornecido pelo repositório de exemplo deve iniciar um banco PostgreSQL com a extensão pgVector disponível.
- **FR-2:** `requirements.txt` deve declarar as dependências necessárias para LangChain, PostgreSQL/pgVector, leitura de PDF e integração com OpenAI.
- **FR-3:** `.env.example` deve manter as variáveis do repositório de exemplo — `GOOGLE_API_KEY`, `GOOGLE_EMBEDDING_MODEL`, `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `DATABASE_URL`, `PG_VECTOR_COLLECTION_NAME` e `PDF_PATH` — acrescidas de `OPENAI_LLM_MODEL`, sem valores secretos reais.
- **FR-4:** O README deve instruir como criar e ativar o ambiente virtual, instalar dependências, configurar as variáveis e iniciar o banco.

## Acceptance Criteria

- **AC-1 [FR-1]:** `docker compose up -d` inicia o PostgreSQL e permite utilizar a extensão pgVector.
- **AC-2 [FR-2]:** As dependências podem ser instaladas em um ambiente virtual novo a partir de `requirements.txt`.
- **AC-3 [FR-3]:** `.env.example` contém as variáveis do repositório de exemplo mais `OPENAI_LLM_MODEL` e não contém credenciais reais.
- **AC-4 [FR-4]:** O README apresenta `python3 -m venv venv`, `source venv/bin/activate`, instalação das dependências e `docker compose up -d`, e documenta os valores que o usuário deve preencher em `.env`.

## Constraints

- Aplicam-se as tecnologias e a estrutura definidas em `docs/SPEC.md`, seção `Constraints`.
- A integração de modelos deve usar OpenAI por meio do LangChain.
- Os nomes dos modelos devem permanecer configuráveis.

## Assumptions

- Docker, Docker Compose e Python 3 estarão disponíveis no ambiente do usuário.
- As variáveis `GOOGLE_*` são herdadas do repositório de exemplo e não são usadas por este projeto.

## Edge Cases

- Configuração ausente ou inválida da conexão com o banco.
- Chave da OpenAI ausente ou inválida.

## Out of Scope

- Nenhum item adicional foi explicitamente excluído.

## Open Questions

- Nenhuma questão permanece aberta.
