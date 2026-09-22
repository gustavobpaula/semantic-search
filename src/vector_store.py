"""Construção dos clientes OpenAI e da collection pgVector.

Ingestão e busca compartilham este ponto de construção para não abrirem
caminhos paralelos até a OpenAI ou o pgVector.
"""

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

from config import Settings

DICA_DE_DIMENSAO = (
    "A collection já contém vetores de outra dimensão, gerados por um modelo de "
    "embeddings diferente. Remova a collection ou o volume do banco e refaça a "
    "ingestão."
)

MENSAGEM_DE_CONEXAO = (
    "Não foi possível conectar ao PostgreSQL. Verifique DATABASE_URL no .env e "
    "se o banco está no ar (`docker compose up -d`)."
)


def primeira_linha(error: Exception) -> str:
    """Resumo legível do erro; a causa completa segue encadeada na exceção.

    Exceções sem mensagem caem no `repr`, para que a tradução do erro nunca
    substitua a explicação por uma falha no próprio helper.
    """
    linhas = str(error).splitlines()
    return linhas[0] if linhas else repr(error)


def build_embeddings(settings: Settings) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=settings.embedding_model)


def build_llm(settings: Settings) -> ChatOpenAI:
    return ChatOpenAI(model=settings.llm_model)


def build_vector_store(settings: Settings, embeddings: OpenAIEmbeddings) -> PGVector:
    return PGVector(
        embeddings=embeddings,
        collection_name=settings.collection_name,
        connection=settings.database_url,
        use_jsonb=True,
    )


def connect_vector_store(
    settings: Settings, embeddings: OpenAIEmbeddings, error_class: type[Exception]
) -> PGVector:
    """Conecta na collection, traduzindo falhas de banco em mensagem clara.

    Ingestão e busca compartilham a tradução e informam apenas o tipo de erro
    da própria capacidade.
    """
    try:
        return build_vector_store(settings, embeddings)
    except Exception as error:
        raise error_class(
            f"{MENSAGEM_DE_CONEXAO}\nDetalhe: {primeira_linha(error)}"
        ) from error
