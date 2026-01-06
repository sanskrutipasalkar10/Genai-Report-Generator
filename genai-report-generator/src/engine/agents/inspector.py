import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from src.engine.llm import get_llm

# 🟢 GENERALIZED PROMPT: Covers all standard business terminologies
INSPECTOR_PROMPT = """
You are a Senior Data Architect. Analyze the provided raw data snippet (first 300 rows).
Categorize the document and generate a JSON configuration.

### 1. FINANCIAL REPORT
**Keywords to look for:** - Revenue, Sales, Turnover, Gross Receipts, Top Line
- EBITDA, OIBDA, Operating Profit, EBIT
- Net Income, Net Profit, PAT (Profit After Tax), Surplus, Bottom Line
- Assets, Liabilities, Equity, Balance Sheet, P&L, Cash Flow
**Structure:** Usually Row-Based (Metrics in Col A, Values in Col B).

### 2. OPERATIONAL REPORT
**Keywords to look for:**
- Quantity, Qty, Units, Volume, Count, Stock, Inventory
- SKU, Product ID, Order ID, Transaction ID
- FTE, Headcount, Hours, Utilization, Efficiency
- Sales Rep, Region, Zone, Territory
**Structure:** Usually Column-Based (Headers in Row 1, Data below).

### OUTPUT JSON FORMAT:
{
    "report_type": "FINANCIAL" or "OPERATIONAL",
    "data_structure": "ROW_BASED" or "COLUMN_BASED",
    "header_row_index": <int> (The row number where headers likely start, 0-indexed),
    "rag_config": {
        "chunk_size": 1000,
        "chunk_overlap": 200
    }
}
"""

def inspect_file(raw_preview: str, file_name: str) -> dict:
    print(f"--- 🕵️ Inspector Agent: Analyzing {file_name} ---")
    llm = get_llm() # Connects to Qwen-Cloud
    
    messages = [
        SystemMessage(content=INSPECTOR_PROMPT),
        HumanMessage(content=f"FILENAME: {file_name}\n\nRAW CONTENT PREVIEW:\n{raw_preview}")
    ]
    
    response = llm.invoke(messages)
    content = response.content.strip()
    
    try:
        # Robust JSON Extraction
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            config = json.loads(json_match.group(0))
            print(f"   ✅ Report Identified: {config.get('report_type')} ({config.get('data_structure')})")
            return config
        else:
            raise ValueError("No JSON found")
            
    except Exception as e:
        print(f"   ⚠️ Inspection Warning: {e}. Defaulting to OPERATIONAL.")
        return {"report_type": "OPERATIONAL", "data_structure": "COLUMN_BASED", "header_row_index": 0}