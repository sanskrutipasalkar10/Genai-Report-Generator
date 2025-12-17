import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import PROCESSED_PATH, CHUNK_SIZE, CHUNK_OVERLAP

def chunk_documents():
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = []

    for file in os.listdir(PROCESSED_PATH):
        file_path = os.path.join(PROCESSED_PATH, file)

        if not file_path.endswith(".txt"):
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        file_chunks = splitter.split_text(text)
        chunks.extend(file_chunks)

    print(f"✅ Total chunks created: {len(chunks)}")
    print("\n🔹 Sample chunk:\n", chunks[0][:500])

    return chunks

if __name__ == "__main__":
    chunk_documents()
