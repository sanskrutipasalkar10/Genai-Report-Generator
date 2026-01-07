import pandas as pd
import numpy as np
import os
import sys  # <--- THIS WAS MISSING
from datetime import datetime, timedelta

# --- SETUP ---
# Ensure directories exist
# We need to calculate base_path relative to this script
current_dir = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.dirname(current_dir) # Go up one level to project root
output_dir = os.path.join(base_path, "data", "raw")
os.makedirs(output_dir, exist_ok=True)

file_path = os.path.join(output_dir, "Complex_Tata_Sales_Test.xlsx")

print(f"⚙️ Generating complex test data at: {file_path}")

# --- 1. GENERATE RAW DATA (40 rows, 15 columns) ---
np.random.seed(42)
rows = 40

# Create varied data types
data = {
    "Transaction_ID": [f"TXN-{1000+i}" for i in range(rows)],
    "Date": [datetime(2024, 1, 1) + timedelta(days=i*2) for i in range(rows)],
    "Zone": np.random.choice(["North", "South", "East", "West"], rows),
    "State": np.random.choice(["Maharashtra", "Karnataka", "Delhi", "Tamil Nadu", "Gujarat"], rows),
    "Dealer_Name": [f"Tata Dealer {np.random.randint(1, 50)}" for _ in range(rows)], # High cardinality
    "Model": np.random.choice(["Nexon", "Punch", "Harrier", "Safari"], rows),
    "Fuel_Type": np.random.choice(["Petrol", "Diesel", "EV"], rows),
    
    # Financials (Floats)
    "Ex_Showroom_Price": np.random.randint(600000, 2500000, rows),
    "Discount_Amount": np.random.randint(0, 50000, rows),
    
    # Metrics (Integers/Floats)
    "NPS_Score": np.random.randint(1, 10, rows), # Scale 1-10
    "Delivery_Days": np.random.randint(1, 45, rows),
    
    # Boolean / Flags
    "Stockout_Flag": np.random.choice([True, False], rows, p=[0.1, 0.9]),
    
    # Empty column (to test garbage removal)
    "Unnamed: 12": [np.nan] * rows 
}

df = pd.DataFrame(data)

# --- 2. INJECT CHAOS (Missing Values & Outliers) ---
# Add outliers to Price to test stats
df.loc[0, "Ex_Showroom_Price"] = 15000000 # Massive outlier
df.loc[1, "Ex_Showroom_Price"] = 100      # Impossible low value

# Add missing values (NaN)
df.loc[5:8, "Zone"] = np.nan
df.loc[10:15, "NPS_Score"] = np.nan
df.loc[20, "Model"] = np.nan

# Calculated Columns (to test Summation logic)
df["Net_Revenue"] = df["Ex_Showroom_Price"] - df["Discount_Amount"]

# --- 3. WRITE TO EXCEL WITH "BAD" STRUCTURE ---
try:
    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Sales_Data_FY24")
        writer.sheets["Sales_Data_FY24"] = worksheet
        
        # A. Write Metadata / Junk at the top
        bold_fmt = workbook.add_format({'bold': True, 'font_size': 14})
        worksheet.write("A1", "TATA MOTORS SALES REPORT - INTERNAL ONLY", bold_fmt)
        worksheet.write("A2", "Generated on: " + datetime.now().strftime("%Y-%m-%d"))
        worksheet.write("A3", "Confidential Document")
        # Row 4 is empty
        
        # B. Write the Header manually at Row 6 (Index 5)
        # We simulate "Merged Headers" by writing categories above columns
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        
        # Merged Cells (Visual only, but data is below)
        worksheet.merge_range("A5:B5", "Metadata", header_fmt)
        worksheet.merge_range("H5:J5", "Financials", header_fmt)
        
        # C. Write the actual DataFrame starting at Row 7 (Index 6)
        df.to_excel(writer, sheet_name="Sales_Data_FY24", startrow=6, index=False)
        
    print("✅ Complex Excel File Created Successfully!")
    
except Exception as e:
    print(f"❌ Failed to create excel: {e}")

# --- 4. IMMEDIATE VERIFICATION ---
print("\n🔎 VERIFYING WITH SMART LOADER...")
try:
    # Append project root to path so we can import src
    sys.path.append(base_path)
    
    from src.utils.data_utils import smart_load_table, summarize_dataframe
    
    # 1. Load
    loaded_df = smart_load_table(file_path)
    print(f"✅ Loaded DataFrame Shape: {loaded_df.shape}")
    
    # 2. Check if it skipped the junk top rows
    first_col = loaded_df.columns[0]
    print(f"   - First Column Detected: '{first_col}'")
    
    if "Transaction_ID" in str(first_col) or "Metadata" in str(first_col):
        print("   ✅ Header detection working (Found valid column name)")
    else:
        print(f"   ⚠️ Warning: Header might be wrong. Saw '{first_col}'")

    # 3. Generate Summary
    summary = summarize_dataframe(loaded_df)
    print("\n📊 GENERATED SUMMARY PREVIEW (First 15 lines):")
    print("-" * 40)
    print("\n".join(summary.splitlines()[:15]))
    print("-" * 40)
    
    # 4. Check for Specific Features
    if "Total =" in summary:
        print("✅ Financial Totals Detected!")
    if "Missing Values" in summary:
        print("✅ Missing Values Detected!")
    if "Outliers" in summary:
        print("✅ Outlier Detection Working!")
        
except ImportError:
    print("⚠️ Could not import src.utils.data_utils. Please ensure the project structure is correct.")
except Exception as e:
    print(f"❌ Verification Failed: {e}")