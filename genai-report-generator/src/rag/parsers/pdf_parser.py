import pdfplumber
import pandas as pd
import logging
from typing import Tuple, Dict

# 🟢 SILENCE WARNINGS: Stops pdfminer console spam
logging.getLogger("pdfminer").setLevel(logging.ERROR)

def parse_pdf(file_path: str) -> Tuple[str, Dict[str, pd.DataFrame]]:
    """
    Extracts text and filters for high-quality data tables from PDF.
    Returns raw DataFrames (no headers set) for the Sanitizer to clean.
    """
    full_text = ""
    tables = {}
    table_count = 0

    print(f"   📄 Parsing PDF: {file_path}")

    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"      Scanning {len(pdf.pages)} pages...")
            
            for i, page in enumerate(pdf.pages):
                # 1. Extract Text
                text = page.extract_text()
                if text:
                    full_text += f"--- Page {i+1} ---\n{text}\n\n"

                # 2. Extract Tables
                extracted_table_data = page.extract_tables()
                
                for table_data in extracted_table_data:
                    if not table_data:
                        continue
                        
                    # --- 🟢 HEURISTIC FILTERING ---
                    
                    # Rule 1: Minimum Size (2x2)
                    if len(table_data) < 2 or len(table_data[0]) < 2:
                        continue
                    
                    # Clean data: Replace None with ""
                    clean_data = [[cell if cell is not None else "" for cell in row] for row in table_data]
                    
                    # Rule 2: Layout Check
                    # If the first row is massive text blocks (>500 chars), it's likely layout text, not a table header
                    if len(str(clean_data[0])) > 1000:
                        continue

                    try:
                        # 🟢 CRITICAL CHANGE: No Header Assignment
                        # We pass the raw grid to DataSanitizer
                        df = pd.DataFrame(clean_data)
                        
                        # Rule 3: Numerical Density
                        # Financial tables must have digits
                        has_numbers = df.astype(str).apply(lambda x: x.str.contains(r'\d', na=False)).any().any()
                        
                        if has_numbers:
                            table_count += 1
                            # Name tables by Page Number helps context
                            tables[f"Page_{i+1}_Table_{table_count}"] = df
                            
                    except Exception as e:
                        continue

        print(f"      ✅ Extracted {len(tables)} Valid Tables from PDF.")
        return full_text, tables

    except Exception as e:
        print(f"   ❌ PDF Parse Error: {e}")
        return "", {}