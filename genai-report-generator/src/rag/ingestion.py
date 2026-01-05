import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.rag.vector_store import get_vector_store
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "config/settings.yaml"
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

def load_file(file_path: str):
    """Router to choose the correct loader based on extension"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        return PyPDFLoader(file_path).load()
    elif ext == ".csv":
        return CSVLoader(file_path).load()
    elif ext in [".xlsx", ".xls"]:
        return UnstructuredExcelLoader(file_path).load()
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def ingest_file(file_path: str):
    """
    Main pipeline: Load -> Split -> Embed -> Store
    """
    print(f"🚀 Starting ingestion for: {file_path}")
    
    # 1. Load
    raw_docs = load_file(file_path)
    print(f"📄 Loaded {len(raw_docs)} pages/rows")
    
    # 2. Split (Chunking)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config['rag']['chunk_size'],
        chunk_overlap=config['rag']['chunk_overlap']
    )
    chunks = text_splitter.split_documents(raw_docs)
    print(f"✂️  Split into {len(chunks)} chunks")
    
    # 3. Store (Embedding happens automatically here)
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    
    print("✅ Ingestion complete. Data is ready for RAG.")
    return True