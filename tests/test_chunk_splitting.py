"""AC-2: a divisão usa tamanho 1000 e overlap 150."""

from langchain_core.documents import Document

import ingest


def test_splitter_configurado_com_1000_e_150(monkeypatch):
    capturado = {}
    splitter_real = ingest.RecursiveCharacterTextSplitter

    def splitter_espiao(**kwargs):
        capturado.update(kwargs)
        return splitter_real(**kwargs)

    monkeypatch.setattr(ingest, "RecursiveCharacterTextSplitter", splitter_espiao)
    ingest.split_documents([Document(page_content="texto qualquer")])

    assert capturado["chunk_size"] == 1000
    assert capturado["chunk_overlap"] == 150


def test_nenhum_chunk_excede_o_tamanho_configurado():
    texto = " ".join(f"palavra{indice}" for indice in range(2000))

    chunks = ingest.split_documents([Document(page_content=texto)])

    assert len(chunks) > 1
    assert all(len(chunk.page_content) <= ingest.CHUNK_SIZE for chunk in chunks)


def _tamanho_da_sobreposicao(primeiro: str, segundo: str) -> int:
    """Maior sufixo do primeiro chunk que é prefixo do segundo."""
    for tamanho in range(min(len(primeiro), len(segundo)), 0, -1):
        if primeiro.endswith(segundo[:tamanho]):
            return tamanho
    return 0


def test_chunks_consecutivos_compartilham_o_overlap():
    texto = " ".join(f"palavra{indice}" for indice in range(2000))

    chunks = ingest.split_documents([Document(page_content=texto)])

    sobreposicao = _tamanho_da_sobreposicao(chunks[0].page_content, chunks[1].page_content)
    # O divisor respeita fronteiras de palavra, então a sobreposição fica logo
    # abaixo do overlap configurado, nunca acima dele nem ausente.
    assert 0 < sobreposicao <= ingest.CHUNK_OVERLAP
    assert sobreposicao > ingest.CHUNK_OVERLAP - 20


def test_chunks_vazios_sao_descartados():
    documentos = [
        Document(page_content="conteúdo real"),
        Document(page_content="   \n  "),
    ]

    chunks = ingest.split_documents(documentos)

    assert [chunk.page_content for chunk in chunks] == ["conteúdo real"]


def test_metadados_de_origem_sao_preservados():
    documentos = [Document(page_content="conteúdo", metadata={"page": 3})]

    chunks = ingest.split_documents(documentos)

    assert chunks[0].metadata["page"] == 3
