from openai import OpenAI

def embed_chunks(chunks: list[str], client: OpenAI) -> list[list[float]]:
    embeddings_list = []

    for chunk in chunks:
        response = client.embeddings.create(
            input=chunk,
            model="text-embedding-3-small"
        )
        embeddings_list.append(response.data[0].embedding)
    
    return embeddings_list

def embed_single(text: str, client: OpenAI) -> list[float]:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding
    