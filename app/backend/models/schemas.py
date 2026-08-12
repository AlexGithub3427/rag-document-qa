from pydantic import BaseModel

class Chunk(BaseModel):
    text: str
    header_path: str


class DocUploadResponse(BaseModel):
    message: str
    document_id: str
    document_title: str


class QueryRequest(BaseModel):
    question: str
    document_id: str


class QueryResponse(BaseModel):
    answer: str
    chunks: list[Chunk]