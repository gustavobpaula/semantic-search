"""Chat no terminal: laço de perguntas, formato da saída e encerramento.

Tudo offline: o encadeamento é injetado e, quando a cadeia real é usada,
store e LLM são dublês — sem OpenAI nem PostgreSQL.
"""

import builtins

import pytest

import chat
from chat import DESPEDIDA, ROTULO_PERGUNTA, ROTULO_RESPOSTA, main
from config import ConfigError
from conftest import FakeVectorStore, RecordingLLM
from search import MENSAGEM_SEM_CONTEXTO, PROMPT_TEMPLATE, SearchError, search_prompt

CHUNKS = [f"trecho numero {indice}" for indice in range(12)]


class CadeiaFalsa:
    """Encadeamento falso que registra as perguntas recebidas."""

    def __init__(self, resposta: str = "resposta da LLM", erro: Exception | None = None):
        self.resposta = resposta
        self.erro = erro
        self.perguntas: list[str] = []

    def invoke(self, pergunta: str) -> str:
        self.perguntas.append(pergunta)
        if self.erro is not None:
            raise self.erro
        return self.resposta


def responder_com(monkeypatch, linhas: list[str]) -> None:
    """Faz o `input` do chat devolver `linhas` e depois sinalizar EOF."""
    entradas = iter(linhas)

    def falso_input(prompt=""):
        print(prompt, end="")
        try:
            linha = next(entradas)
        except StopIteration:
            raise EOFError from None
        print(linha)
        return linha

    monkeypatch.setattr(builtins, "input", falso_input)


def test_varias_perguntas_em_sequencia(monkeypatch, capsys):
    """AC-1: cada pergunta da sessão recebe a sua resposta."""
    cadeia = CadeiaFalsa()
    responder_com(monkeypatch, ["primeira", "segunda", "terceira"])

    assert main(chain=cadeia) == 0

    assert cadeia.perguntas == ["primeira", "segunda", "terceira"]
    assert capsys.readouterr().out.count(ROTULO_RESPOSTA) == 3


def test_pergunta_e_respondida_pelo_encadeamento_com_k_10(monkeypatch, settings):
    """AC-2: a pergunta percorre a cadeia real, com k=10 e o prompt obrigatório."""
    store = FakeVectorStore(CHUNKS)
    llm = RecordingLLM()
    cadeia = search_prompt(settings=settings, store=store, llm=llm)
    responder_com(monkeypatch, ["qual o faturamento?"])

    assert main(chain=cadeia) == 0

    assert store.consultas == [("qual o faturamento?", 10)]
    assert llm.prompts[0] == PROMPT_TEMPLATE.format(
        contexto="\n\n".join(CHUNKS[:10]), pergunta="qual o faturamento?"
    )


def test_encadeamento_e_criado_uma_unica_vez(monkeypatch):
    """AC-2: o chat monta a cadeia na entrada e a reutiliza nas perguntas."""
    cadeia = CadeiaFalsa()
    criacoes = []

    def falso_search_prompt():
        criacoes.append(cadeia)
        return cadeia

    monkeypatch.setattr(chat, "search_prompt", falso_search_prompt)
    responder_com(monkeypatch, ["primeira", "segunda"])

    assert main() == 0

    assert len(criacoes) == 1
    assert cadeia.perguntas == ["primeira", "segunda"]


def test_saida_distingue_pergunta_e_resposta(monkeypatch, capsys):
    """AC-3: a resposta aparece logo após a pergunta correspondente."""
    responder_com(monkeypatch, ["qual o faturamento?"])

    main(chain=CadeiaFalsa(resposta="10 milhões de reais"))

    saida = capsys.readouterr().out
    assert f"{ROTULO_PERGUNTA}qual o faturamento?" in saida
    posicao_pergunta = saida.index(f"{ROTULO_PERGUNTA}qual o faturamento?")
    posicao_resposta = saida.index(f"{ROTULO_RESPOSTA}10 milhões de reais")
    assert posicao_pergunta < posicao_resposta


def test_pergunta_sem_contexto_exibe_a_mensagem_de_insuficiencia(
    monkeypatch, capsys, settings
):
    """AC-4: sem chunks recuperados, o terminal mostra exatamente a mensagem."""
    cadeia = search_prompt(settings=settings, store=FakeVectorStore([]), llm=RecordingLLM())
    responder_com(monkeypatch, ["quantos clientes temos em 2024?"])

    main(chain=cadeia)

    saida = capsys.readouterr().out
    assert f"{ROTULO_RESPOSTA}{MENSAGEM_SEM_CONTEXTO}" in saida
    assert (
        f"{ROTULO_RESPOSTA}Não tenho informações necessárias para responder sua pergunta."
        in saida
    )


@pytest.mark.parametrize("comando", ["sair", "exit", "QUIT", "  Sair  "])
def test_comando_de_saida_encerra_a_sessao(monkeypatch, capsys, comando):
    """FR-7: os comandos de saída encerram sem consultar a cadeia."""
    cadeia = CadeiaFalsa()
    responder_com(monkeypatch, [comando, "nao deve ser perguntado"])

    assert main(chain=cadeia) == 0

    assert cadeia.perguntas == []
    assert DESPEDIDA in capsys.readouterr().out


def test_fim_da_entrada_encerra_a_sessao(monkeypatch, capsys):
    """FR-7: EOF (Ctrl+D) termina o laço com código 0."""
    responder_com(monkeypatch, [])

    assert main(chain=CadeiaFalsa()) == 0

    assert DESPEDIDA in capsys.readouterr().out


def test_interrupcao_do_teclado_encerra_sem_traceback(monkeypatch, capsys):
    """FR-7: Ctrl+C durante a pergunta encerra com código 0."""

    def input_interrompido(prompt=""):
        raise KeyboardInterrupt

    monkeypatch.setattr(builtins, "input", input_interrompido)

    assert main(chain=CadeiaFalsa()) == 0

    assert DESPEDIDA in capsys.readouterr().out


@pytest.mark.parametrize("vazia", ["", "   ", "\t"])
def test_entrada_vazia_nao_aciona_o_encadeamento(monkeypatch, capsys, vazia):
    """FR-8: linha vazia é ignorada e o chat volta a perguntar."""
    cadeia = CadeiaFalsa()
    responder_com(monkeypatch, [vazia, "pergunta de verdade"])

    assert main(chain=cadeia) == 0

    assert cadeia.perguntas == ["pergunta de verdade"]
    assert capsys.readouterr().out.count(ROTULO_PERGUNTA) == 3


def test_configuracao_incompleta_interrompe_o_chat(monkeypatch, capsys):
    """Edge case: sem configuração o chat nem começa, e sinaliza falha."""

    def search_prompt_quebrado():
        raise ConfigError("Configuração incompleta. Defina no .env: OPENAI_API_KEY")

    monkeypatch.setattr(chat, "search_prompt", search_prompt_quebrado)

    assert main() == 1

    capturado = capsys.readouterr()
    assert "Configuração incompleta" in capturado.err
    assert capturado.out == ""


def test_falha_na_busca_interrompe_com_mensagem_clara(monkeypatch, capsys):
    """Edge case: banco indisponível encerra a sessão com código 1."""
    cadeia = CadeiaFalsa(erro=SearchError("Falha ao consultar a collection: timeout"))
    responder_com(monkeypatch, ["pergunta"])

    assert main(chain=cadeia) == 1

    assert "Falha ao consultar a collection" in capsys.readouterr().err
