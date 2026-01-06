import pandas as pd
import os
from typing import Tuple, Dict, Any
from src.engine.agents.inspector import inspect_file

# Import the new parsers
try:
    from src.rag.parsers.pdf_parser import parse_hybrid_pdf
    from src.rag.parsers.docx_parser import parse_docx
except ImportError:
    print("⚠️ Warning: Parsers not found. PDF/DOCX support limited.")

def load_file(file_path: str) -> Tuple[str, Dict[str, pd.DataFrame], Dict[str, Any]]:
    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)
    print(f"📂 Processing: {filename}")

    INSPECT_ROWS = 300 
    raw_preview = ""
    tables = {}
    full_text = ""

    try:
        # --- 1. EXCEL ---
        if ext in [".xlsx", ".xls"]:
            tables = pd.read_excel(file_path, sheet_name=None)
            if tables:
                largest_sheet = max(tables, key=lambda k: tables[k].size)
                df_preview = tables[largest_sheet].head(INSPECT_ROWS)
                raw_preview = f"Sheet '{largest_sheet}' Preview:\n{df_preview.to_string()}"
            
        # --- 2. CSV ---
        elif ext == ".csv":
            df = pd.read_csv(file_path)
            tables = {"CSV_Data": df}
            raw_preview = f"CSV Preview:\n{df.head(INSPECT_ROWS).to_string()}"

        # --- 3. PDF (New Logic) ---
        elif ext == ".pdf":
            full_text, tables = parse_hybrid_pdf(file_path)
            # Create preview from first valid table
            if tables:
                first_table = list(tables.values())[0]
                raw_preview = f"PDF Table Preview:\n{first_table.head(10).to_string()}"
            else:
                raw_preview = full_text[:2000]

        # --- 4. DOCX (New Logic) ---
        elif ext == ".docx":
            full_text, tables = parse_docx(file_path)
            if tables:
                first_table = list(tables.values())[0]
                raw_preview = f"DOCX Table Preview:\n{first_table.head(10).to_string()}"
            else:
                raw_preview = full_text[:2000]

        else:
            print(f"❌ Unsupported file type: {ext}")
            return "", {}, {}

    except Exception as e:
        print(f"❌ Read Error: {e}")
        return "", {}, {}

    # --- 5. INSPECTION ---
    config = inspect_file(raw_preview, filename)

    # --- 6. CLEANING ---
    cleaned_tables = {}
    for name, df in tables.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            df.dropna(how='all', axis=0, inplace=True)
            df.dropna(how='all', axis=1, inplace=True)
            cleaned_tables[name] = df

    return full_text, cleaned_tables, config