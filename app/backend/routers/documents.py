from typing import Annotated
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Request

from services.pdf_processor import pdf_to_markdown
from services.chunker import split_markdown
from services.embedder import embed_chunks
from services.retriever import store

from models.schemas import DocUploadResponse

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

MAX_FILE_SIZE = 1 # currently unused
ALLOWED_MIME_TYPES = {"application/pdf"}

# Notes:
# - currently does not validate file size
@router.post("/", response_model=DocUploadResponse)
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

    # from file bytes, extract pdf title and markdown string
    title, markdown_string = pdf_to_markdown(file_bytes)

    # pass markdown string into 
    text_chunks = split_markdown(markdown_string)

    # passes chunks to embedder.embed()
    embeddings = embed_chunks(text_chunks, openai_client)

    # stores results in Chroma via retriever.store()
    document_id = str(store(title, text_chunks, embeddings, collection))

    # returns {"message": "success", "chunks": len(chunks)}
    return DocUploadResponse(
        message="success",
        document_id=document_id,
        document_title=title
    )