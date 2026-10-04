import json
import os

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    PyPDFLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

from config import INDEX_NAME
from pinecone_setup import obtener_indice, NAMESPACE

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def cargar_documentos():
    documentos = []

    # Markdown
    loader_md = DirectoryLoader(
        "data",
        glob="*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )

    documentos.extend(loader_md.load())

    # PDF
    archivos_pdf = [
        archivo for archivo in os.listdir("data") if archivo.lower().endswith(".pdf")
    ]

    for archivo in archivos_pdf:
        ruta = os.path.join("data", archivo)
        loader_pdf = PyPDFLoader(ruta)
        documentos.extend(loader_pdf.load())

    # JSON
    archivos_json = [
        archivo for archivo in os.listdir("data") if archivo.lower().endswith(".json")
    ]

    for archivo in archivos_json:
        ruta = os.path.join("data", archivo)

        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)

        contenido = json.dumps(datos, ensure_ascii=False, indent=2)

        documentos.append(
            Document(page_content=contenido, metadata={"source": archivo, "page": 0})
        )

    print(f"📄 Documentos cargados: {len(documentos)}")

    return documentos

def dividir_documentos(documentos):
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=600,
        chunk_overlap=100,
    )

    chunks = splitter.split_documents(documentos)

    for i, chunk in enumerate(chunks):

        nombre_archivo = os.path.basename(chunk.metadata.get("source", "desconocido"))
        categoria = os.path.splitext(nombre_archivo)[0].replace("_", " ").title()
        pagina = chunk.metadata.get("page", 0)

        chunk.metadata["source"] = nombre_archivo
        chunk.metadata["page"] = pagina
        chunk.metadata["categoria"] = categoria
        chunk.metadata["content"] = chunk.page_content
        chunk.metadata["chunk_id"] = i

    print(f"✂️ Fragmentos generados: {len(chunks)}")
    return chunks

def generar_embeddings():
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return embeddings

def subir_a_pinecone(chunks, embeddings):
    obtener_indice()

    vectorstore = PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        index_name=INDEX_NAME,
        namespace=NAMESPACE,
    )
    print("☁️ Documentos subidos correctamente a Pinecone.")
    return vectorstore


def ejecutar_ingesta():    
    documentos = cargar_documentos()
    chunks = dividir_documentos(documentos)
    embeddings = generar_embeddings()
    vectorstore = subir_a_pinecone(chunks, embeddings)
    return vectorstore

if __name__ == "__main__":
    ejecutar_ingesta()