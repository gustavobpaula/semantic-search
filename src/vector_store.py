"""Construção dos clientes de embeddings e da collection pgVector."""

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from config import Settings


def build_embeddings(settings: Settings) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=settings.embedding_model)


def build_vector_store(settings: Settings, embeddings: OpenAIEmbeddings) -> PGVector:
    return PGVector(
        embeddings=embeddings,
        collection_name=settings.collection_name,
        connection=settings.database_url,
        use_jsonb=True,
    )
