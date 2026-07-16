import os
import chromadb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import documents, query
from contextlib import asynccontextmanager
from openai import OpenAI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # -- Startup --
    app.state.chroma = chromadb.PersistentClient(path="./chroma")
    app.state.collection = app.state.chroma.get_or_create_collection("documents")
    app.state.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    yield
    # -- Shutdown --
    

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], #placeholder
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(query.router)


