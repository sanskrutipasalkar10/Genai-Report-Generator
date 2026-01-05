import pdfplumber
import pandas as pd
from typing import List, Tuple, Optional

def parse_hybrid_pdf(file_path: str) -> Tuple[str, List[pd.DataFrame]]:
    """
    Scans a PDF and separates it into:
    1. Raw Text (for RAG/Summarization)
    2. DataFrames (for Analyst/Calculation)
    """
    full_text = []
    extracted_tables = []
    
    print(f"🔍 Scanning PDF: {file_path}...")
    
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # 1. Extract Tables from this page
            tables = page.extract_tables()
            
            for table_data in tables:
                # Clean Data: Remove None/Empty cells
                clean_table = [row for row in table_data if any(row)]
                
                if clean_table:
                    # Assume first row is header
                    try:
                        df = pd.DataFrame(clean_table[1:], columns=clean_table[0])
                        
                        # 🟢 FIX: Modern Pandas numeric conversion
                        # Try to convert each column to numeric, if it fails, keep as is.
                        for col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col])
                            
                        extracted_tables.append(df)
                        print(f"   found table on page {i+1} with columns: {list(df.columns)}")
                    except Exception as e:
                        print(f"   ⚠️ Warning: Could not parse table on page {i+1}: {e}")

            # 2. Extract Text (ignoring tables to avoid duplication usually requires complex coordinate logic, 
            # but for now we extract full text for context)
            text = page.extract_text()
            if text:
                full_text.append(text)

    return "\n".join(full_text), extracted_tables