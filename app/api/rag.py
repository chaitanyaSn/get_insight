from fastapi import APIRouter, HTTPException,Depends
from app.services.rag_service import load_repo_and_index, ask_question,get_chat_history
from app.database.entities import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

router = APIRouter()

class RepoRequest(BaseModel):
    name: str
    description: str | None = None
    repo_url: str
    branch: str = "main"

class QueryRequest(BaseModel):
    repo_id: str
    repo_name: str
    question: str

@router.post("/load_repo")
async def load_repo(
    request: RepoRequest,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        result = await load_repo_and_index(
            name=request.name,
            description=request.description,
            repo_url=request.repo_url,
            branch=request.branch,
            session=session
        )
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask")
async def ask(
    req: QueryRequest,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        result = await ask_question(
            question=req.question,
            repo_id=req.repo_id,
            repo_name=req.repo_name,
            session=session
        )
        return {"status": "success", **result}
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/chat_history/{repo_id}")
async def get_history(
    repo_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        history = await get_chat_history(repo_id, session)
        return {"status": "success", "chats": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))