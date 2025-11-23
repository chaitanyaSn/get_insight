from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.document_loaders import GitLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import shutil
import os

app = FastAPI(title="RAG GitHub Analyzer API")

EMBED_MODEL = "nomic-ai/nomic-embed-text-v1"
FAISS_INDEX_PATH = "./faiss_index"
output_parser = StrOutputParser()


# ---------------------------
# 📌 Pydantic Models
# ---------------------------
class RepoRequest(BaseModel):
    repo_url: str
    branch: str = "main"


class QueryRequest(BaseModel):
    question: str


# ---------------------------
# 💡 API 1 — Load Repo
# ---------------------------
@app.post("/load_repo")
async def load_repo(request: RepoRequest):
    try:
        # 1. Load repo
        loader = GitLoader(
            clone_url=request.repo_url,
            repo_path="./temp_clone",
            branch=request.branch
        )

        docs = loader.load()

        # Remove clone folder
        try:
            shutil.rmtree("./temp_clone")
        except:
            pass

        # 2. Chunking
        splitter = RecursiveCharacterTextSplitter.from_language(
            language="java",
            chunk_size=2000,
            chunk_overlap=400
        )
        chunks = splitter.split_documents(docs)

        # Fix metadata
        for ch in chunks:
            ch.metadata["source"] = ch.metadata.get("source", "unknown_file")
            ch.metadata["path"] = ch.metadata.get("file_path", "unknown_path")

        # 3. Embeddings
        embeddings = HuggingFaceEmbeddings(
            model=EMBED_MODEL,
            model_kwargs={"trust_remote_code": True}
        )

        # 4. Create FAISS
        vectorstore = FAISS.from_documents(chunks, embeddings)

        # Delete old FAISS if exists
        if os.path.exists(FAISS_INDEX_PATH):
            shutil.rmtree(FAISS_INDEX_PATH)

        vectorstore.save_local(FAISS_INDEX_PATH)

        return {"status": "success", "message": "Repository indexed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# 💡 API 2 — Ask Question
# ---------------------------
@app.post("/ask")
async def ask_question(req: QueryRequest):
    question = req.question

    if not os.path.exists(FAISS_INDEX_PATH):
        raise HTTPException(status_code=400, detail="Index not found. Load a repo first.")

    # Load FAISS
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

    # LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

    # Step 1: Rewrite Question
    question_rewriter = PromptTemplate(
        template="""
You are an AI assistant responsible for rewriting user queries 
so they become clearer, more detailed, and optimized for code retrieval.

Rewrite the user's question to make it:
- more technical
- specific to filenames/modules if possible
- neutral and focused

Do NOT answer the question.

Original question:
{question}

Rewritten improved question:
""",
        input_variables=["question"]
    )

    rewrite_prompt = question_rewriter.format(question=question)
    rewritten_q = output_parser.invoke(llm.invoke(rewrite_prompt))

    # Step 2: Retrieve documents
    docs = retriever.invoke(rewritten_q)
    context_text = " ".join([doc.page_content for doc in docs])

    # Step 3: Final Answer Prompt
    final_prompt_template = PromptTemplate(
        template="""
You are a helpful assistant analyzing a GitHub repository.
Answer the question based ONLY on context provided below.

If answer is not present in the context — say "I don't know".

Context:
{context}

Question:
{question}

Answer:
""",
        input_variables=["context", "question"]
    )

    final_prompt = final_prompt_template.format(
        context=context_text,
        question=question
    )

    response = llm.invoke(final_prompt)
    final_answer = output_parser.invoke(response)

    return {
        "status": "success",
        "rewritten_question": rewritten_q,
        "answer": final_answer
    }
