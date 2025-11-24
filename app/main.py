from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import rag
from app.database.entities import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    print("Creating database tables...")
    await create_db_and_tables()
    print("Database tables created successfully!")
    yield
    # Shutdown (optional cleanup here if needed)
    print("Application shutting down...")


app = FastAPI(
    title="RAG GitHub Analyzer API",
    lifespan=lifespan
)

app.include_router(rag.router)