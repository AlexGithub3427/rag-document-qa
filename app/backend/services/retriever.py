import uuid

from chromadb.api.models.Collection import Collection
from langchain_core.documents import Document

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.schemas import Chunk
from models.db import Document, DocumentCreate, ChatMessage, ChatMessageCreate, Role

async def store_document(title: str, text_chunks: list[Document], embeddings: list[list[float]], collection: Collection, session: AsyncSession) -> uuid.UUID:
    document_id = str(uuid.uuid4())

    ids = [f"{document_id}_chunk_{i}" for i in range(len(text_chunks))]
    documents = [chunk.page_content for chunk in text_chunks]
    metadatas = [{**chunk.metadata, "title": title, "document_id": str(document_id)} for chunk in text_chunks]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

    document = DocumentCreate(id=document_id, title=title)
    db_document = Document(**document.model_dump())
    session.add(db_document)
    await session.commit()
    # session.refresh(db_document)

    return document_id

async def store_chat_exchange(question: str, document_id: str, retrieved_chunks: list[Chunk], answer: str, session: AsyncSession) -> None:
    user_message = ChatMessageCreate(document_id=document_id, role=Role.USER, content=question)
    db_user_message = ChatMessage(**user_message.model_dump())
    session.add(db_user_message)
    await session.commit()

    citations = {index: chunk.model_dump() for index, chunk in enumerate(retrieved_chunks)}
    assistant_message = ChatMessageCreate(document_id=document_id, role=Role.ASSISTANT, content=answer, citations=citations)
    db_assistant_message = ChatMessage(**assistant_message.model_dump())

    session.add(db_assistant_message)
    await session.commit()

     
def search(document_id: str, embedding: list[float], collection: Collection, session: AsyncSession, n_results: int = 5) -> tuple[list[Chunk], str]:
    query_result = collection.query(
        query_embeddings=[embedding],
        n_results=5,
        where={"document_id": document_id}
    )

    # retrieve from DB in future with session

    retrieved_chunks = [
        Chunk(text=text, header_path=metadata["header_path"])
        for text, metadata in zip(query_result["documents"][0], query_result["metadatas"][0])
    ]

    title = query_result["metadatas"][0][0]["title"]

    return retrieved_chunks, title

async def retrieve_all_documents(session: AsyncSession) -> list[tuple[str, str]]:
    stmt = select(Document)
    result = await session.execute(stmt)
    documents = result.scalars().all()

    document_ids = [d.id for d in documents]
    document_titles = [d.title for d in documents]

    return list(zip(document_ids, document_titles))

async def retrieve_document_history(document_id: str, session: AsyncSession) -> list[tuple[Role, str, dict]]:
    stmt = select(ChatMessage).where(ChatMessage.document_id == document_id).order_by(ChatMessage.id)
    result = await session.execute(stmt)
    chat_messages = result.scalars().all()

    role_list = [cm.role for cm in chat_messages]
    content_list = [cm.content for cm in chat_messages]
    citations_list = [cm.citations for cm in chat_messages]

    return list(zip(role_list, content_list, citations_list))

