import sys
import os

# Setup Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.rag.parsers.pdf_parser import parse_hybrid_pdf
from src.engine.agents.scanner import scanner_agent
from src.engine.agents.analyst import analyst_agent
from langchain_core.messages import HumanMessage

def run_pipeline(pdf_path):
    print(f"🚀 Processing: {pdf_path}")
    
    # 1. HYBRID PARSING
    # We get text (for RAG) AND tables (for Analyst)
    raw_text, tables = parse_hybrid_pdf(pdf_path)
    
    if not tables:
        print("❌ No tables found. Switching to text-only mode.")
        return

    # 2. SCANNER AGENT
    # "See what calculations we can do"
    print("\n--- 🧠 Scanner Agent Working ---")
    scan_result = scanner_agent(tables)
    print(scan_result['analysis_summary'])
    
    # 3. ANALYST AGENT
    # Now we perform a specific calculation based on the scan
    print("\n--- 🤖 Analyst Agent Working ---")
    
    # We automatically ask it to do one of the calculations found, 
    # or let the user ask. Here we simulate a user question.
    user_q = "Based on the data, calculate the total sum of the numerical column."
    
    state = {
        "messages": [HumanMessage(content=user_q)],
        "data": scan_result['primary_dataframe'] # Pass the extracted PDF table!
    }
    
    final_result = analyst_agent(state)
    print(f"\n✅ Final Calculation:\n{final_result['final_answer']}")

if __name__ == "__main__":
    # Point this to a real PDF with a table on your computer
    # If you don't have one, the script will fail at the parsing step.
    pdf_file = "data/raw/sample_with_table.pdf" 
    
    if os.path.exists(pdf_file):
        run_pipeline(pdf_file)
    else:
        print(f"Please place a PDF with a table at {pdf_file} to test this.")