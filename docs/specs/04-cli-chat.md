# Feature Specification: CLI Chat

## Goal

Permitir que o usuário faça perguntas no terminal, em interação contínua, e receba respostas da LLM fundamentadas exclusivamente nos chunks recuperados do PDF.

## Functional Requirements

- **FR-1:** `src/chat.py` deve simular um chat no terminal, recebendo perguntas do usuário de forma repetida e apresentando cada resposta antes de solicitar a próxima.
- **FR-2:** O chat deve obter a resposta por meio do encadeamento definido em `docs/specs/03-semantic-retrieval.md FR-5`, criado uma vez e reutilizado nas perguntas seguintes.
- **FR-5:** O chat deve exibir a resposta no terminal distinguindo pergunta e resposta, como no exemplo do briefing (`PERGUNTA:` e `RESPOSTA:`).
- **FR-6:** Quando a informação não estiver explícita no contexto, a resposta deve ser exatamente `Não tenho informações necessárias para responder sua pergunta.`
- **FR-7:** O chat deve encerrar a sessão quando o usuário digitar `sair`, `exit` ou `quit`, ou quando a entrada terminar (Ctrl+D) ou for interrompida (Ctrl+C). A forma de encerrar deve ser anunciada ao iniciar a sessão.
- **FR-8:** Uma entrada vazia ou composta apenas por espaços deve ser ignorada, sem acionar o encadeamento, e o chat deve solicitar a próxima pergunta.

`FR-3` e `FR-4` foram movidos para `docs/specs/03-semantic-retrieval.md` (`FR-4` e `FR-5`). Os identificadores permanecem vagos para não renumerar os demais.

## Acceptance Criteria

- **AC-1 [FR-1]:** `python src/chat.py` permite informar várias perguntas em sequência, apresentando uma resposta para cada uma.
- **AC-2 [FR-2]:** Cada pergunta é respondida pelo encadeamento de recuperação, com `k=10`, sem que o chat monte o prompt por conta própria.
- **AC-3 [FR-5]:** A resposta é exibida no terminal associada à pergunta correspondente.
- **AC-4 [FR-6]:** Uma pergunta cuja resposta não esteja explícita no contexto produz exatamente a mensagem de insuficiência definida.
- **AC-5 [FR-6]:** Uma solicitação de opinião ou interpretação produz a mesma mensagem de insuficiência.
- **AC-6 [FR-6]:** Uma resposta válida não contém fatos que não estejam sustentados pelo contexto recuperado.
- **AC-7 [FR-7]:** Um comando de saída, o fim da entrada ou uma interrupção pelo teclado encerram a sessão sem erro, e a sessão informa como encerrá-la ao iniciar.
- **AC-8 [FR-8]:** Uma entrada vazia não gera consulta ao banco nem chamada à LLM, e o chat solicita a próxima pergunta.

## Constraints

- Aplicam-se as restrições globais de `docs/SPEC.md`.
- O chat não deve montar nem alterar o prompt obrigatório; ele pertence a `docs/specs/03-semantic-retrieval.md FR-5`.

## Assumptions

- A infraestrutura, a ingestão e a recuperação semântica foram concluídas antes da execução do chat.

## Edge Cases

- Nenhum resultado recuperado.
- Pergunta sobre conteúdo ausente.
- Solicitação de opinião ou interpretação.
- Entrada vazia informada pelo usuário (resolvida por `FR-8`).
- Falha de configuração ou de recuperação durante a sessão: o chat interrompe com mensagem clara e código de saída 1.

## Out of Scope

- Uso de conhecimento externo ao contexto recuperado.
- Produção de opiniões ou interpretações além do texto.

## Open Questions

- Nenhuma questão permanece aberta. O briefing não define comando de saída nem política para entrada vazia; `FR-7` e `FR-8` registram as decisões tomadas.
