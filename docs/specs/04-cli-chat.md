# Feature Specification: CLI Chat

## Goal

Permitir que o usuário faça perguntas no terminal e receba respostas da LLM fundamentadas exclusivamente nos chunks recuperados do PDF.

## Functional Requirements

- **FR-1:** `src/chat.py` deve receber uma pergunta do usuário pela linha de comando.
- **FR-2:** O chat deve obter os dez resultados mais relevantes por meio da busca definida em `docs/specs/03-semantic-retrieval.md`.
- **FR-3:** Os conteúdos recuperados devem ser concatenados no campo `CONTEXTO` do prompt.
- **FR-4:** O prompt enviado à LLM deve seguir este formato e estas regras:

  ```text
  CONTEXTO:
  {resultados concatenados do banco de dados}

  REGRAS:
  - Responda somente com base no CONTEXTO.
  - Se a informação não estiver explicitamente no CONTEXTO,
  responda:
  "Não tenho informações necessárias para responder sua pergunta."
  - Nunca invente ou use conhecimento externo.
  - Nunca produza opiniões ou interpretações além do que está escrito.

  PERGUNTA DO USUÁRIO:
  {pergunta do usuário}

  RESPONDA A "PERGUNTA DO USUÁRIO"
  ```

- **FR-5:** O chat deve chamar a LLM OpenAI configurada externamente e exibir a resposta no terminal.
- **FR-6:** Quando a informação não estiver explícita no contexto, a resposta deve ser exatamente `Não tenho informações necessárias para responder sua pergunta.`

## Acceptance Criteria

- **AC-1 [FR-1]:** `python src/chat.py` permite informar uma pergunta e apresenta uma resposta.
- **AC-2 [FR-2, FR-3]:** Cada pergunta dispara a recuperação com `k=10` e insere os conteúdos retornados no contexto do prompt.
- **AC-3 [FR-4, FR-5]:** A LLM recebe o contexto, as regras e a pergunta do usuário antes de gerar a resposta.
- **AC-4 [FR-6]:** Uma pergunta cuja resposta não esteja explícita no contexto produz exatamente a mensagem de insuficiência definida.
- **AC-5 [FR-6]:** Uma solicitação de opinião ou interpretação produz a mesma mensagem de insuficiência.
- **AC-6 [FR-4]:** Uma resposta válida não contém fatos que não estejam sustentados pelo contexto recuperado.

## Constraints

- Aplicam-se as restrições globais de `docs/SPEC.md`.
- O chat deve usar o prompt obrigatório sem remover ou enfraquecer suas regras.

## Assumptions

- A infraestrutura, a ingestão e a recuperação semântica foram concluídas antes da execução do chat.

## Edge Cases

- Nenhum resultado recuperado.
- Pergunta sobre conteúdo ausente.
- Solicitação de opinião ou interpretação.

## Out of Scope

- Uso de conhecimento externo ao contexto recuperado.
- Produção de opiniões ou interpretações além do texto.

## Open Questions

- Nenhuma questão permanece aberta.
