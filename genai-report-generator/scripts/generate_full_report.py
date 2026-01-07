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

# --- IMPORT SMART UTILS ---
# We import both the summarizer and the smart loader
try:
    from src.utils.data_utils import summarize_dataframe, smart_load_table
except ImportError:
    print("⚠️ Warning: src/utils/data_utils.py not found. Using basic fallback.")
    # Fallback definitions to prevent crash
    def summarize_dataframe(df): return str(df.describe())
    def smart_load_table(path): 
        return pd.read_csv(path) if path.endswith('.csv') else pd.read_excel(path)

def main(file_path):
    print(f"🎬 Starting Full Report Generation for: {file_path}")
    
    # --- PHASE 1: UNIVERSAL INGESTION ---
    raw_text, tables, config = load_file(file_path)
    
    # 🔴 FORCE DATA HANDLING FOR CSV/EXCEL
    # If it is a structured file, we ignore the raw text dump and use Smart Aggregation.
    if file_path.lower().endswith(('.csv', '.xlsx', '.xls')):
        print("⚡ Tabular file detected. Using Smart Loader & Aggregation...")
        
        try:
            # 1. Use Smart Loader (Handles merged headers, metadata rows)
            df = smart_load_table(file_path)
            
            # 2. Generate Elaborated Summary (Includes Outliers, Financial Sums, Missing Vals)
            print("📊 Generating comprehensive statistical summary...")
            summary = summarize_dataframe(df)
            
            # 3. OVERRIDE raw_text with ENRICHED CONTEXT
            # This prompt ensures the Writer Agent looks for specific insights
            raw_text = f"""
            SYSTEM GENERATED DATA INTELLIGENCE REPORT
            =========================================
            This is a pre-computed statistical summary of the raw dataset. 
            Do NOT complain about missing data. Use the statistics below to write the report.

            DATA SUMMARY:
            {summary}

            WRITER INSTRUCTIONS:
            1. FINANCIALS: Look for the 'FINANCIAL & VOLUME TOTALS' section. You MUST report the Total Revenue, Total Units Sold, and Gross Profit if available.
            2. DEMOGRAPHICS: Analyze the 'Customer_Age', 'Gender', and 'Location' (State/Zone) columns.
            3. PRODUCT MIX: Detail the 'Model', 'Variant', and 'Fuel_Type' breakdown.
            4. PERFORMANCE: Analyze 'NPS' (Net Promoter Score) and 'OTD_Days' (Delivery Time) if present.
            5. CORRELATIONS: If you see high discounts and high sales, mention that relationship.
            """
            
            # 4. Update 'tables' for the Analyst Agent
            # We keep the cleaned DataFrame here in case the Analyst needs to run specific math.
            tables = [df]
            
            print(f"✅ Data Processed: {len(df)} rows compressed into {len(summary.splitlines())} lines of insight.")
            
        except Exception as e:
            print(f"❌ Error processing table file: {e}")
            # If smart load fails, we return early to avoid generating a garbage report
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
    print(f"ℹ️ Input to Writer Agent (First 500 chars):\n{raw_text[:500]}...\n")
    
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