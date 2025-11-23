import os
from dotenv import load_dotenv

load_dotenv()  

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  
EMBED_MODEL = "nomic-ai/nomic-embed-text-v1"
FAISS_INDEX_PATH = "./faiss_index"