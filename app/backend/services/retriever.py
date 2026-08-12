import uuid

from chromadb.api.models.Collection import Collection
from langchain_core.documents import Document

from models.schemas import Chunk


def store(title: str, text_chunks: list[Document], embeddings: list[list[float]], collection: Collection) -> uuid.UUID:
    document_id = uuid.uuid4()

    ids = [f"{document_id}_chunk_{i}" for i in range(len(text_chunks))]
    documents = [chunk.page_content for chunk in text_chunks]
    metadatas = [{**chunk.metadata, "title": title, "document_id": str(document_id)} for chunk in text_chunks]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

    return document_id

     
def search(document_id: str, embedding: list[float], collection: Collection, n_results: int = 5) -> tuple[list[Chunk], str]:
    query_result = collection.query(
        query_embeddings=[embedding],
        n_results=5,
        where={"document_id": document_id}
    )

    retrieved_chunks = [
        Chunk(text=text, header_path=metadata["header_path"])
        for text, metadata in zip(query_result["documents"][0], query_result["metadatas"][0])
    ]

    title = query_result["metadatas"][0][0]["title"]

    return retrieved_chunks, title