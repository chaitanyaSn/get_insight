from fastapi import FastAPI
from app.api import rag

app = FastAPI(title="RAG GitHub Analyzer API")

app.include_router(rag.router)
