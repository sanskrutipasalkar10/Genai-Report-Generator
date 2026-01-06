import pandas as pd
import docx
from typing import Tuple, List, Dict

def parse_docx(file_path: str) -> Tuple[str, Dict[str, pd.DataFrame]]:
    """
    Parses a DOCX file to extract text and VALID data tables.
    """
    doc = docx.Document(file_path)
    full_text = []
    tables = {}

    # 1. Extract Text
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)

    # 2. Extract & Filter Tables
    for i, table in enumerate(doc.tables):
        # EXTRACT: Get all rows
        data = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        
        if not data:
            continue

        # --- 🟢 HEURISTIC FILTERING ---
        # Rule 1: Must have at least 2 rows (Header + Data)
        if len(data) < 2:
            continue
            
        # Rule 2: Must have at least 2 columns (Single col is usually a list/layout)
        if len(data[0]) < 2:
            continue
            
        # Rule 3: Check for "Ghost" tables (mostly empty)
        # Flatten list and count empty strings
        flat_cells = [item for sublist in data for item in sublist]
        empty_count = flat_cells.count("")
        if empty_count / len(flat_cells) > 0.8: # Skip if >80% empty
            continue
            
        # Create DataFrame
        try:
            # Assume first row is header
            headers = data[0]
            # Handle duplicate headers
            headers = [f"{h}_{j}" if headers.count(h) > 1 else h for j, h in enumerate(headers)]
            
            df = pd.DataFrame(data[1:], columns=headers)
            
            # Additional check: Does it contain ANY numbers? 
            # (Financial tables must have digits)
            # This logic creates a boolean mask of digits and checks if any exist
            has_numbers = df.astype(str).apply(lambda x: x.str.contains(r'\d', na=False)).any().any()
            
            if has_numbers:
                tables[f"Table_{i+1}"] = df
                
        except Exception as e:
            print(f"⚠️ Warning processing DOCX table {i}: {e}")

    return "\n".join(full_text), tables