from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel

from services.embedder import embed_question
from services.retriever import search, store_chat_exchange
from services.llm import generate

from models.schemas import QueryRequest, QueryResponse
from models.db import SessionDep

router = APIRouter(
    prefix="/query",
    tags=["Query"]
)


# accepts Query Request body
@router.post("/", response_model=QueryResponse)
async def handle_query(request: Request, body: QueryRequest, session: SessionDep):
    # pass request
    collection = request.app.state.collection
    openai_client = request.app.state.openai_client

    # embed the question
    embedding = embed_question(body.question, openai_client)

    # queries Chroma for top 5 chunks
    retrieved_chunks, document_title = search(body.document_id, embedding, collection, session)

    # calls llm.generate(question, context)
    answer = generate(body.question, document_title, retrieved_chunks, openai_client)

    # store chat exchange
    await store_chat_exchange(body.question, body.document_id, retrieved_chunks, answer, session)

    # returns QueryResponse of answer and retrieved chunks
    return QueryResponse(
        answer=answer,
        chunks=retrieved_chunks
    )