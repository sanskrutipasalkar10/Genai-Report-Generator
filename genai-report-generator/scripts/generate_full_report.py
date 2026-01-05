import sys
import os
from langchain_core.messages import HumanMessage

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.rag.parsers.pdf_parser import parse_hybrid_pdf
from src.engine.agents.scanner import scanner_agent
from src.engine.agents.analyst import analyst_agent
from src.engine.agents.writer import writer_agent

def main(file_path):
    print(f"🎬 Starting Full Report Generation for: {file_path}")
    
    # --- PHASE 1: INGESTION ---
    # Extract both Text (for context) and Tables (for math)
    raw_text, tables = parse_hybrid_pdf(file_path)
    
    if not tables:
        print("❌ No tables found. Switching to text-only summary mode.")
        # In a real app, you would handle text-only reports here
        return

    # --- PHASE 2: PLANNING (Scanner) ---
    print("\n--- 🧠 Step 2: Scanning Data ---")
    scan_result = scanner_agent(tables)
    print(f"Strategy: {scan_result['analysis_summary']}")
    
    # --- PHASE 3: EXECUTION (Analyst) ---
    print("\n--- 🤖 Step 3: Analyzing Data ---")
    
    # We ask the Analyst to compute the sum to simulate a KPI extraction.
    # In the API version, the user would ask "What is the total revenue?"
    task = "Calculate the total sum of all Revenue and Cost columns."
    
    analyst_state = {
        "messages": [HumanMessage(content=task)],
        "data": scan_result['primary_dataframe']
    }
    
    analyst_output = analyst_agent(analyst_state)
    final_metric = analyst_output['final_answer']
    
    # --- PHASE 4: REPORTING (Writer) ---
    print("\n--- ✍️ Step 4: Writing Final Report ---")
    
    # The writer gets the 'Vibe' (raw_text) and the 'Fact' (final_metric)
    final_report = writer_agent(
        context_text=raw_text, 
        analysis_result=f"The total financial volume (Revenue + Cost) for the period is: {final_metric}"
    )
    
    # --- SAVE OUTPUT ---
    output_dir = "data/artifacts"
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/executive_summary.md"
    
    with open(output_path, "w") as f:
        f.write(final_report)
        
    print(f"\n✅ SUCCESS! Report saved to: {output_path}")
    print("="*60)
    print(final_report)
    print("="*60)

if __name__ == "__main__":
    # Ensure we use the PDF we created earlier
    pdf_file = "data/raw/sample_with_table.pdf"
    
    if os.path.exists(pdf_file):
        main(pdf_file)
    else:
        print("Please run 'scripts/create_test_pdf.py' first.")