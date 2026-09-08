from openai import OpenAI

from sqlalchemy.ext.asyncio import AsyncSession

from services.prompts import build_context_string, build_rag_prompt
from services.retriever import store_chat_exchange

from models.schemas import Chunk

 
def generate(question: str, document_title: str, retrieved_chunks: list[Chunk], client: OpenAI) -> str:
    """
    Generates AI response to user submitted question

    Parameters:
    ** question: Question submitted by the user
    ** document_title: Title of the corresponding document
    ** retrieved_chunks: List of chunks retrieved by search function supplying document context
    ** session: DB asyncronous session to store the question-response
    ** client: client object to call AI API

    Returns:
    str: The AI generated response to the user question 
    """
    context = build_context_string(retrieved_chunks)
    system_prompt = build_rag_prompt(question, document_title, context)
    response = client.responses.create(
        model="gpt-4o-mini",
        input=system_prompt
    )
    answer = response.output_text

    return answer
