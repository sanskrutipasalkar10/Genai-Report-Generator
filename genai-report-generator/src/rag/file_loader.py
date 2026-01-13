import pandas as pd
import os
from typing import Tuple, List, Dict, Any, Union

# Try importing parsers, gracefully handle if missing
try:
    from src.rag.parsers.pdf_parser import parse_pdf # Renamed to match standard
    from src.rag.parsers.docx_parser import parse_docx
except ImportError:
    print("⚠️ [File Loader] Parsers not found. PDF/DOCX support limited.")
    parse_pdf = None
    parse_docx = None

def load_file(file_path: str) -> Tuple[str, Union[List[pd.DataFrame], Dict[str, pd.DataFrame]], Dict]:
    """
    Ingests a file and returns raw content.
    
    Returns:
        raw_text (str): Extracted text (for RAG/Summarization)
        tables (list/dict): Extracted DataFrames (raw, no headers set)
        config (dict): Empty dict (placeholder for compatibility)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)
    print(f"📂 [File Loader] Ingesting: {filename}")

    raw_text = ""
    tables = [] # Can be a List or Dict
    config = {} # Placeholder - Inspection happens in main pipeline now

    try:
        # --- 1. EXCEL ---
        if ext in [".xlsx", ".xls"]:
            # Load with header=None so DataSanitizer can find the real header later
            # Load all sheets as a Dict
            tables = pd.read_excel(file_path, sheet_name=None, header=None)
            
        # --- 2. CSV ---
        elif ext == ".csv":
            # Load with header=None so DataSanitizer can find the real header later
            df = pd.read_csv(file_path, header=None, engine='python')
            tables = [df] # Return as list

        # --- 3. PDF ---
        elif ext == ".pdf":
            if parse_pdf:
                raw_text, tables = parse_pdf(file_path)
            else:
                print("❌ PDF Parser not installed.")

        # --- 4. DOCX ---
        elif ext in [".docx", ".doc"]:
            if parse_docx:
                raw_text, tables = parse_docx(file_path)
            else:
                print("❌ DOCX Parser not installed.")

        else:
            print(f"❌ Unsupported file type: {ext}")

    except Exception as e:
        print(f"❌ [File Loader] Read Error: {e}")
        # Return empty structures on failure to prevent crashes
        return "", [], {}

    # Return raw data. 
    # NOTE: We do NOT clean here. usage of DataSanitizer in main.py handles that.
    return raw_text, tables, config