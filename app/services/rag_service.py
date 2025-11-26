import shutil
import uuid
from langchain_community.document_loaders import GitLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI


from app.database.entities import Repositories, ChatHistory, ChatRole
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select


from app.core.config import  GOOGLE_API_KEY
from app.prompt.rag_prompt import output_parser, question_rewrite_template, final_answer_template

from app.database.chroma_connection import get_chroma_client


embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

async def load_repo_and_index(
        name: str,
        description: str | None,
        repo_url: str,
        session: AsyncSession,
        branch: str = "main",
        ) -> dict:
    loader = GitLoader(
        clone_url=repo_url,
        repo_path="./temp_clone",
        branch=branch
    )
    docs = loader.load()
  
    try:
        shutil.rmtree("./temp_clone")
    except:
        pass

    splitter = RecursiveCharacterTextSplitter.from_language(
        language="java",
        chunk_size=3000,
        chunk_overlap=300
    )
    chunks = splitter.split_documents(docs)
    
    for ch in chunks:
        meta = ch.metadata
        ch.metadata = {
            "source": meta.get("source") or meta.get("file_path") or "unknown",
            "path": meta.get("file_path") or meta.get("source") or "unknown",
        }   

    client = get_chroma_client()

    # Create or get collection with repo name
    collection_name = name.lower().replace(" ", "_")

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": description, "github_url": repo_url}
    )

    ids = [f"{collection_name}_{uuid.uuid4()}" for _ in range(len(chunks))]

    documents = [c.page_content for c in chunks]
    metadatas = [c.metadata for c in chunks]

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    repository=Repositories(
        name=name,
        description=description,
        github_url=repo_url

    )
    session.add(repository)
    await session.commit()
    await session.refresh(repository)  

    return {
        "repo_id": repository.id,
        "name": repository.name,
        "message": "Repository indexed and saved successfully"
    }



async def ask_question(
        question: str,
        repo_id: str,
        repo_name: str,
         session: AsyncSession
         ) -> dict:
    


    # Get Chroma Cloud client
    client = get_chroma_client()
    collection_name = repo_name.lower().replace(" ", "_")
    collection = client.get_collection(name=collection_name)

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",api_key=GOOGLE_API_KEY)

    rewritten_q = output_parser.invoke(
        llm.invoke(
            question_rewrite_template.format(question=question)
        )
    )

    embedded_q = embedding_model.embed_query(rewritten_q)

    # Query the collection
    results = collection.query(
        query_embeddings=[embedded_q],
        n_results=7
    )

    # Extract documents from results
    context_text = " ".join(results["documents"][0]) if results["documents"] else ""

    

    

    final_answer = output_parser.invoke(
        llm.invoke(
            final_answer_template.format(context=context_text, question=question)
        )
    )
    user_chat = ChatHistory(
        repo_id=repo_id,
        role=ChatRole.user,
        message=question
    )
    session.add(user_chat)

    ai_chat=ChatHistory(
        repo_id=repo_id,
        role=ChatRole.ai,
        message=final_answer
    )
    session.add(ai_chat)
    
    await session.commit()

    return {
        "rewritten_question":rewritten_q,
        "answer": final_answer
    }


async def get_chat_history(repo_id: str, session: AsyncSession) -> list:
    """Retrieve all chat history for a repository"""
    stmt = select(ChatHistory).where(ChatHistory.repo_id == repo_id).order_by(ChatHistory.created_at)
    result = await session.execute(stmt)
    chats = result.scalars().all()
    
    return [
        {
            "id": chat.id,
            "role": chat.role.value,
            "message": chat.message,
            "created_at": chat.created_at.isoformat()
        }
        for chat in chats
    ]

