import os
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from app.step2_chunk import chunk_documents
from app.config import VECTOR_DB_PATH, OLLAMA_EMBED

def build_vector_db():
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)

    chunks = chunk_documents()

    embeddings = OllamaEmbeddings(model=OLLAMA_EMBED)

    vectordb = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_PATH
    )

    vectordb.persist()
    print("✅ Vector database created and persisted")

if __name__ == "__main__":
    build_vector_db()
