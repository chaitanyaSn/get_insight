from fastapi import APIRouter, HTTPException
from app.services.rag_service import load_repo_and_index, ask_question
from pydantic import BaseModel

router = APIRouter()

class RepoRequest(BaseModel):
    repo_url: str
    branch: str = "main"

class QueryRequest(BaseModel):
    question: str

@router.post("/load_repo")
async def load_repo(request: RepoRequest):
    try:
        load_repo_and_index(request.repo_url, request.branch)
        return {"status": "success", "message": "Repository indexed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask")
async def ask(req: QueryRequest):
    try:
        result = ask_question(req.question)
        return {"status": "success", **result}
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
