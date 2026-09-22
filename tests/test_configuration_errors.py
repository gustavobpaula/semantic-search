"""AC-5 e edge cases: configuração externa e falhas com mensagem clara."""

import pytest

import ingest
from config import ConfigError, load_settings

AMBIENTE_COMPLETO = {
    "OPENAI_API_KEY": "chave-secreta-de-teste",
    "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
    "DATABASE_URL": "postgresql+psycopg://postgres:postgres@localhost:5432/rag",
    "PG_VECTOR_COLLECTION_NAME": "document_embeddings",
    "PDF_PATH": "document.pdf",
}


def test_configuracao_completa_produz_settings():
    settings = load_settings(env=dict(AMBIENTE_COMPLETO))

    assert settings.pdf_path == "document.pdf"
    assert settings.collection_name == "document_embeddings"
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.database_url == AMBIENTE_COMPLETO["DATABASE_URL"]


@pytest.mark.parametrize("variavel", sorted(AMBIENTE_COMPLETO))
def test_variavel_obrigatoria_ausente_falha_nomeando_a_variavel(variavel):
    ambiente = dict(AMBIENTE_COMPLETO)
    del ambiente[variavel]

    with pytest.raises(ConfigError) as erro:
        load_settings(env=ambiente)

    assert variavel in str(erro.value)


def test_variavel_em_branco_e_tratada_como_ausente():
    ambiente = dict(AMBIENTE_COMPLETO, PG_VECTOR_COLLECTION_NAME="   ")

    with pytest.raises(ConfigError) as erro:
        load_settings(env=ambiente)

    assert "PG_VECTOR_COLLECTION_NAME" in str(erro.value)


def test_a_chave_da_openai_nao_e_exposta():
    settings = load_settings(env=dict(AMBIENTE_COMPLETO))

    assert "chave-secreta-de-teste" not in repr(settings)


def test_pdf_de_amostra_e_legivel(pdf_de_amostra):
    documentos = ingest.load_documents(str(pdf_de_amostra))

    assert len(documentos) == 3
    assert documentos[0].page_content.startswith("pagina0palavra0")


def test_pdf_ausente_falha_com_mensagem_clara(tmp_path):
    caminho = tmp_path / "inexistente.pdf"

    with pytest.raises(ingest.IngestionError) as erro:
        ingest.load_documents(str(caminho))

    assert "PDF não encontrado" in str(erro.value)


def test_pdf_ilegivel_falha_com_mensagem_clara(tmp_path):
    caminho = tmp_path / "corrompido.pdf"
    caminho.write_bytes(b"isto nao e um pdf")

    with pytest.raises(ingest.IngestionError) as erro:
        ingest.load_documents(str(caminho))

    assert "Não foi possível ler o PDF" in str(erro.value)
