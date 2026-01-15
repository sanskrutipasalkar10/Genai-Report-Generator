import sys
import os
import argparse
import pandas as pd
import json
import logging
from langchain_core.messages import HumanMessage

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
from src.engine.llm import get_llm, get_vision_model 
from src.utils.image_extractor import extract_images_from_file 

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

def run_visual_analysis(file_path):
    """
    Extracts images and uses Vision Model to describe them.
    """
    print("\n--- PHASE 1.5: VISUAL ANALYSIS (Vision Model) ---")
    visual_report = ""
    
    # 1. Extract Images
    print(f"   👁️ Scanning {os.path.basename(file_path)} for embedded images...")
    images_b64 = extract_images_from_file(file_path)
    
    if not images_b64:
        print("      No extractable images found.")
        return ""
    
    print(f"      Found {len(images_b64)} images. Analyzing with qwen3-vl...")
    
    # 2. Analyze with Vision Model
    vision_llm = get_vision_model()
    
    for i, img_b64 in enumerate(images_b64):
        print(f"      🖼️ Processing Image {i+1}/{len(images_b64)}...")
        
        # Prepare Multimodal Message
        msg_content = {
            "text": "Analyze this image for a business report. Describe charts, trends, or key details visible.",
            "image_base64": img_b64
        }
        
        try:
            # Wrap dictionary in a list to satisfy HumanMessage validation
            response = vision_llm.invoke([HumanMessage(content=[msg_content])])
            desc = response.content
            visual_report += f"\n**Visual Exhibit {i+1} Analysis:**\n{desc}\n"
        except Exception as e:
            logger.error(f"      ❌ Failed to analyze image {i+1}: {e}")
            
    return visual_report

def main(file_path):
    print(f"\n🎬 [Pipeline] Starting: {file_path}")
    
    # ---------------------------------------------------------
    # 1. INGEST & SANITIZE 
    # ---------------------------------------------------------
    print("\n--- PHASE 1: SANITIZATION (Python) ---")
    raw_text, tables, _ = load_file(file_path)
    df = pd.DataFrame()
    
    if tables:
        print("   🚿 Sanitizing Extracted Tables...")
        raw_df = tables[0] if isinstance(tables, list) else list(tables.values())[0]
        df = DataSanitizer.clean_dataframe(raw_df)
        
    if df.empty:
        print("   🚿 Running Strict File Sanitization...")
        df = DataSanitizer.clean_file(file_path)

    # ---------------------------------------------------------
    # 1.5 VISUAL ANALYSIS (The New Feature)
    # ---------------------------------------------------------
    # Run this regardless of whether tabular data was found
    visual_analysis_text = run_visual_analysis(file_path)

    # ---------------------------------------------------------
    # PROCESS VALID DATA
    # ---------------------------------------------------------
    full_context = ""
    charts = []

    # PATH A: Structured Data (Excel/CSV/Table)
    if not df.empty:
        print("\n--- PHASE 2: INSPECTION (LLM) ---")
        inspector = InspectorAgent()
        plan = inspector.inspect_and_plan(df)
        
        print("\n--- PHASE 3: ANALYSIS (Code) ---")
        analyst = AnalystAgent()
        insights, _ = analyst.perform_analysis(df, plan)
        
        print("\n--- PHASE 4: SUMMARIZATION ---")
        summary = run_summary_agent(insights)
            
        print("\n--- PHASE 5: VISUALIZATION ---")
        charts = generate_smart_charts(df, IMAGES_DIR)
        print(f"   ✅ Generated {len(charts)} charts.")
        
        full_context = f"""
        EXECUTIVE SUMMARY:
        {summary}
        
        DETAILED FINDINGS:
        {insights}
        
        VISUAL ANALYSIS (FROM EMBEDDED IMAGES):
        {visual_analysis_text}
        
        GENERATED CHARTS:
        Attached {len(charts)} charts.
        """

    # PATH B: Text Documents (PDF/Docx with Text)
    elif raw_text and len(raw_text) > 50:
        print("\nℹ️ No structured data found. Switching to Text Mode.")
        summary = run_summary_agent(raw_text[:5000])
        full_context = f"""
        EXECUTIVE SUMMARY:
        {summary}
        
        VISUAL ANALYSIS (FROM EMBEDDED IMAGES):
        {visual_analysis_text}
        
        DOCUMENT CONTENT:
        {raw_text[:15000]}
        """
        
    # PATH C: Image-Only Documents (Scanned PDFs / Charts) - 🟢 NEW
    elif visual_analysis_text:
        print("\nℹ️ No Text/Tables found, but Visual Analysis is available. Generating Image-Based Report.")
        summary = run_summary_agent(visual_analysis_text)
        full_context = f"""
        EXECUTIVE SUMMARY:
        {summary}
        
        VISUAL ANALYSIS (FROM EMBEDDED IMAGES):
        {visual_analysis_text}
        
        NOTE:
        This report is based solely on the visual analysis of images found in the document, 
        as no extractable text or tabular data was detected.
        """
        
    else:
        print("❌ Error: File contains no readable text, tables, or images.")
        return

    # ---------------------------------------------------------
    # 6. REPORT GENERATION
    # ---------------------------------------------------------
    print("\n--- PHASE 6: FINAL REPORT ---")
    report = writer_agent(full_context, "Strategic Report")
    
    # Append Visuals
    if charts:
        report += "\n## Generated Analytics\n" + "\n".join([f"![{n}]({os.path.relpath(p, ARTIFACTS_DIR).replace(os.sep, '/')})" for n,p in charts])

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
    os.environ["DEBUG_MODE"] = "True"
    main(args.file_path)