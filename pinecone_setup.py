from pinecone import Pinecone, ServerlessSpec
from config import PINECONE_API_KEY, INDEX_NAME

EMBEDDING_DIM = 384
NAMESPACE = "videojuegos"

def obtener_indice():
    """
    Conecta con Pinecone y devuelve el índice configurado.
    Si el índice no existe, lo crea.
    """

    pc = Pinecone(api_key=PINECONE_API_KEY)

    indices_existentes = [indice["name"] for indice in pc.list_indexes()]

    if INDEX_NAME not in indices_existentes:
        print(f"🆕 Creando índice '{INDEX_NAME}'...")

        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

        print("✅ Índice creado correctamente.")

    else:
        print(f"♻️ El índice '{INDEX_NAME}' ya existe.")

    return pc.Index(INDEX_NAME)