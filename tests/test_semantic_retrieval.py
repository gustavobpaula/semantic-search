"""Recuperação semântica: contexto, prompt obrigatório e encadeamento.

Tudo offline: a store e a LLM são dublês, sem OpenAI nem PostgreSQL.
"""

import pytest

from conftest import FakeVectorStore, RecordingLLM
from search import (
    MENSAGEM_SEM_CONTEXTO,
    PROMPT_TEMPLATE,
    SearchError,
    search_prompt,
)

CHUNKS = [f"trecho numero {indice}" for indice in range(12)]


class FalhaDaOpenAI(Exception):
    """Exceção com o módulo de origem do SDK, como as do provedor real."""


FalhaDaOpenAI.__module__ = "openai"


def montar_cadeia(settings, conteudos=CHUNKS, erro=None, erro_llm=None):
    store = FakeVectorStore(conteudos, erro=erro)
    llm = RecordingLLM(erro=erro_llm)
    return search_prompt(settings=settings, store=store, llm=llm), store, llm


def test_busca_usa_similarity_search_with_score_com_k_10(settings):
    """AC-3: a consulta vetorial roda com a pergunta recebida e k=10."""
    cadeia, store, _ = montar_cadeia(settings)

    cadeia.invoke("qual o faturamento?")

    assert store.consultas == [("qual o faturamento?", 10)]


def test_contexto_concatena_os_chunks_na_ordem_de_relevancia(settings):
    """AC-4: o CONTEXTO traz os dez primeiros chunks, na ordem devolvida."""
    cadeia, _, llm = montar_cadeia(settings)

    cadeia.invoke("pergunta")

    contexto = llm.prompts[0].split("CONTEXTO:")[1].split("REGRAS:")[0]
    assert contexto.strip() == "\n\n".join(CHUNKS[:10])


def test_prompt_reproduz_o_texto_obrigatorio(settings):
    """AC-5: o prompt enviado é o template obrigatório, sem alterações."""
    cadeia, _, llm = montar_cadeia(settings)

    cadeia.invoke("qual o faturamento?")

    esperado = PROMPT_TEMPLATE.format(
        contexto="\n\n".join(CHUNKS[:10]), pergunta="qual o faturamento?"
    )
    assert llm.prompts[0] == esperado


def test_encadeamento_e_reutilizado_em_varias_perguntas(settings):
    """AC-6: uma única construção atende perguntas sucessivas."""
    cadeia, store, llm = montar_cadeia(settings)

    primeira = cadeia.invoke("primeira pergunta")
    segunda = cadeia.invoke("segunda pergunta")

    assert primeira == segunda == "resposta da LLM"
    assert [pergunta for pergunta, _k in store.consultas] == [
        "primeira pergunta",
        "segunda pergunta",
    ]
    assert "primeira pergunta" in llm.prompts[0]
    assert "segunda pergunta" in llm.prompts[1]


def test_menos_de_dez_chunks_usa_os_disponiveis(settings):
    """Assumption: com poucos chunks, o contexto traz apenas o que existe."""
    cadeia, _, llm = montar_cadeia(settings, conteudos=["unico trecho"])

    cadeia.invoke("pergunta")

    contexto = llm.prompts[0].split("CONTEXTO:")[1].split("REGRAS:")[0]
    assert contexto.strip() == "unico trecho"


def test_collection_vazia_responde_a_mensagem_de_insuficiencia(settings):
    """AC-7: sem chunks recuperados, a LLM nem é chamada."""
    cadeia, _, llm = montar_cadeia(settings, conteudos=[])

    resposta = cadeia.invoke("qual o faturamento?")

    assert resposta == "Não tenho informações necessárias para responder sua pergunta."
    assert resposta == MENSAGEM_SEM_CONTEXTO
    assert llm.prompts == []


def test_dimensao_incompativel_falha_com_mensagem_clara(settings):
    """Edge case: modelo de consulta incompatível com a collection."""
    erro = Exception("different vector dimensions 8 and 1536")
    cadeia, _, _ = montar_cadeia(settings, erro=erro)

    with pytest.raises(SearchError) as falha:
        cadeia.invoke("pergunta")

    assert "Remova a collection ou o volume" in str(falha.value)


def test_falha_de_banco_na_consulta_vira_mensagem_clara(settings):
    """Edge case: collection inacessível interrompe com mensagem explicativa."""
    erro = Exception("connection refused\nlinha de detalhe")
    cadeia, _, _ = montar_cadeia(settings, erro=erro)

    with pytest.raises(SearchError) as falha:
        cadeia.invoke("pergunta")

    assert "Falha ao consultar a collection" in str(falha.value)
    assert "linha de detalhe" not in str(falha.value)


def test_falha_de_embedding_nao_e_atribuida_ao_banco(settings):
    """Edge case: erro da OpenAI ao vetorizar aponta para a OpenAI, não para o banco."""
    erro = FalhaDaOpenAI("Error code: 401 - Incorrect API key provided")
    cadeia, _, _ = montar_cadeia(settings, erro=erro)

    with pytest.raises(SearchError) as falha:
        cadeia.invoke("pergunta")

    assert "Não foi possível vetorizar a pergunta na OpenAI" in str(falha.value)
    assert "OPENAI_EMBEDDING_MODEL" in str(falha.value)
    assert "collection" not in str(falha.value)


def test_falha_da_llm_vira_mensagem_clara(settings):
    """Edge case: erro do provedor na geração interrompe com texto legível."""
    erro = Exception(
        "Error code: 404 - modelo inexistente\nframe interno do provedor"
    )
    cadeia, _, _ = montar_cadeia(settings, erro_llm=erro)

    with pytest.raises(SearchError) as falha:
        cadeia.invoke("pergunta")

    assert "Não foi possível gerar a resposta com a LLM" in str(falha.value)
    assert "OPENAI_LLM_MODEL" in str(falha.value)
    assert "frame interno do provedor" not in str(falha.value)


def test_erro_sem_mensagem_ainda_produz_texto_legivel(settings):
    """Regressão: exceção vazia não pode quebrar a tradução do erro."""
    cadeia, _, _ = montar_cadeia(settings, erro=RuntimeError())

    with pytest.raises(SearchError) as falha:
        cadeia.invoke("pergunta")

    assert "Falha ao consultar a collection" in str(falha.value)
    assert "RuntimeError()" in str(falha.value)
