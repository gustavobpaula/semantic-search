# Feature Specification: Semantic Retrieval

## Goal

Converter uma pergunta em embedding, recuperar do PostgreSQL os dez chunks semanticamente mais relevantes e montar, com eles, o prompt obrigatório enviado à LLM.

## Functional Requirements

- **FR-1:** `src/search.py` deve vetorizar a pergunta usando o mesmo modelo de embeddings configurado para a ingestão.
- **FR-2:** A busca deve consultar a mesma collection preenchida por `docs/specs/02-pdf-ingestion.md`.
- **FR-3:** A busca deve usar similaridade com score e `k=10`.
- **FR-4:** Os conteúdos dos chunks recuperados devem ser concatenados no campo `CONTEXTO` do prompt, na ordem retornada pelo mecanismo de busca.
- **FR-5:** `src/search.py` deve expor `search_prompt()`, que monta o prompt obrigatório abaixo e o encadeia com a LLM OpenAI configurada externamente por `OPENAI_LLM_MODEL`:

  ```text
  CONTEXTO:
  {contexto}

  REGRAS:
  - Responda somente com base no CONTEXTO.
  - Se a informação não estiver explicitamente no CONTEXTO, responda:
    "Não tenho informações necessárias para responder sua pergunta."
  - Nunca invente ou use conhecimento externo.
  - Nunca produza opiniões ou interpretações além do que está escrito.

  EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
  Pergunta: "Qual é a capital da França?"
  Resposta: "Não tenho informações necessárias para responder sua pergunta."

  Pergunta: "Quantos clientes temos em 2024?"
  Resposta: "Não tenho informações necessárias para responder sua pergunta."

  Pergunta: "Você acha isso bom ou ruim?"
  Resposta: "Não tenho informações necessárias para responder sua pergunta."

  PERGUNTA DO USUÁRIO:
  {pergunta}

  RESPONDA A "PERGUNTA DO USUÁRIO"
  ```

- **FR-6:** `search_prompt()` deve devolver um encadeamento reutilizável que aceita uma pergunta e produz a resposta da LLM.
- **FR-7:** Quando a busca não recuperar nenhum chunk, o encadeamento deve responder exatamente `Não tenho informações necessárias para responder sua pergunta.` sem acionar a LLM.

## Acceptance Criteria

- **AC-1 [FR-1]:** Uma pergunta recebida pela busca é convertida em embedding antes da consulta vetorial.
- **AC-2 [FR-2]:** A consulta usa a collection que recebeu os chunks durante a ingestão.
- **AC-3 [FR-3]:** A operação de busca é executada com `similarity_search_with_score(query, k=10)`.
- **AC-4 [FR-4]:** O campo `CONTEXTO` contém os conteúdos recuperados na ordem de relevância devolvida pela busca.
- **AC-5 [FR-5]:** O prompt enviado à LLM reproduz o texto obrigatório sem remover ou enfraquecer suas regras.
- **AC-6 [FR-6]:** O encadeamento pode ser criado uma vez e invocado para várias perguntas.
- **AC-7 [FR-7]:** Com a collection vazia ou sem resultados para a pergunta, a resposta é exatamente a mensagem de insuficiência e nenhuma chamada à LLM é feita.

## Constraints

- Aplicam-se as restrições globais de `docs/SPEC.md`.
- O modelo de embeddings da consulta deve ser compatível com a dimensão da collection.
- O texto do prompt obrigatório não pode ser alterado.

## Assumptions

- A ingestão foi concluída antes da busca.
- Quando houver menos de dez chunks, a busca retornará somente os resultados disponíveis.

## Edge Cases

- Collection vazia ou ainda não criada (resolvida por `FR-7`).
- Menos de dez chunks disponíveis.
- Modelo de consulta incompatível com a dimensão da collection.

## Out of Scope

- Nenhum item adicional foi explicitamente excluído.

## Open Questions

- Nenhuma questão permanece aberta.
