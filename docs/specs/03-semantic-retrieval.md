# Feature Specification: Semantic Retrieval

## Goal

Converter uma pergunta em embedding e recuperar do PostgreSQL os dez chunks semanticamente mais relevantes para uso como contexto da resposta.

## Functional Requirements

- **FR-1:** `src/search.py` deve vetorizar a pergunta usando o mesmo modelo de embeddings configurado para a ingestão.
- **FR-2:** A busca deve consultar a mesma collection preenchida por `docs/specs/02-pdf-ingestion.md`.
- **FR-3:** A busca deve usar similaridade com score e `k=10`.
- **FR-4:** O resultado deve disponibilizar o conteúdo dos chunks recuperados para composição do contexto do chat.

## Acceptance Criteria

- **AC-1 [FR-1]:** Uma pergunta recebida pela busca é convertida em embedding antes da consulta vetorial.
- **AC-2 [FR-2]:** A consulta usa a collection que recebeu os chunks durante a ingestão.
- **AC-3 [FR-3]:** A operação de busca é executada com `similarity_search_with_score(query, k=10)`.
- **AC-4 [FR-4]:** O chamador recebe os conteúdos recuperados em ordem de relevância do mecanismo de busca.

## Constraints

- Aplicam-se as restrições globais de `docs/SPEC.md`.
- O modelo de embeddings da consulta deve ser compatível com a dimensão da collection.

## Assumptions

- A ingestão foi concluída antes da busca.
- Quando houver menos de dez chunks, a busca retornará somente os resultados disponíveis.

## Edge Cases

- Collection vazia ou ainda não criada.
- Menos de dez chunks disponíveis.
- Modelo de consulta incompatível com a dimensão da collection.

## Out of Scope

- Nenhum item adicional foi explicitamente excluído.

## Open Questions

- Nenhuma questão permanece aberta.
