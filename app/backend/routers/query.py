from fastapi import APIRouter, Request
from pydantic import BaseModel

from services.embedder import embed_question
from services.retriever import search
from services.llm import generate

from models.schemas import QueryRequest, QueryResponse

router = APIRouter(
    prefix="/query",
    tags=["Query"]
)


# accepts Query Request body
@router.post("/", response_model=QueryResponse)
async def handle_query(request: Request, body: QueryRequest):
    # pass request
    collection = request.app.state.collection
    openai_client = request.app.state.openai_client

    # embed the question
    embedding = embed_question(body.question, openai_client)

    # queries Chroma for top 5 chunks
    retrieved_chunks, document_title = search(body.document_id, embedding, collection)

    # calls llm.generate(question, context)
    answer = generate(body.question, document_title, retrieved_chunks, openai_client)

    # returns QueryResponse of answer and retrieved chunks
    return QueryResponse(
        answer=answer,
        chunks=retrieved_chunks
    )