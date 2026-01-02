# src/storage/retriever.py
from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
from langchain_community.retrievers import EnsembleRetriever
from langchain_huggingface import HuggingFaceEmbeddings

def get_hybrid_retriever(docs):
    # 1. Dense Vector Retriever (Semantic)
    embedding = HuggingFaceEmbeddings(model_name="nomic-ai/nomic-embed-text-v1.5")
    vectorstore = Chroma.from_documents(docs, embedding)
    chroma_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # 2. Sparse Retriever (Keyword Exact Match)
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = 5

    # 3. Ensemble (Rerank results from both)
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, chroma_retriever],
        weights=[0.5, 0.5]
    )
    
    return ensemble_retriever