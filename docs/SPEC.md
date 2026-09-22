# Specification

## Goal

Entregar uma aplicação em Python que ingira um PDF no PostgreSQL com pgVector e responda perguntas pelo terminal usando exclusivamente informações recuperadas do documento. O briefing de origem está transcrito em [challenge.md](challenge.md).

## Feature Specifications

- [01 - Infrastructure](specs/01-infrastructure.md)
- [02 - PDF Ingestion](specs/02-pdf-ingestion.md)
- [03 - Semantic Retrieval](specs/03-semantic-retrieval.md)
- [04 - CLI Chat](specs/04-cli-chat.md)

## Functional Requirements

- **FR-1:** O sistema deve oferecer um fluxo executável na ordem: iniciar o banco, ingerir `document.pdf` e iniciar o chat no terminal.
- **FR-2:** O projeto deve ser entregue em um repositório público no GitHub, com todo o código-fonte e instruções claras de execução.

## Acceptance Criteria

- **AC-1 [FR-1]:** Seguindo o README, o usuário consegue executar `docker compose up -d`, `python src/ingest.py` e `python src/chat.py`, nessa ordem, concluindo o fluxo completo.
- **AC-2 [FR-2]:** A URL de entrega usa `https://`, aponta para um repositório público e disponibiliza o código-fonte e o README.

## Constraints

- A implementação deve usar Python, LangChain, PostgreSQL com pgVector e Docker Compose.
- O provedor de embeddings e LLM deve ser OpenAI por meio da integração do LangChain.
- A chave de API e os identificadores dos modelos devem ser configurações externas.
- Os identificadores dos modelos não devem ser fixados nesta especificação.
- A estrutura deve conter `docker-compose.yml`, `requirements.txt`, `.env.example`, `src/ingest.py`, `src/search.py`, `src/chat.py`, `document.pdf` e `README.md`.
- As interfaces públicas de execução devem permanecer:
  - `docker compose up -d`
  - `python src/ingest.py`
  - `python src/chat.py`

## Assumptions

- `document.pdf` é o único documento exigido para a execução do desafio.
- Um modelo de embeddings e um modelo de LLM disponíveis serão selecionados no momento da implementação.

## Edge Cases

- A troca do modelo de embeddings pode alterar a dimensão dos vetores e exigir a recriação da collection ou do volume do banco.

## Out of Scope

- Nenhum item adicional foi explicitamente excluído no escopo global.

## Open Questions

- Nenhuma questão global permanece aberta.
