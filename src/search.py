"""Recuperação semântica: contexto, prompt obrigatório e chamada à LLM."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda

from config import Settings, load_settings
from vector_store import (
    DICA_DE_DIMENSAO,
    build_embeddings,
    build_llm,
    connect_vector_store,
    primeira_linha,
)

PROMPT_TEMPLATE = """
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
"""

K = 10

MENSAGEM_SEM_CONTEXTO = "Não tenho informações necessárias para responder sua pergunta."

MENSAGEM_DE_EMBEDDING = (
    "Não foi possível vetorizar a pergunta na OpenAI. Verifique OPENAI_API_KEY e "
    "OPENAI_EMBEDDING_MODEL no .env e a conexão com a OpenAI."
)

MENSAGEM_DE_GERACAO = (
    "Não foi possível gerar a resposta com a LLM. Verifique OPENAI_API_KEY e "
    "OPENAI_LLM_MODEL no .env e a conexão com a OpenAI."
)


class SearchError(Exception):
    """Falha impeditiva durante a recuperação semântica."""


def formatar_contexto(resultados) -> str:
    """Concatena os chunks na ordem de relevância devolvida pela busca."""
    return "\n\n".join(documento.page_content for documento, _score in resultados)


def e_falha_da_openai(error: Exception) -> bool:
    """Distingue uma falha do provedor de uma falha do banco.

    Uma única chamada da store vetoriza a pergunta na OpenAI e consulta a
    collection, então o módulo de origem da exceção é o que separa as duas
    causas antes de escolher a mensagem.
    """
    return type(error).__module__.startswith(("openai", "langchain_openai"))


def recuperar_contexto(store, pergunta: str) -> str:
    """Vetoriza a pergunta na store e devolve o contexto dos `K` vizinhos."""
    try:
        resultados = store.similarity_search_with_score(pergunta, k=K)
    except Exception as error:
        if "dimension" in str(error).lower():
            raise SearchError(
                f"{DICA_DE_DIMENSAO}\nDetalhe: {primeira_linha(error)}"
            ) from error
        if e_falha_da_openai(error):
            raise SearchError(
                f"{MENSAGEM_DE_EMBEDDING}\nDetalhe: {primeira_linha(error)}"
            ) from error
        raise SearchError(
            f"Falha ao consultar a collection: {primeira_linha(error)}"
        ) from error

    return formatar_contexto(resultados)


def gerar_resposta(cadeia_llm, contexto: str, pergunta: str) -> str:
    """Chama a LLM, traduzindo falhas do provedor em mensagem clara.

    Chave inválida, modelo inexistente, cota e rede chegam aqui como
    exceções da integração; sem esta tradução elas subiriam cruas até o
    terminal.
    """
    try:
        return cadeia_llm.invoke({"contexto": contexto, "pergunta": pergunta})
    except Exception as error:
        raise SearchError(
            f"{MENSAGEM_DE_GERACAO}\nDetalhe: {primeira_linha(error)}"
        ) from error


def search_prompt(
    settings: Settings | None = None, store=None, llm=None
) -> Runnable:
    """Monta o encadeamento reutilizável que responde a uma pergunta.

    Store, prompt e LLM são construídos uma única vez; o encadeamento
    devolvido aceita a pergunta e produz a resposta da LLM.
    """
    settings = settings or load_settings()

    if store is None:
        store = connect_vector_store(settings, build_embeddings(settings), SearchError)

    llm = llm if llm is not None else build_llm(settings)
    cadeia_llm = PromptTemplate.from_template(PROMPT_TEMPLATE) | llm | StrOutputParser()

    def responder(pergunta: str) -> str:
        contexto = recuperar_contexto(store, pergunta)
        if not contexto.strip():
            return MENSAGEM_SEM_CONTEXTO
        return gerar_resposta(cadeia_llm, contexto, pergunta)

    return RunnableLambda(responder)
