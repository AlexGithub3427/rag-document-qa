from pydantic import BaseModel

from models.db import Role, Chunk


class DocUploadResponse(BaseModel):
    message: str
    id: str
    title: str

class DocRetrievalResponse(BaseModel):
    ids: list[str]
    titles: list[str]

class DocHistoryRetrievalResponse(BaseModel):
    role_list: list[Role]
    content_list: list[str]
    citations_list: list[list[Chunk] | None]


class QueryRequest(BaseModel):
    question: str
    document_id: str

class QueryResponse(BaseModel):
    answer: str
    chunks: list[Chunk]
