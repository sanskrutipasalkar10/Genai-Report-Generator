import pdfplumber
import pandas as pd
import logging
import io
import re
from typing import Tuple, Dict
from langchain_core.messages import HumanMessage
from src.engine.llm import get_llm

# 🟢 SILENCE WARNINGS
logging.getLogger("pdfminer").setLevel(logging.ERROR)

def parse_pdf(file_path: str) -> Tuple[str, Dict[str, pd.DataFrame]]:
    """
    Production-Grade PDF Parser with AGGRESSIVE VALIDATION.
    1. Tries Standard Extraction.
    2. SCANS FOR "BAD SLICES" (Partial words like 'nsit', 'Tra').
    3. Fallback: AI Repair if any garbage is detected.
    """
    full_text = ""
    tables = {}
    table_count = 0
    llm = get_llm()

    print(f"   📄 Parsing PDF: {file_path}")

    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"      Scanning {len(pdf.pages)} pages...")
            
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    full_text += f"--- Page {i+1} ---\n{text}\n\n"

                # PHASE 1: STANDARD EXTRACTION
                strategies = [
                    {"vertical_strategy": "lines", "horizontal_strategy": "lines"}, 
                    {"vertical_strategy": "text", "horizontal_strategy": "text"},   
                ]
                
                valid_df = None
                for settings in strategies:
                    try:
                        found = page.extract_tables(table_settings=settings)
                        if found:
                            # Iterate through found tables
                            for table_data in found:
                                raw_df = pd.DataFrame(table_data)
                                # 🟢 AGGRESSIVE VALIDATION
                                if _is_valid_table(raw_df):
                                    valid_df = raw_df
                                    break
                            if valid_df is not None: break
                    except: continue

                # PHASE 2: AI REPAIR (Triggered if Valid DF is still None)
                if valid_df is None and text and _text_looks_like_data(text):
                    print(f"      ⚠️ Page {i+1}: Standard parse rejected (Bad Slices Detected). Engaging AI Repair...")
                    
                    ai_df = _extract_via_llm(llm, text)
                    if ai_df is not None:
                        if _validate_numbers(text, ai_df):
                            valid_df = ai_df
                            print(f"      ✅ AI Output Validated (Numbers match source).")
                        else:
                            print(f"      ❌ AI Hallucination Detected! Discarding unsafe table.")

                # PHASE 3: SAVE
                if valid_df is not None:
                    try:
                        # Normalize headers
                        valid_df.columns = [str(c).strip() for c in valid_df.columns]
                        has_numbers = valid_df.astype(str).apply(lambda x: x.str.contains(r'\d', na=False)).any().any()
                        if has_numbers:
                            table_count += 1
                            tables[f"Page_{i+1}_Table_{table_count}"] = valid_df
                    except: pass

        print(f"      ✅ Extracted {len(tables)} Valid Tables.")
        return full_text, tables

    except Exception as e:
        print(f"   ❌ PDF Parse Error: {e}")
        return "", {}

# --- HELPER FUNCTIONS ---

def _is_valid_table(df: pd.DataFrame) -> bool:
    """
    Aggressively rejects tables with "Bad Slices" (partial words).
    """
    if df.empty or len(df) < 2 or len(df.columns) < 2: return False
    
    # 🟢 NEW: SCAN TOP 5 ROWS (Not just Row 0)
    # The header might be on Row 2 or 3. We check them all.
    rows_to_scan = 5
    scan_limit = min(len(df), rows_to_scan)
    
    # BAD KEYWORDS: Common fragments from bad PDF slicing
    # 'nsit' -> from Transit
    # 'Tra' -> from Transit
    # 'n_Hand' -> from On_Hand
    # 'ui' -> from Require
    bad_fragments = ["nsit", "n_Hand", "Tra_", "_Tra", "ock_On", "ui_"]
    
    for i in range(scan_limit):
        row_str = " ".join(df.iloc[i].astype(str)).lower()
        
        # 1. Check for Bad Fragments
        for bad in bad_fragments:
            if bad in row_str:
                # print(f"         🚫 Rejected: Found bad fragment '{bad}' in Row {i}")
                return False

        # 2. Check for Lowercase Starters (e.g. "hand", "transit" in a Header row)
        # If a cell starts with lowercase but is not 'unnamed', it's suspicious in a header
        for cell in df.iloc[i].astype(str):
            cell = cell.strip()
            if len(cell) > 3 and cell[0].islower() and "unnamed" not in cell.lower() and not cell.replace('.','').isdigit():
                # Only strict if it looks like a word
                if cell.isalpha():
                    # print(f"         🚫 Rejected: Lowercase header '{cell}' detected.")
                    return False

    return True

def _text_looks_like_data(text: str) -> bool:
    digit_count = sum(c.isdigit() for c in text)
    return digit_count > 10

def _extract_numbers_from_string(s: str) -> set:
    s_clean = s.replace(',', '')
    matches = re.findall(r'-?\d+\.?\d*', s_clean)
    return {float(x) for x in matches}

def _validate_numbers(raw_text: str, df: pd.DataFrame) -> bool:
    raw_numbers = _extract_numbers_from_string(raw_text)
    df_text = df.to_string(index=False, header=False)
    ai_numbers = _extract_numbers_from_string(df_text)
    
    if not ai_numbers: return False 
    
    hallucinations = ai_numbers - raw_numbers
    critical_hallucinations = [h for h in hallucinations if abs(h) > 50]
    
    if critical_hallucinations:
        print(f"         🚨 Blocked Numbers: {critical_hallucinations}")
        return False
        
    return True

def _extract_via_llm(llm, text_chunk: str) -> pd.DataFrame:
    prompt = f"""
    You are a Strict Data Extraction Engine.
    Convert the following text into CSV format.
    
    RULES:
    1. EXACT MATCH: Do not change any numbers.
    2. Structure: Fix merged headers. e.g. "Stock On Hand" is ONE column. "In Transit" is ONE column.
    3. Output ONLY the CSV data.
    
    TEXT:
    {text_chunk[:2500]}
    """
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        csv_content = response.content.strip()
        if "```" in csv_content:
            csv_content = csv_content.replace("```csv", "").replace("```", "").strip()
        return pd.read_csv(io.StringIO(csv_content))
    except: return None