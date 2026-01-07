import sys
import os
import argparse
import pandas as pd 
from langchain_core.messages import HumanMessage

# --- 1. SETUP & DIRECTORIES ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Define where to save the reports and images
ARTIFACTS_DIR = os.path.join(project_root, "data", "artifacts")
IMAGES_DIR = os.path.join(ARTIFACTS_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# Import internal modules
from src.rag.file_loader import load_file
from src.engine.agents.analyst import analyst_agent
from src.engine.agents.writer import writer_agent

# --- IMPORT SMART UTILS ---
try:
    from src.utils.data_utils import summarize_dataframe, smart_load_table
except ImportError:
    print("⚠️ Warning: src/utils/data_utils.py not found. Using basic fallback.")
    def summarize_dataframe(df): return str(df.describe())
    def smart_load_table(path): return pd.read_csv(path) if path.endswith('.csv') else pd.read_excel(path)

# --- IMPORT VISUALIZATION UTILS ---
try:
    from src.utils.viz_utils import generate_smart_charts
except ImportError:
    print("⚠️ Warning: src/utils/viz_utils.py not found. Charts will be skipped.")
    def generate_smart_charts(df, output_dir): return []

# --- IMPORT PDF UTILS (NEW) ---
try:
    from src.utils.pdf_utils import convert_markdown_to_pdf_brochure
except ImportError:
    print("⚠️ Warning: src/utils/pdf_utils.py not found. PDF Brochure generation will be skipped.")
    convert_markdown_to_pdf_brochure = None

def main(file_path):
    print(f"🎬 Starting Full Report Generation for: {file_path}")
    
    # --- PHASE 1: UNIVERSAL INGESTION ---
    raw_text, tables, config = load_file(file_path)
    
    # Variable to hold charts for the PDF step
    created_charts = []

    # 🔴 FORCE DATA HANDLING FOR CSV/EXCEL
    if file_path.lower().endswith(('.csv', '.xlsx', '.xls')):
        print("⚡ Tabular file detected. Using Smart Loader & Aggregation...")
        
        try:
            # 1. Use Smart Loader
            df = smart_load_table(file_path)
            
            # 2. Generate Statistical Summary
            print("📊 Generating comprehensive statistical summary...")
            summary = summarize_dataframe(df)
            
            # 3. GENERATE CHARTS
            print("🎨 Generating visual analytics...")
            created_charts = generate_smart_charts(df, IMAGES_DIR)
            
            # Format chart info for the AI (Just for context, not for embedding anymore)
            if created_charts:
                chart_info = "\n".join([f"- {desc}" for desc, path in created_charts])
                print(f"✅ Generated {len(created_charts)} charts in {IMAGES_DIR}")
            else:
                chart_info = "(No charts could be generated due to data format)"

            # 4. OVERRIDE raw_text with ENRICHED CONTEXT
            raw_text = f"""
            SYSTEM GENERATED DATA INTELLIGENCE REPORT
            =========================================
            This is a pre-computed statistical summary of the raw dataset. 
            
            DATA SUMMARY:
            {summary}

            AVAILABLE VISUALIZATIONS:
            I have already generated the following charts. You do NOT need to insert them. 
            They will be appended to the end of the report automatically.
            {chart_info}

            WRITER INSTRUCTIONS:
            1. FINANCIALS: Report Total Revenue, Units Sold, and Gross Profit.
            2. INSIGHTS: Analyze demographics, product mix, and correlations.
            3. FORMAT: Use Markdown headers (#, ##) clearly.
            4. NOTE: Do not write "Refer to the chart below" as charts are in the appendix.
            """
            
            # 5. Update tables for Analyst
            tables = [df]
            
        except Exception as e:
            print(f"❌ Error processing table file: {e}")
            import traceback
            traceback.print_exc()
            return

    # 🟢 VALIDATION
    if not tables and not raw_text:
        print("❌ File is empty or unreadable. Exiting.")
        return

    report_type = config.get("report_type", "GENERAL_TEXT")

    # --- PHASE 2: ANALYSIS (Conditional) ---
    final_metric = "N/A (Text Analysis Only)"
    
    if tables:
        print("\n--- 🤖 Step 2: Analyzing Data ---")
        if report_type == "FINANCIAL":
            task = "Analyze the P&L trends. Calculate total revenue and EBITDA margin."
        else:
            task = "Calculate the total volume/sum of the main numerical metrics."

        analyst_state = {"messages": [HumanMessage(content=task)], "data": tables, "config": config}
        
        try:
            analyst_output = analyst_agent(analyst_state)
            final_metric = analyst_output['final_answer']
        except Exception as e:
            print(f"⚠️ Analyst Warning: {e}")
            final_metric = "Error in Data Analysis"

    # --- PHASE 3: REPORTING (Writer) ---
    print("\n--- ✍️ Step 3: Writing Final Report ---")
    final_report = writer_agent(context_text=raw_text, analysis_result=final_metric)
    
    # --- 4. SAVE THE REPORT ---
    report_filename = os.path.splitext(os.path.basename(file_path))[0] + "_report.md"
    report_path = os.path.join(ARTIFACTS_DIR, report_filename)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_report)
        
    print(f"\n✅ SUCCESS! Report saved to: {report_path}")

    # --- 5. GENERATE PDF BROCHURE (VISUAL DASHBOARD STRATEGY) ---
    if convert_markdown_to_pdf_brochure:
        print("\n--- 📕 Step 4: Generating PDF Brochure ---")
        pdf_filename = os.path.splitext(os.path.basename(file_path))[0] + "_brochure.pdf"
        pdf_path = os.path.join(ARTIFACTS_DIR, pdf_filename)
        
        # Dynamic Title Logic
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        report_title = base_name.replace("_", " ").replace("-", " ").title()
        report_subtitle = "Automated AI Intelligence Report"
        
        try:
            # 🟢 WE PASS THE 'created_charts' LIST HERE
            convert_markdown_to_pdf_brochure(
                final_report, 
                pdf_path, 
                IMAGES_DIR,
                title=report_title,
                subtitle=report_subtitle,
                chart_list=created_charts 
            )
            print(f"✅ PDF SUCCESS! Brochure saved to: {pdf_path}")
        except Exception as e:
            print(f"❌ PDF Generation Failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a full AI report from a file.")
    parser.add_argument("file_path", help="Path to the data file (PDF, XLSX, CSV, DOCX, TXT)")
    args = parser.parse_args()
    
    main(args.file_path)