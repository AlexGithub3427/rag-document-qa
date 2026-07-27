from pydantic import BaseModel
from chromadb.api.models.Collection import Collection

from models.schemas import Chunk


def store(text_chunks: list[str], embeddings: list[list[float]], collection: Collection) -> None:
    ids = [f"chunk_{i}" for i in range(len(text_chunks))]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=text_chunks
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