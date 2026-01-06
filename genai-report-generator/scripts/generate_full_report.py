import sys
import os
import argparse
from langchain_core.messages import HumanMessage

# --- 1. SETUP & DIRECTORIES ---
# Get the absolute path of the project root to ensure imports work from anywhere
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

def main(file_path):
    print(f"🎬 Starting Full Report Generation for: {file_path}")
    
    # --- PHASE 1: UNIVERSAL INGESTION ---
    # Unpack 3 values: Raw Text (for summary), Tables (for math), Config (metadata)
    raw_text, tables, config = load_file(file_path)
    
    # 🟢 VALIDATION: Only exit if BOTH text and tables are missing.
    # This allows Excel (Tables) and Word/PDF (Text) to both pass.
    if not tables and not raw_text:
        print("❌ File is empty or unreadable. Exiting.")
        return

    report_type = config.get("report_type", "GENERAL_TEXT")
    print(f"🔍 Inspector identified Report Type: {report_type}")

    # --- PHASE 2: ANALYSIS (Conditional) ---
    final_metric = "N/A (Text Analysis Only)"
    
    # Only run the Analyst Agent if we actually have tables to calculate things.
    if tables:
        print("\n--- 🤖 Step 2: Analyzing Data ---")
        
        # Dynamic Task Assignment
        if report_type == "FINANCIAL":
            task = "Analyze the P&L trends. Calculate total revenue and EBITDA margin."
        else:
            task = "Calculate the total volume/sum of the main numerical metrics."

        # Prepare state for the agent
        analyst_state = {
            "messages": [HumanMessage(content=task)],
            "data": tables, # Passes ALL Excel sheets here
            "config": config 
        }
        
        try:
            analyst_output = analyst_agent(analyst_state)
            final_metric = analyst_output['final_answer']
        except Exception as e:
            print(f"⚠️ Analyst Warning: Could not analyze tables. {e}")
            final_metric = "Error in Data Analysis"
    else:
        print("\n--- 🤖 Step 2: Analyst Skipped (No Data Tables found) ---")

    # --- PHASE 3: REPORTING (Writer) ---
    print("\n--- ✍️ Step 3: Writing Final Report ---")
    
    # The Writer works with EITHER raw_text OR analysis_result OR both
    final_report = writer_agent(
        context_text=raw_text, 
        analysis_result=final_metric
    )
    
    # --- 4. SAVE THE REPORT ---
    report_filename = os.path.splitext(os.path.basename(file_path))[0] + "_report.md"
    report_path = os.path.join(ARTIFACTS_DIR, report_filename)
    
    # 🟢 ENCODING FIX: Use utf-8 to prevent crashes with currency symbols (₹, $, etc.)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_report)
        
    print(f"\n✅ SUCCESS! Report saved to: {report_path}")
    print("="*60)
    print(final_report)
    print("="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a full AI report from a file.")
    parser.add_argument("file_path", help="Path to the data file (PDF, XLSX, CSV, DOCX, TXT)")
    args = parser.parse_args()
    
    main(args.file_path)