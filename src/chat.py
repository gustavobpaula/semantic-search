"""Chat no terminal sobre o conteúdo do PDF ingerido."""

import sys

from config import ConfigError
from search import SearchError, search_prompt

COMANDOS_DE_SAIDA = ("sair", "exit", "quit")

ROTULO_PERGUNTA = "PERGUNTA: "
ROTULO_RESPOSTA = "RESPOSTA: "

BANNER = (
    "Chat sobre o documento ingerido. Faça sua pergunta.\n"
    f"Para encerrar: '{COMANDOS_DE_SAIDA[0]}' ou Ctrl+C.\n"
)

DESPEDIDA = "Até logo."


def ler_pergunta() -> str | None:
    """Devolve a linha digitada, ou `None` quando a entrada termina (EOF).

    O rótulo da pergunta é o próprio prompt do `input`, de modo que a
    transcrição do terminal já sai no formato do briefing.
    """
    try:
        return input(ROTULO_PERGUNTA)
    except EOFError:
        print()
        return None


def conversar(chain) -> None:
    """Pergunta, responde e repete até o usuário encerrar.

    Linha vazia não chega ao encadeamento: sem pergunta não há consulta
    ao banco nem chamada à LLM.
    """
    while True:
        linha = ler_pergunta()
        if linha is None:
            break

        pergunta = linha.strip()
        if not pergunta:
            continue
        if pergunta.lower() in COMANDOS_DE_SAIDA:
            break

        print(f"{ROTULO_RESPOSTA}{chain.invoke(pergunta)}\n")

    print(DESPEDIDA)


def main(chain=None) -> int:
    """Cria o encadeamento uma única vez e conduz a conversa.

    `chain` existe para os testes injetarem um encadeamento pronto; na
    execução real ele vem de `search_prompt()`.
    """
    try:
        chain = chain if chain is not None else search_prompt()
        print(BANNER)
        conversar(chain)
    except (ConfigError, SearchError) as error:
        print(error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print(f"\n{DESPEDIDA}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
