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
        error_str = str(e).lower()
        error_type = str(type(e).__name__)
        
        # Handle poppler missing error
        if "poppler" in error_str or "PDFInfoNotInstalledError" in error_type:
            print("[WARNING] Poppler not found. Falling back to 'fast' strategy (may have lower table detection quality).")
            print("   To enable hi_res strategy, install poppler: https://github.com/oschwartz10612/poppler-windows/releases")
            # Fallback to "fast" strategy which doesn't require poppler
            elements = partition(
                filename=file_path,
                strategy="fast",
                infer_table_structure=True
            )
        # Handle pdfminer import errors (psexceptions, layout, etc.)
        elif "pdfminer" in error_str:
            print("[WARNING] pdfminer import error detected. Trying alternative PDF processing methods.")
            # Try "fast" strategy first
            try:
                elements = partition(
                    filename=file_path,
                    strategy="fast",
                    infer_table_structure=True
                )
            except Exception as e2:
                # If fast also fails, try "auto" strategy
                try:
                    print("[WARNING] 'fast' strategy also failed. Trying 'auto' strategy.")
                    elements = partition(
                        filename=file_path,
                        strategy="auto",
                        infer_table_structure=True
                    )
                except Exception as e3:
                    # If all unstructured strategies fail, use pypdf as last resort
                    print("[WARNING] All unstructured strategies failed. Using pypdf fallback (text only, no tables).")
                    print(f"   Error details: {str(e3)[:200]}")
                    return _fallback_pypdf_extraction(file_path)
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

def _fallback_pypdf_extraction(file_path: str):
    """
    Fallback PDF extraction using pypdf when unstructured fails.
    Only extracts text, no table detection.
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text_chunks = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text.strip():
                text_chunks.append(text)
        
        # Return text chunks, no tables (pypdf doesn't detect tables)
        return text_chunks, []
    except Exception as e:
        raise Exception(f"Even pypdf fallback failed: {e}")