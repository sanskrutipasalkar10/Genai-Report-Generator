import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for professional reports
sns.set_theme(style="whitegrid")

def generate_smart_charts(df, output_dir):
    """
    Analyzes the DataFrame and generates relevant charts automatically.
    Returns a list of generated image paths to inject into the report.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_charts = []
    
    # Identify Column Types
    num_cols = df.select_dtypes(include=['number']).columns
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    date_cols = df.select_dtypes(include=['datetime']).columns
    
    # 1. TIME SERIES TRENDS (If Date column exists)
    if len(date_cols) > 0 and len(num_cols) > 0:
        date_col = date_cols[0] # Pick primary date column
        # Aggregate by month/day to avoid noise
        df_sorted = df.sort_values(by=date_col)
        
        for num_col in num_cols[:2]: # Limit to top 2 numeric metrics (e.g., Sales, Revenue)
            if "id" in num_col.lower(): continue # Skip IDs
            
            plt.figure(figsize=(10, 6))
            sns.lineplot(data=df_sorted, x=date_col, y=num_col, marker='o', linewidth=2.5)
            plt.title(f"Trend Analysis: {num_col} over Time", fontsize=14)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            filename = f"trend_{num_col}.png"
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath)
            plt.close()
            
            generated_charts.append((f"Trend of {num_col}", filepath))

    # 2. CATEGORICAL DISTRIBUTIONS (Bar Charts)
    for cat_col in cat_cols:
        # Only plot if cardinality is reasonable (e.g., < 20 categories)
        unique_count = df[cat_col].nunique()
        if 2 <= unique_count <= 20:
            plt.figure(figsize=(10, 6))
            # Get top 10 values
            top_vals = df[cat_col].value_counts().head(10)
            sns.barplot(x=top_vals.values, y=top_vals.index, palette="viridis")
            plt.title(f"Distribution by {cat_col}", fontsize=14)
            plt.xlabel("Count")
            plt.tight_layout()
            
            filename = f"dist_{cat_col}.png"
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath)
            plt.close()
            
            generated_charts.append((f"Distribution of {cat_col}", filepath))
            
            if len(generated_charts) > 5: break # Cap at 5 charts max

    return generated_charts