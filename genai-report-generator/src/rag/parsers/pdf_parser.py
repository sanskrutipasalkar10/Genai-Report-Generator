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
    Universal "LLM-First" PDF Parser with NUMERIC FIREWALL.
    
    Logic:
    1. Extract Raw Text (Layout Preserved).
    2. Filter: Skip pages with no "Business Data" (numbers) to save cost.
    3. Extract: AI converts Text -> CSV directly (No standard parser used).
    4. FIREWALL: Rejects any table where AI numbers do not match source text.
    """
    full_text = ""
    tables = {}
    table_count = 0
    llm = get_llm()

    print(f"   📄 Parsing PDF (LLM-Only Mode): {file_path}")

    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"      Scanning {len(pdf.pages)} pages...")
            
            for i, page in enumerate(pdf.pages):
                # 1. Get Raw Text (Preserve physical layout)
                # This helps the LLM see the 'shape' of the table
                text = page.extract_text(layout=True)
                if not text: continue
                
                full_text += f"--- Page {i+1} ---\n{text}\n\n"

                # 2. Pre-Filter: Does this page even have data?
                # Optimization: Don't send legal text or cover pages to the LLM.
                if not _page_has_data_potential(text):
                    # print(f"      Skipping Page {i+1} (No numerical data detected)")
                    continue

                print(f"      🧠 Page {i+1} has potential data. Asking AI to extract...")
                
                # 3. AI Extraction (The Core Logic)
                ai_df = _extract_via_llm(llm, text)
                
                # 4. THE FIREWALL (Anti-Hallucination Validation)
                if ai_df is not None and not ai_df.empty:
                    if _validate_numbers(text, ai_df):
                        table_count += 1
                        # Normalize headers
                        ai_df.columns = [str(c).strip() for c in ai_df.columns]
                        tables[f"Page_{i+1}_Table_{table_count}"] = ai_df
                        print(f"      ✅ Extracted & Verified Table {table_count}")
                    else:
                        print(f"      ❌ AI Hallucination Blocked. (Numbers in output do not match source text)")

        print(f"      ✅ Final Count: {len(tables)} Valid Tables.")
        return full_text, tables

    except Exception as e:
        print(f"   ❌ PDF Parse Error: {e}")
        return "", {}

# --- HELPER FUNCTIONS ---

def _page_has_data_potential(text: str) -> bool:
    """
    Heuristic: A financial/inventory table must have at least 3 distinct numbers.
    This prevents sending pages of just text (Introduction, Legal) to the LLM.
    """
    nums = re.findall(r'\d+', text)
    return len(set(nums)) >= 3

def _extract_via_llm(llm, text_chunk: str) -> pd.DataFrame:
    """
    Directly asks LLM to find the table in the text layout.
    """
    prompt = f"""
    You are a Strict Data Extraction Engine.
    Analyze the text layout below.
    
    TASK:
    1. Identify if there is a STRUCTURED DATA TABLE (Rows & Columns).
    2. If YES: Extract it as a standard CSV.
    3. If NO (e.g. it's just sentences, legal text, or lists): Output "NO_DATA".
    
    CRITICAL RULES:
    - EXACT MATCH: Do not change any numbers.
    - Do not extract page numbers, headers, or footers as data.
    - Fix merged headers (e.g. "Stock On Hand" -> "Stock_On_Hand").
    
    TEXT CONTENT:
    {text_chunk[:3500]}
    """
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        
        # Check for refusal
        if "NO_DATA" in content or "no structured data" in content.lower():
            return None
            
        # Clean Markdown
        if "```" in content:
            content = content.replace("```csv", "").replace("```", "").strip()
            
        df = pd.read_csv(io.StringIO(content))
        
        # Sanity Check: A table must have at least 1 row and 2 columns
        if len(df) < 1 or len(df.columns) < 2:
            return None
            
        return df
    except: return None

def _extract_numbers_from_string(s: str) -> set:
    """
    Extracts all numbers (integers and floats) from a string for validation.
    """
    s_clean = str(s).replace(',', '')
    matches = re.findall(r'-?\d+\.?\d*', s_clean)
    return {float(x) for x in matches}

def _validate_numbers(raw_text: str, df: pd.DataFrame) -> bool:
    """
    The Hallucination Firewall.
    Returns False if the AI invented 'Business Numbers' (> 50) that don't exist in the source text.
    """
    raw_numbers = _extract_numbers_from_string(raw_text)
    
    # Get all numbers from the AI's output dataframe
    df_text = df.to_string(index=False, header=False)
    ai_numbers = _extract_numbers_from_string(df_text)
    
    if not ai_numbers: return False 
    
    # Check: Are there numbers in AI that are NOT in Source?
    hallucinations = ai_numbers - raw_numbers
    
    # Filter out trivial mismatches (like 1 vs 1.0, or small integers < 50 that might be dates/IDs)
    # We care about "Business Numbers" (Values > 50) being invented.
    critical_hallucinations = [h for h in hallucinations if abs(h) > 50]
    
    if critical_hallucinations:
        print(f"         🚨 Blocked Hallucination: {critical_hallucinations}")
        return False
        
    return True