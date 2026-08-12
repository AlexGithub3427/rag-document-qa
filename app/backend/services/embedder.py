from openai import OpenAI
from langchain_core.documents import Document


def embed_chunks(chunks: list[Document], client: OpenAI) -> list[list[float]]:
    embeddings_list = []

    for chunk in chunks:        
        input = f"{chunk.metadata["header_path"]}\n{chunk.page_content}"

        response = client.embeddings.create(
            input=input,
            model="text-embedding-3-small"
        )
        embeddings_list.append(response.data[0].embedding)

    return embeddings_list

def embed_question(question: str, client: OpenAI) -> list[float]:
    response = client.embeddings.create(
        input=question,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding
    