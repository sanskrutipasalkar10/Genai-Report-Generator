import sys
import os
import argparse
import pandas as pd
import yaml
import json
import requests
from io import StringIO
import traceback

# --- 1. SETUP & DIRECTORIES ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

ARTIFACTS_DIR = os.path.join(project_root, "data", "artifacts")
IMAGES_DIR = os.path.join(ARTIFACTS_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

from src.rag.file_loader import load_file
from src.engine.agents.writer import writer_agent

# 🟢 IMPORT CODE EXECUTOR
try:
    from src.engine.tools.code_executor import execute_python_code
except ImportError:
    print("❌ Critical: src/engine/tools/code_executor.py not found.")
    sys.exit(1)

# --- 🟢 UNIVERSAL REST AGENT ---
class OllamaRestAgent:
    def __init__(self, model_name, base_url):
        self.model_name = model_name
        self.base_url = base_url.rstrip('/') + "/api/generate"

    def invoke(self, prompt_text):
        content = prompt_text.content if hasattr(prompt_text, 'content') else str(prompt_text)
        payload = {"model": self.model_name, "prompt": content, "stream": True}
        try:
            response = requests.post(self.base_url, data=json.dumps(payload), stream=True)
            response.raise_for_status()
            full_text = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    if 'response' in data: full_text += data['response']
                    if data.get('done'): break
            class MockResponse:
                def __init__(self, text): self.content = text
            return MockResponse(full_text)
        except Exception as e:
            print(f"\n❌ REST API Error: {e}")
            class MockResponse:
                def __init__(self, text): self.content = ""
            return MockResponse("")

def get_llm():
    return OllamaRestAgent("qwen3-coder:480b-cloud", "http://localhost:11434")

# --- UTILS ---
def smart_load_table(path): 
    # Do NOT try to read PDFs/DOCX as Excel
    if path.lower().endswith(('.pdf', '.docx', '.doc')):
        return pd.DataFrame()
        
    try:
        print(f"📂 Smart Loading: {path}")
        if path.endswith('.csv'): return pd.read_csv(path, header=None)
        return pd.read_excel(path, header=None)
    except Exception as e:
        print(f"❌ Smart Load Failed: {e}")
        return pd.DataFrame()

# ---------------------------------------------------------
# 🕵️ AGENT 1: INSPECTOR
# ---------------------------------------------------------
def run_inspector_agent(df):
    print("\n🕵️ Inspector Agent is analyzing file structure...")
    buffer = StringIO(); df.info(buf=buffer); schema_info = buffer.getvalue()
    try: sample = df.head(10).to_markdown(index=False)
    except: sample = df.head(10).to_string(index=False)

    prompt = f"""
    You are a Senior Data Architect. Reverse-engineer this dataset.
    
    RAW DATA (First 10 Rows):
    {sample}
    
    SCHEMA:
    {schema_info}
    
    TASK:
    1. Identify the REAL header row index.
    2. Map "Unnamed" columns to business labels.
    3. Identify Key Metrics (Revenue, Counts, etc).
    
    OUTPUT FORMAT (STRICT):
    HEADER ROW INDEX: [Integer]
    COLUMN MAPPINGS:
    - Column 0: [Name]
    ...
    METRICS TO CALCULATE:
    - [Metric 1]
    """
    response = get_llm().invoke(prompt)
    print("\n" + "="*40 + "\n📋 TECHNICAL SPEC:\n" + response.content[:300] + "...\n" + "="*40 + "\n")
    return response.content, schema_info

# ---------------------------------------------------------
# 🚑 AGENT 2: SELF-HEALING CODER
# ---------------------------------------------------------
def run_self_healing_coder(df, plan, schema_info):
    MAX_RETRIES = 3
    current_error = None
    previous_code = ""

    for attempt in range(1, MAX_RETRIES + 2):
        if attempt == 1:
            print(f"👨‍💻 Coder Agent: Initial Attempt...")
            prompt = f"""
            You are a Senior Python Engineer. Implement this Spec on 'df'.
            
            SPEC: {plan}
            SCHEMA: {schema_info}
            
            CRITICAL RULES:
            1. **HEADER FIX**: `df.columns = df.iloc[X]; df = df[X+1:].copy()`
            2. **NUMERICS**: `pd.to_numeric(..., errors='coerce')`.
            3. **ANALYSIS**: PRINT results (sums, counts, averages).
            4. **OVERWRITE**: Update `df` in place.
            
            Wrap code in ```python.
            """
        else:
            print(f"🚑 Debugger Agent: Attempt {attempt} (Fixing Error)...")
            prompt = f"""
            Fix this Python code.
            
            PREVIOUS CODE: {previous_code}
            ERROR: {current_error}
            
            TASK:
            1. Fix bugs.
            2. **ADD PRINT STATEMENTS**: You MUST print analysis results.
            3. Ensure `df` is modified in place.
            """

        response = get_llm().invoke(prompt)
        generated_code = response.content
        previous_code = generated_code 

        result_text, cleaned_df = execute_python_code(generated_code, df)

        if "Error executing code" in result_text:
            current_error = result_text
            print(f"   ⚠️ Failed: {current_error[:60]}...")
            continue 
        elif len(result_text.strip()) < 10:
            current_error = "Code executed but printed NOTHING."
            print(f"   ⚠️ Output empty. Retrying...")
            continue
        else:
            print("   ✅ Success! Analysis Generated.")
            return result_text, cleaned_df 

    return f"FAILED. Last Error: {current_error}", df

# --- MAIN ---
def main(file_path):
    print(f"🎬 Processing: {file_path}")
    
    # 1. Ingest (Handles PDF/DOCX Text & Tables)
    raw_text, tables, config = load_file(file_path)
    
    df = pd.DataFrame()
    
    # 🟢 FIXED LOGIC: Handle List OR Dict types for 'tables'
    if tables:
        if isinstance(tables, list) and len(tables) > 0:
            print(f"   ✅ Found {len(tables)} tables (List). Using the first one.")
            df = tables[0]
        elif isinstance(tables, dict) and len(tables) > 0:
            print(f"   ✅ Found {len(tables)} tables (Dict). Using the first one.")
            # Safely grab the first available dataframe
            df = list(tables.values())[0]
            
    # If no tables found via loader, try smart load (for Excel/CSV)
    if df.empty:
        df = smart_load_table(file_path)

    # PATH A: DATA MODE (If we have a valid table)
    if not df.empty:
        # 2. Analyze & Clean
        plan, schema_info = run_inspector_agent(df)
        analysis_output, cleaned_df = run_self_healing_coder(df, plan, schema_info)
        
        # 3. Visuals
        print("🎨 Generating Charts...")
        charts = []
        try:
            from src.utils.viz_utils import generate_smart_charts
            target_df = cleaned_df if not cleaned_df.empty else df
            if len(target_df) > 0 and len(target_df.columns) > 1:
                charts = generate_smart_charts(target_df, IMAGES_DIR)
                print(f"   ✅ Created {len(charts)} charts.")
        except Exception as e: print(f"   ⚠️ Chart Error: {e}")

        chart_section = "\n## Visual Analytics\n" + "\n".join([f"![{d}]({os.path.relpath(p, ARTIFACTS_DIR).replace(os.sep, '/')})" for d, p in charts]) if charts else ""
        context = f"TECHNICAL SPEC:\n{plan}\n\nDERIVED INSIGHTS:\n{analysis_output}\n\nVISUALS:\nAttached {len(charts)} charts."
        
    # PATH B: TEXT MODE (Brochures/Docs with no data)
    elif raw_text and len(raw_text) > 10:
        print("ℹ️ No structured data found. Switching to TEXT ANALYSIS mode.")
        context = f"DOCUMENT CONTENT:\n{raw_text[:15000]}...\n\nINSTRUCTION: Summarize this brochure/document highlighting key offerings, vision, and details."
        chart_section = ""
        analysis_output = "Text Analysis Mode"
        charts = []
    else:
        print("❌ Error: File contains no readable text or tables.")
        return

    # 4. Write Report
    print("\n--- ✍️ Writing Report ---")
    report = writer_agent(context, "Strategic Analysis")
    
    final_report = report + ("\n" + chart_section if "Visual Analytics" not in report else "")
    out_path = os.path.join(ARTIFACTS_DIR, f"{os.path.basename(file_path)}_report.md")
    with open(out_path, "w", encoding="utf-8") as f: f.write(final_report)
    print(f"✅ Saved: {out_path}")

    # 5. PDF
    print("--- 📕 Generating PDF ---")
    try:
        from src.utils.pdf_utils import convert_markdown_to_pdf_brochure
        if convert_markdown_to_pdf_brochure:
            convert_markdown_to_pdf_brochure(final_report, out_path.replace(".md", ".pdf"), IMAGES_DIR, title=os.path.basename(file_path), chart_list=charts)
            print(f"✅ PDF Created: {out_path.replace('.md', '.pdf')}")
    except: pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path")
    main(parser.parse_args().file_path)