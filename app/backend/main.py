import os
import chromadb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import documents, query
from contextlib import asynccontextmanager
from openai import OpenAI

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

from engine.json_serializer import custom_serializer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # -- Startup --
    app.state.chroma = chromadb.PersistentClient(path="./chroma")
    app.state.collection = app.state.chroma.get_or_create_collection("documents")

    load_dotenv()
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    db = os.getenv("POSTGRES_DB")
    postgres_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    app.state.engine = create_async_engine(
        postgres_url,
        echo=True,
        json_serializer=custom_serializer,
        pool_size=5,
        max_overflow=5,
        pool_recycle=1800
    )

    app.state.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    yield

    await app.state.engine.dispose()
    # -- Shutdown --
    

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(query.router)


