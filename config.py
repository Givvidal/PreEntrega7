import os
from dotenv import load_dotenv

load_dotenv()


PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME", "videojuegos-rag")


if not PINECONE_API_KEY:
    raise ValueError("Falta configurar PINECONE_API_KEY en el archivo .env")


if not GOOGLE_API_KEY:
    raise ValueError("Falta configurar GOOGLE_API_KEY en el archivo .env")
