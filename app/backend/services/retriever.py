from chromadb.api.models.Collection import Collection
from chromadb.api.types import QueryResult

def store(text_chunks: list[str], embeddings: list[list[float]], collection: Collection) -> None:
    ids = [f"chunk_{i}" for i in range(len(text_chunks))]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=text_chunks
    )


# function search(query_embedding, collection, n_results=3):
#     call collection.query(query_embeddings, n_results)
#     return retrieved documents list
def search(embedding: list[float], collection: Collection, n_results: int = 5) -> QueryResult:
    return collection.query(
        query_embeddings=[embedding],
        n_results=5
    )