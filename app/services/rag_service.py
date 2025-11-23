import shutil
import os
from langchain_community.document_loaders import GitLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI


from app.core.config import EMBED_MODEL, FAISS_INDEX_PATH, GOOGLE_API_KEY
from app.prompt.rag_prompt import output_parser, question_rewrite_template, final_answer_template

def load_repo_and_index(repo_url: str, branch: str = "main") -> None:
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


def ask_question(question: str) -> dict:
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

    return {
        "rewritten_question": rewritten_q,
        "answer": final_answer
    }
