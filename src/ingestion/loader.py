# src/ingestion/loader.py
from unstructured.partition.auto import partition
from unstructured.documents.elements import Table, CompositeElement

def ingest_document(file_path: str):
    """
    Uses 'hi_res' strategy to visualy detect tables vs text.
    Falls back to 'fast' strategy if poppler is not available.
    Returns separate streams for Vector DB (text) and Code Interpreter (tables).
    """
    print(f"Partitioning {file_path}...")
    
    # Try "hi_res" strategy first (requires poppler for image conversion)
    try:
        elements = partition(
            filename=file_path, 
            strategy="hi_res",
            infer_table_structure=True, 
            extract_images_in_pdf=True
        )
    except Exception as e:
        if "poppler" in str(e).lower() or "PDFInfoNotInstalledError" in str(type(e).__name__):
            print("[WARNING] Poppler not found. Falling back to 'fast' strategy (may have lower table detection quality).")
            print("   To enable hi_res strategy, install poppler: https://github.com/oschwartz10612/poppler-windows/releases")
            # Fallback to "fast" strategy which doesn't require poppler
            elements = partition(
                filename=file_path,
                strategy="fast",
                infer_table_structure=True
            )
        else:
            # Re-raise if it's a different error
            raise
    
    text_chunks = []
    tables = []
    
    for el in elements:
        if isinstance(el, Table):
            # Store table as HTML/DataFrame for the LLM to write code against
            if el.metadata.text_as_html:
                tables.append(el.metadata.text_as_html)
        elif isinstance(el, CompositeElement):
            text_chunks.append(str(el))
            
    return text_chunks, tables