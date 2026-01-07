import pandas as pd
import numpy as np
import io

# ==========================================
# PART 1: SMART LOADING
# ==========================================

def find_header_row(file_path, file_ext):
    """Scans first 15 rows to find the row with the most text (the real header)."""
    try:
        if file_ext == '.csv':
            preview = pd.read_csv(file_path, header=None, nrows=15)
        else:
            preview = pd.read_excel(file_path, header=None, nrows=15)
        
        max_score = -1
        best_row_idx = 0
        
        for idx, row in preview.iterrows():
            # Count non-empty strings in row
            score = row.apply(lambda x: isinstance(x, str) and len(x.strip()) > 0).sum()
            if score > max_score:
                max_score = score
                best_row_idx = idx
        return best_row_idx
    except Exception:
        return 0

def smart_load_table(file_path):
    """Robust loader handling merged headers and metadata rows."""
    file_ext = '.' + file_path.split('.')[-1].lower()
    try:
        header_row = find_header_row(file_path, file_ext)
        if file_ext == '.csv':
            df = pd.read_csv(file_path, header=header_row)
        else:
            df = pd.read_excel(file_path, header=header_row)
            
        # Clean column names
        clean_cols = []
        for col in df.columns:
            clean = str(col).strip().replace("\n", " ")
            if "Unnamed" in clean and df[col].isnull().all():
                clean = "__DROP__"
            clean_cols.append(clean)
        df.columns = clean_cols
        return df.drop(columns=[c for c in df.columns if "__DROP__" in c])
    except Exception:
        return pd.read_csv(file_path) if file_ext == '.csv' else pd.read_excel(file_path)

# ==========================================
# PART 2: ELABORATED SUMMARY (THE UPGRADE)
# ==========================================

def summarize_dataframe(df, max_categories=15):
    """
    Generates a deep-dive summary ensuring NO column is ignored.
    Specifically targets Financials (Sums) and Metrics (Means).
    """
    summary = []
    total_rows = len(df)
    
    # 1. High-Level Snapshot
    summary.append("=== 📊 DATASET COMPREHENSIVE REPORT ===")
    summary.append(f"Total Records: {total_rows:,}")
    summary.append(f"Total Columns: {len(df.columns)}")
    
    # 2. Heuristic: Identify 'Financial' vs 'Metric' columns
    # We look for keywords to decide if we should show SUM (Totals)
    sum_keywords = ['revenue', 'profit', 'cost', 'amount', 'sales', 'units', 'leads', 'bonus', 'tax', 'cogs']
    
    # --- SECTION A: FINANCIAL & VOLUME TOTALS ---
    summary.append("\n--- 💰 FINANCIAL & VOLUME TOTALS ---")
    financial_found = False
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col].dtype):
            col_lower = col.lower()
            # If it sounds like money or volume, give me the TOTAL
            if any(k in col_lower for k in sum_keywords) and "id" not in col_lower and "year" not in col_lower:
                total_val = df[col].sum()
                avg_val = df[col].mean()
                summary.append(f"🔹 {col}: Total = {total_val:,.2f} | Avg = {avg_val:,.2f}")
                financial_found = True
    
    if not financial_found:
        summary.append("(No direct financial columns identified based on naming conventions)")

    # --- SECTION B: COLUMN-BY-COLUMN DEEP DIVE ---
    summary.append("\n--- 🔍 DETAILED COLUMN ANALYSIS ---")

    for col in df.columns:
        summary.append(f"\n📌 COLUMN: '{col}'")
        dtype = df[col].dtype
        null_count = df[col].isnull().sum()
        
        # 1. Integrity Check
        if null_count > 0:
            pct = (null_count/total_rows)*100
            summary.append(f"   [Warning] Missing Values: {null_count} ({pct:.1f}%)")

        # 2. Logic by Type
        # --- CATEGORICAL (Text/Flags) ---
        if pd.api.types.is_object_dtype(dtype) or pd.api.types.is_categorical_dtype(dtype) or pd.api.types.is_bool_dtype(dtype):
            unique_count = df[col].nunique()
            summary.append(f"   Type: Categorical | Unique Values: {unique_count}")
            
            # Special handling for High Cardinality (like Dealer_ID or City)
            if unique_count > 50:
                top = df[col].value_counts().head(10) # Show Top 10 for context
                summary.append(f"   Top 10 Contributors:")
                for val, count in top.items():
                    pct = (count / total_rows) * 100
                    summary.append(f"     - {val}: {count} ({pct:.1f}%)")
                summary.append(f"     ... and {unique_count - 10} others.")
            else:
                # Show ALL values if count is low (like Fuel_Type)
                dist = df[col].value_counts()
                for val, count in dist.items():
                    pct = (count / total_rows) * 100
                    summary.append(f"     - {val}: {count} ({pct:.1f}%)")

        # --- NUMERICAL ---
        elif pd.api.types.is_numeric_dtype(dtype):
            summary.append("   Type: Numerical")
            
            # Skip ID columns for stats
            if "id" in col.lower() or "code" in col.lower():
                summary.append("   (ID Column - Statistical analysis skipped)")
                continue
                
            desc = df[col].describe()
            summary.append(f"   - Mean: {desc['mean']:.2f} | Median: {desc['50%']:.2f}")
            summary.append(f"   - Min: {desc['min']} | Max: {desc['max']}")
            
            # Show Sum ONLY if we didn't show it in Section A (avoid duplicates, or reinforce important ones)
            # Actually, showing SUM again here helps context.
            if any(k in col.lower() for k in sum_keywords):
                 summary.append(f"   - Grand Total: {df[col].sum():,.2f}")
            
            # Outlier / Spread
            summary.append(f"   - Std Dev: {desc['std']:.2f} (Variability)")

        # --- DATES ---
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            summary.append("   Type: Date/Time")
            summary.append(f"   - Range: {df[col].min()} to {df[col].max()}")
            
    return "\n".join(summary)