from pydantic import BaseModel
from chromadb.api.models.Collection import Collection
from langchain_core.documents import Document

from models.schemas import Chunk


def store(text_chunks: list[Document], embeddings: list[list[float]], collection: Collection) -> None:
    ids = [f"chunk_{i}" for i in range(len(text_chunks))]
    documents = [chunk.page_content for chunk in text_chunks]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents
    )


#     
def search(embedding: list[float], collection: Collection, n_results: int = 5) -> list[Chunk]:
    query_result = collection.query(
        query_embeddings=[embedding],
        n_results=5
    )

    retrieved_chunks = [
        Chunk(text=text) for text in query_result["documents"][0]
    ]

    return retrieved_chunks