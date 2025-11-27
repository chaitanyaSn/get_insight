import os
from typing import List
from dotenv import load_dotenv

load_dotenv()  

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  
# EMBED_MODEL = "nomic-ai/nomic-embed-text-v1"


# CORS settings
ALLOWED_ORIGINS: List[str] = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173"
).split(",")

CORS_CONFIG = {
    "allow_origins": ALLOWED_ORIGINS,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["*"],
}






