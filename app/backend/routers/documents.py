from typing import Annotated
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Request

from services.pdf_processor import extract_text
from services.chunker import split_text
from services.embedder import embed_chunks
from services.retriever import store

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

MAX_FILE_SIZE = 1
ALLOWED_MIME_TYPES = {"application/pdf"}

# Notes:
# - currently does not validate file size
@router.post("/")
async def upload_document(request: Request, file: UploadFile = File(...)):
    # accepts an uploaded file (PDF)
    # - validate it is pdf 
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Allowed types: PDF."
        )
    
    # pass request
    collection = request.app.state.collection
    openai_client = request.app.state.openai_client

    # read file bytes
    file_bytes = await file.read()

    # passes bytes to pdf_processor.extract_text()
    file_text = extract_text(file_bytes)

    # passes text to chunker.split()
    text_chunks = split_text(file_text)

    # passes chunks to embedder.embed()
    embeddings = embed_chunks(text_chunks, openai_client)

    # stores results in Chroma via retriever.store()
    store(text_chunks, embeddings, collection)

    # returns {"message": "success", "chunks": len(chunks)}
    return {"message": "success", "chunks": len(text_chunks)}