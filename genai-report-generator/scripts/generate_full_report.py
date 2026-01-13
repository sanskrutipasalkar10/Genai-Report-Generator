import sys
import os
import argparse
import pandas as pd
import json
import logging

# --- SETUP & LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

ARTIFACTS_DIR = os.path.join(project_root, "data", "artifacts")
IMAGES_DIR = os.path.join(ARTIFACTS_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# --- IMPORT MODULES ---
from src.utils.data_sanitizer import DataSanitizer
from src.engine.agents.inspector import InspectorAgent
from src.engine.agents.analyst import AnalystAgent
from src.engine.agents.writer import writer_agent
from src.utils.viz_utils import generate_smart_charts
from src.rag.file_loader import load_file
from src.engine.llm import get_llm

def run_summary_agent(insights):
    """
    Synthesizes the raw analysis into an Executive Summary.
    """
    print("\n🧠 [Summary Agent] Synthesizing insights...")
    llm = get_llm()
    prompt = f"""
    You are an Executive Analyst. Write a high-level **Executive Summary** (max 200 words).
    
    DATA INSIGHTS:
    {insights}
    
    FOCUS:
    - Highlight key numbers (Revenue, Totals).
    - Identify top trends or anomalies.
    - Be concise and professional.
    """
    return llm.invoke(prompt).content

def main(file_path):
    print(f"\n🎬 [Pipeline] Starting: {file_path}")
    
    # ---------------------------------------------------------
    # 1. INGEST & SANITIZE (The "Janitor")
    # ---------------------------------------------------------
    print("\n--- PHASE 1: SANITIZATION (Python) ---")
    
    # Try loading as text/tables first (for PDF/DOCX or Excel via Parser)
    raw_text, tables, _ = load_file(file_path)
    
    df = pd.DataFrame()
    
    # PATH A: TABLES FOUND VIA LOADER
    if tables:
        print("   🚿 Sanitizing Extracted Tables...")
        # Handle if tables is List or Dict
        raw_df = tables[0] if isinstance(tables, list) else list(tables.values())[0]
        
        # 🟢 CRITICAL FIX: Use the FULL pipeline on the dataframe
        # This ensures we run Header Detection on extracted tables too
        df = DataSanitizer.clean_dataframe(raw_df)
        
    # PATH B: STRICT LOAD (Fallback for Excel/CSV if loader return empty/bad structure)
    if df.empty:
        print("   🚿 Running Strict File Sanitization...")
        df = DataSanitizer.clean_file(file_path)

    # ---------------------------------------------------------
    # PATH C: PROCESS VALID DATA
    # ---------------------------------------------------------
    if not df.empty:
        # 2. INSPECT (The "Architect")
        print("\n--- PHASE 2: INSPECTION (LLM) ---")
        inspector = InspectorAgent()
        plan = inspector.inspect_and_plan(df)
        
        # 3. ANALYZE (The "Executor")
        print("\n--- PHASE 3: ANALYSIS (Code) ---")
        analyst = AnalystAgent()
        insights, _ = analyst.perform_analysis(df, plan)
        
        # 4. SUMMARIZE
        print("\n--- PHASE 4: SUMMARIZATION ---")
        if "Analysis Failed" in insights:
            summary = "Automated analysis could not be completed due to execution errors."
        else:
            summary = run_summary_agent(insights)
            
        # 5. VISUALIZE
        print("\n--- PHASE 5: VISUALIZATION ---")
        charts = generate_smart_charts(df, IMAGES_DIR)
        print(f"   ✅ Generated {len(charts)} charts.")
        
        # Prepare Context for Final Report
        full_context = f"""
        EXECUTIVE SUMMARY:
        {summary}
        
        DETAILED FINDINGS:
        {insights}
        
        VISUAL EVIDENCE:
        Attached {len(charts)} charts.
        """

    # ---------------------------------------------------------
    # PATH D: TEXT ONLY MODE (Brochures/Docs)
    # ---------------------------------------------------------
    elif raw_text and len(raw_text) > 50:
        print("\nℹ️ No structured data found. Switching to Text Mode.")
        summary = run_summary_agent(raw_text[:5000])
        full_context = f"""
        EXECUTIVE SUMMARY:
        {summary}
        
        DOCUMENT CONTENT:
        {raw_text[:15000]}
        """
        charts = []
    else:
        print("❌ Error: File contains no readable text or tables.")
        return

    # ---------------------------------------------------------
    # 6. REPORT GENERATION
    # ---------------------------------------------------------
    print("\n--- PHASE 6: FINAL REPORT ---")
    report = writer_agent(full_context, "Strategic Report")
    
    # Append Visuals
    if charts:
        report += "\n## Visual Analytics\n" + "\n".join([f"![{n}]({os.path.relpath(p, ARTIFACTS_DIR).replace(os.sep, '/')})" for n,p in charts])

    # Save Markdown
    out_name = f"{os.path.basename(file_path)}_report.md"
    out_path = os.path.join(ARTIFACTS_DIR, out_name)
    with open(out_path, "w", encoding="utf-8") as f: f.write(report)
    print(f"✅ Report Saved: {out_path}")

    # Generate PDF
    print("\n--- PHASE 7: PDF CONVERSION ---")
    try:
        from src.utils.pdf_utils import convert_markdown_to_pdf_brochure
        convert_markdown_to_pdf_brochure(report, out_path.replace(".md", ".pdf"), IMAGES_DIR, title=os.path.basename(file_path), chart_list=charts)
        print(f"✅ PDF Created: {out_path.replace('.md', '.pdf')}")
    except Exception as e:
        print(f"⚠️ PDF Generation Failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path")
    args = parser.parse_args()
    
    # Ensure debug mode is on for LLM visibility
    os.environ["DEBUG_MODE"] = "True"
    
    main(args.file_path)