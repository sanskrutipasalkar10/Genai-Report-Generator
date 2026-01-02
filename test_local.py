import sys
import os
from src.ingestion.loader import ingest_document
from src.reasoning.code_interpreter import analyze_data_with_code

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 1. Setup Dummy Data
# Create a dummy PDF or use an existing one in your data folder
TEST_PDF = "data/raw_uploads/cj.pdf" 

if not os.path.exists(TEST_PDF):
    print(f"Please place a PDF at {TEST_PDF} to test.")
    sys.exit()

# 2. Test Ingestion
print("\n--- Testing Ingestion ---")
try:
    text_chunks, tables_html = ingest_document(TEST_PDF)
    print(f"[OK] Success! Extracted {len(text_chunks)} text chunks and {len(tables_html)} tables.")
except Exception as e:
    print(f"[ERROR] Ingestion Failed: {e}")
    sys.exit()

# 3. Test Reasoning (If tables exist)
if tables_html:
    print("\n--- Testing Logic Agent (No Hallucination) ---")
    query = "What is the total/sum of the values in the first column?"
    try:
        response = analyze_data_with_code(tables_html, query)
        print(f"[OK] Reasoning Response: {response}")
    except Exception as e:
        print(f"[ERROR] Reasoning Failed: {e}")
else:
    print("\n[WARNING] No tables found, skipping Logic Agent test.")