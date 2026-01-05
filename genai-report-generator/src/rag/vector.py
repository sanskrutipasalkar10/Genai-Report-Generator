import chromadb
from langchain_community.vectorstores import Chroma
from src.rag.embeddings import get_embedding_model
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "config/settings.yaml"
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

def get_vector_store():
    """Initializes or loads the ChromaDB vector store"""
    embedding_func = get_embedding_model()
    
    # Persistent client to save data to disk
    persist_path = config['rag']['vector_db_path']
    collection = config['rag']['collection_name']
    
    vector_store = Chroma(
        collection_name=collection,
        embedding_function=embedding_func,
        persist_directory=persist_path
    )
    
    return vector_store