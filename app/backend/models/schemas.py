from pydantic import BaseModel

from models.db import Role

class Chunk(BaseModel):
    text: str
    header_path: str


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
    citations_list: list[dict | None]


class QueryRequest(BaseModel):
    question: str
    document_id: str

class QueryResponse(BaseModel):
    answer: str
    chunks: list[Chunk]
