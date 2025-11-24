import shutil
import os
from langchain_community.document_loaders import GitLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI


from app.database.entities import Repositories, ChatHistory, ChatRole
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select


from app.core.config import EMBED_MODEL, FAISS_INDEX_PATH, GOOGLE_API_KEY
from app.prompt.rag_prompt import output_parser, question_rewrite_template, final_answer_template




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
    # Remove temp clone
    try:
        shutil.rmtree("./temp_clone")
    except:
        pass

    splitter = RecursiveCharacterTextSplitter.from_language(
        language="java",
        chunk_size=2000,
        chunk_overlap=400
    )
    chunks = splitter.split_documents(docs)

    for ch in chunks:
        ch.metadata["source"] = ch.metadata.get("source", "unknown_file")
        ch.metadata["path"] = ch.metadata.get("file_path", "unknown_path")

    embeddings = HuggingFaceEmbeddings(
        model=EMBED_MODEL,
        model_kwargs={"trust_remote_code": True}
    )

    vectorstore = FAISS.from_documents(chunks, embeddings)

    if os.path.exists(FAISS_INDEX_PATH):
        shutil.rmtree(FAISS_INDEX_PATH)

    vectorstore.save_local(FAISS_INDEX_PATH)

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
         session: AsyncSession
         ) -> dict:
    if not os.path.exists(FAISS_INDEX_PATH):
        raise FileNotFoundError("Index not found. Load a repo first.")

    embeddings = HuggingFaceEmbeddings(
        model=EMBED_MODEL,
        model_kwargs={"trust_remote_code": True}
    )
    vectorstore = FAISS.load_local(
        FAISS_INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 7})

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",api_key=GOOGLE_API_KEY)

    rewritten_q = output_parser.invoke(
        llm.invoke(
            question_rewrite_template.format(question=question)
        )
    )
    docs = retriever.invoke(rewritten_q)
    context_text = " ".join([doc.page_content for doc in docs])

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

