import sys
import os
import argparse
import pandas as pd 
import yaml
from io import StringIO
from langchain_core.messages import HumanMessage

# --- 1. SETUP & DIRECTORIES ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

ARTIFACTS_DIR = os.path.join(project_root, "data", "artifacts")
IMAGES_DIR = os.path.join(ARTIFACTS_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# Import internal modules
from src.rag.file_loader import load_file
from src.engine.agents.analyst import analyst_agent
from src.engine.agents.writer import writer_agent

# 🟢 IMPORT THE CODE EXECUTOR
try:
    from src.engine.tools.code_executor import execute_python_code
except ImportError:
    print("❌ Critical: src/engine/tools/code_executor.py not found.")
    sys.exit(1)

# --- 🟢 DYNAMIC LLM LOADER ---
def load_config():
    config_path = os.path.join(project_root, "config", "settings.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}

def get_llm():
    """Loads Ollama settings from config/settings.yaml"""
    config = load_config()
    llm_config = config.get("llm", {})
    
    # Defaults
    model_name = llm_config.get("reasoning_model", "qwen2.5:0.5b")
    base_url = llm_config.get("base_url", "http://localhost:11434")
    temp = llm_config.get("temperature", 0.1)

    try:
        # 🟢 FIX DEPRECATION WARNING: Use langchain_ollama if available
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            from langchain_community.chat_models import ChatOllama
            
        return ChatOllama(model=model_name, base_url=base_url, temperature=temp)
    except Exception as e:
        print(f"❌ Error initializing Ollama: {e}")
        sys.exit(1)

# --- IMPORT UTILS ---
try:
    from src.utils.data_utils import smart_load_table
except ImportError:
    def smart_load_table(path): return pd.read_csv(path) if path.endswith('.csv') else pd.read_excel(path)

try:
    from src.utils.viz_utils import generate_smart_charts
except ImportError:
    def generate_smart_charts(df, output_dir): return []

try:
    from src.utils.pdf_utils import convert_markdown_to_pdf_brochure
except ImportError:
    convert_markdown_to_pdf_brochure = None

# ---------------------------------------------------------
# 🧠 DYNAMIC CODE GENERATION (WITH SAFETY FILTER)
# ---------------------------------------------------------
def generate_dynamic_summary(df):
    print("🧠 Agent is writing Python analysis code...")
    
    # 1. Get DataFrame Structure
    buffer = StringIO()
    df.info(buf=buffer)
    schema_info = buffer.getvalue()
    
    # 2. Construct Prompt (Simplified for Small Models)
    prompt = f"""
    You are a Python Data Analyst. 
    You have a pandas DataFrame named 'df' loaded in memory.
    
    SCHEMA:
    {schema_info}
    
    TASK:
    Write a Python script to print a summary.
    1. Print total rows: len(df)
    2. Print sum of numerical columns.
    3. Print top 3 values for 'Zone' and 'State' if they exist.
    
    RULES:
    - DO NOT load any files. df is already defined.
    - DO NOT use pd.read_csv or pd.read_excel.
    - Wrap code in ```python blocks.
    - Use print() for all outputs.
    """
    
    # 3. Get Code from LLM
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        code_text = response.content if hasattr(response, 'content') else str(response)
        
        # 🟢 DEBUG: Show what the clumsy AI wrote
        # print(f"\n[DEBUG] AI Generated Code:\n{code_text}\n") 
        
        # 🟢 SAFETY FILTER: Remove file loading attempts
        clean_lines = []
        for line in code_text.split('\n'):
            if "read_csv" in line or "read_excel" in line:
                print(f"   🛡️ Blocked unsafe line: {line.strip()}")
                continue
            clean_lines.append(line)
        code_text = "\n".join(clean_lines)

    except Exception as e:
        print(f"⚠️ LLM Generation Failed: {e}")
        return str(df.describe()) 

    # 4. Execute the Code safely
    result = execute_python_code(code_text, df)
    
    # Check if execution failed
    if "Error executing code" in result:
        print(f"   ⚠️ Code Execution Error: {result}")
        return str(df.describe()) # Fallback to standard stats
        
    return result

# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------
def main(file_path):
    print(f"🎬 Starting Full Report Generation for: {file_path}")
    
    raw_text, tables, config = load_file(file_path)
    created_charts = []

    if file_path.lower().endswith(('.csv', '.xlsx', '.xls')):
        print("⚡ Tabular file detected. Using Smart Loader...")
        
        try:
            df = smart_load_table(file_path)
            
            print("📊 Generating agentic statistical summary...")
            summary = generate_dynamic_summary(df) 
            print(f"   ✅ Agent Analysis Complete.")
            
            print("🎨 Generating visual analytics...")
            created_charts = generate_smart_charts(df, IMAGES_DIR)
            
            if created_charts:
                chart_info = "\n".join([f"- {desc}" for desc, path in created_charts])
            else:
                chart_info = "(No charts could be generated)"

            raw_text = f"""
            SYSTEM GENERATED DATA INTELLIGENCE REPORT
            =========================================
            The following analysis was generated by executing Python code on the raw data.
            It is mathematically accurate.
            
            EXECUTED CODE OUTPUT:
            {summary}

            AVAILABLE VISUALIZATIONS:
            I have already generated the following charts. They will be appended to the report.
            {chart_info}

            WRITER INSTRUCTIONS:
            1. Use the 'EXECUTED CODE OUTPUT' above as the absolute truth.
            2. Report Financials (Revenue, Profit) exactly as calculated.
            3. Analyze insights based on the Top 3 categorical values found.
            4. Do not mention file errors.
            """
            
            tables = [df]
            
        except Exception as e:
            print(f"❌ Error processing table file: {e}")
            import traceback
            traceback.print_exc()
            return

    if not tables and not raw_text:
        print("❌ File is empty or unreadable. Exiting.")
        return

    print("\n--- ✍️ Step 3: Writing Final Report ---")
    final_report = writer_agent(context_text=raw_text, analysis_result="Generated via Code Interpreter")
    
    report_filename = os.path.splitext(os.path.basename(file_path))[0] + "_report.md"
    report_path = os.path.join(ARTIFACTS_DIR, report_filename)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_report)
        
    print(f"\n✅ SUCCESS! Report saved to: {report_path}")

    if convert_markdown_to_pdf_brochure:
        print("\n--- 📕 Step 4: Generating PDF Brochure ---")
        pdf_filename = os.path.splitext(os.path.basename(file_path))[0] + "_brochure.pdf"
        pdf_path = os.path.join(ARTIFACTS_DIR, pdf_filename)
        
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        report_title = base_name.replace("_", " ").replace("-", " ").title()
        
        try:
            convert_markdown_to_pdf_brochure(
                final_report, 
                pdf_path, 
                IMAGES_DIR,
                title=report_title,
                subtitle="Agentic AI Analysis",
                chart_list=created_charts 
            )
            print(f"✅ PDF SUCCESS! Brochure saved to: {pdf_path}")
        except Exception as e:
            print(f"❌ PDF Generation Failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a full AI report from a file.")
    parser.add_argument("file_path", help="Path to the data file (PDF, XLSX, CSV, DOCX, TXT)")
    args = parser.parse_args()
    
    main(args.file_path)