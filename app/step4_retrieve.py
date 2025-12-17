from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from app.config import VECTOR_DB_PATH, OLLAMA_EMBED

def retrieve_context(query, k=4):
    embeddings = OllamaEmbeddings(model=OLLAMA_EMBED)

    vectordb = Chroma(
        persist_directory=VECTOR_DB_PATH,
        embedding_function=embeddings
    )

    docs = vectordb.similarity_search(query, k=k)

    context = "\n\n".join(doc.page_content for doc in docs)

    print("🔎 Retrieved context preview:\n")
    print(context[:600])

    return context

if __name__ == "__main__":
    retrieve_context("key business risks and insights")
