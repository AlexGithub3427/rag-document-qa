from fastapi import APIRouter, Request
from pydantic import BaseModel

from services.embedder import embed_single
from services.retriever import search
from services.llm import generate

router = APIRouter(
    prefix="/query",
    tags=["Query"]
)

# define a QueryRequest Pydantic model:
class QueryRequest(BaseModel):
    question: str


# accepts Query Request body
@router.post("/")
async def handle_query(request: Request, body: QueryRequest):
    # pass request
    collection = request.app.state.collection
    openai_client = request.app.state.openai_client

    # embeds the question via embedder.embed single()
    embedding = embed_single(body.question, openai_client)

    # queries Chroma for top 5 chunks via retriever.search()
    retrieved_chunks = search(embedding, collection)

    # calls llm.generate(question, context)
    answer = generate(body.question, retrieved_chunks["documents"], openai_client)

    # returns {"answer": answer, "sources": chunks}
    return {"answer": answer, "sources": retrieved_chunks}