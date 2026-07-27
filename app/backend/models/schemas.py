from pydantic import BaseModel


class DocUploadResponse(BaseModel):
    message: str
    chunk_count: int


class QueryRequest(BaseModel):
    question: str

class Chunk(BaseModel):
    text: str

class QueryResponse(BaseModel):
    answer: str
    chunks: list[Chunk]