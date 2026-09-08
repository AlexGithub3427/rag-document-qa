import os
import asyncio

from datetime import datetime, timezone
from typing import Optional, Annotated
from enum import StrEnum

from fastapi import Depends, Request

from sqlalchemy import Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import Field, SQLModel, JSON, Column

from dotenv import load_dotenv
load_dotenv()

class DocumentBase(SQLModel):
    id: str = Field(primary_key=True)
    title: str

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase, table=True):
    __tablename__ = "documents"

    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    

class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"

class Chunk(SQLModel):
    text: str
    header_path: str

class ChatMessageBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: str = Field(foreign_key="documents.id")
    role: Role
    content: str = Field(sa_type=Text)
    citations: Optional[list[Chunk]] = Field(default=None, sa_type=JSON)

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase, table=True):
    __tablename__ = "chat_messages"

    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT")
db = os.getenv("POSTGRES_DB")

postgres_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

engine = create_async_engine(
    postgres_url,
    echo=True
)

async def delete_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def main():
    await delete_db_and_tables()
    await create_db_and_tables()


if __name__ == "__main__":
    asyncio.run(main())




async def get_session(request: Request):
    async with AsyncSession(request.app.state.engine) as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]