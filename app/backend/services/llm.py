from openai import OpenAI
from chromadb.api.types import Document

from services.prompts import build_context_string, build_rag_prompt
from models.schemas import Chunk

# function generate(question, context):
#     build prompt string with context and question
#     call client.responses.create(model, input=prompt)
#     return response.output_text
def generate(question: str, retrieved_chunks: list[Chunk], client: OpenAI) -> str:
    retrieved_chunks_text = [chunk.text for chunk in retrieved_chunks]
    context = build_context_string(retrieved_chunks_text)
    system_prompt = build_rag_prompt(question, context)
    response = client.responses.create(
        model="gpt-4o-mini",
        input=system_prompt
    )

    return response.output_text
