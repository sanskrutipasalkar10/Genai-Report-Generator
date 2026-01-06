import pdfplumber
import pandas as pd
from typing import Tuple, Dict
import pdfplumber
import pandas as pd
import logging  # <--- Add this

# 🟢 SILENCE WARNINGS: This stops the console spam
logging.getLogger("pdfminer").setLevel(logging.ERROR)

from typing import Tuple, Dict

# ... rest of your code ...

def parse_hybrid_pdf(file_path: str) -> Tuple[str, Dict[str, pd.DataFrame]]:
    """
    Extracts text and filters for high-quality data tables from PDF.
    """
    full_text = ""
    tables = {}
    table_count = 0

    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"   📄 Scanning {len(pdf.pages)} pages in PDF...")
            
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
                    
                    # Rule 2: Header sanity check
                    # If the first row is massive text blocks, it's likely layout, not a header
                    if len(str(clean_data[0])) > 1000:
                        continue

                    try:
                        header = clean_data[0]
                        # Handle duplicate headers
                        header = [f"{col}_{j}" if header.count(col) > 1 else col for j, col in enumerate(header)]
                        
                        df = pd.DataFrame(clean_data[1:], columns=header)
                        
                        # Rule 3: Numerical Density
                        # Check if at least one cell has a number
                        has_numbers = df.astype(str).apply(lambda x: x.str.contains(r'\d', na=False)).any().any()
                        
                        if has_numbers:
                            table_count += 1
                            tables[f"PDF_Table_{table_count}"] = df
                            
                    except Exception as e:
                        continue

        print(f"   ✅ Extracted {len(tables)} Valid Tables (Filtered out junk).")
        return full_text, tables

    except Exception as e:
        print(f"❌ PDF Parse Error: {e}")
        return "", {}