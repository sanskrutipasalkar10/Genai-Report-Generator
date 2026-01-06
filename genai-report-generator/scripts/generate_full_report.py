import sys
import os
import argparse
import pandas as pd 
from langchain_core.messages import HumanMessage

# --- 1. SETUP & DIRECTORIES ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Define where to save the reports
ARTIFACTS_DIR = os.path.join(project_root, "data", "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# Import internal modules
from src.rag.file_loader import load_file
from src.engine.agents.analyst import analyst_agent
from src.engine.agents.writer import writer_agent

# --- IMPORT SUMMARIZER ---
try:
    from src.utils.data_utils import summarize_dataframe
except ImportError:
    # Fallback to prevent crash if file is missing
    print("⚠️ Warning: src/utils/data_utils.py not found. Creating simple summary.")
    def summarize_dataframe(df): return str(df.describe())

def main(file_path):
    print(f"🎬 Starting Full Report Generation for: {file_path}")
    
    # --- PHASE 1: UNIVERSAL INGESTION ---
    raw_text, tables, config = load_file(file_path)
    
    # 🔴 FORCE DATA HANDLING FOR CSV/EXCEL
    # Even if load_file returned text, we discard it and force aggregation for structured files.
    if file_path.lower().endswith(('.csv', '.xlsx', '.xls')):
        print("⚡ Tabular file detected. Forcing Smart Aggregation...")
        
        try:
            # 1. Force Load DataFrame
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # 2. Force Summary Generation
            summary = summarize_dataframe(df)
            
            # 3. OVERRIDE raw_text
            # This ensures the Writer Agent NEVER sees the raw rows
            raw_text = f"""
            DATASET SUMMARY (Aggregated from {len(df)} rows):
            {summary}
            """
            
            # 4. Ensure tables is populated for the Analyst
            tables = [df]
            
            print(f"✅ Data Compressed: {len(df)} rows converted to {len(summary.splitlines())} lines of summary.")
            
        except Exception as e:
            print(f"❌ Error reading table file: {e}")
            return

    # 🟢 VALIDATION
    if not tables and not raw_text:
        print("❌ File is empty or unreadable. Exiting.")
        return

    report_type = config.get("report_type", "GENERAL_TEXT")
    print(f"🔍 Inspector identified Report Type: {report_type}")

    # --- PHASE 2: ANALYSIS (Conditional) ---
    final_metric = "N/A (Text Analysis Only)"
    
    if tables:
        print("\n--- 🤖 Step 2: Analyzing Data ---")
        
        if report_type == "FINANCIAL":
            task = "Analyze the P&L trends. Calculate total revenue and EBITDA margin."
        else:
            task = "Calculate the total volume/sum of the main numerical metrics."

        analyst_state = {
            "messages": [HumanMessage(content=task)],
            "data": tables, 
            "config": config 
        }
        
        try:
            # Only run analyst if we have a real agent, otherwise skip to save time
            analyst_output = analyst_agent(analyst_state)
            final_metric = analyst_output['final_answer']
        except Exception as e:
            print(f"⚠️ Analyst Warning: {e}")
            final_metric = "Error in Data Analysis"
    else:
        print("\n--- 🤖 Step 2: Analyst Skipped (No Data Tables found) ---")

    # --- PHASE 3: REPORTING (Writer) ---
    print("\n--- ✍️ Step 3: Writing Final Report ---")
    
    # DEBUG: Show user what is being sent to the writer
    print(f"ℹ️ Input to Writer Agent (First 200 chars): {raw_text[:200]}...")
    
    final_report = writer_agent(
        context_text=raw_text, 
        analysis_result=final_metric
    )
    
    # --- 4. SAVE THE REPORT ---
    report_filename = os.path.splitext(os.path.basename(file_path))[0] + "_report.md"
    report_path = os.path.join(ARTIFACTS_DIR, report_filename)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_report)
        
    print(f"\n✅ SUCCESS! Report saved to: {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a full AI report from a file.")
    parser.add_argument("file_path", help="Path to the data file (PDF, XLSX, CSV, DOCX, TXT)")
    args = parser.parse_args()
    
    main(args.file_path)