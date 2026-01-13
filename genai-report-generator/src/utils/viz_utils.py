import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
import re

# Set style
sns.set_theme(style="whitegrid")

def generate_smart_charts(df, output_dir):
    """
    Generates intelligent charts covering MULTIPLE dimensions.
    Iterates through top categorical columns to ensure Primary Keys are plotted.
    """
    os.makedirs(output_dir, exist_ok=True)
    charts = []
    
    # 1. Identify Columns
    num_cols = df.select_dtypes(include=['number']).columns
    cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns
    
    if len(num_cols) == 0 or len(cat_cols) == 0:
        return []

    # 🟢 UPGRADE: Pick Top 2 Dimensions (e.g., Product_ID AND Station)
    # This ensures we get charts for the Primary Key M001.. AND the Categories
    target_cats = cat_cols[:2] 
    
    # Limit to Top 2 Metrics to avoid chart spam
    target_metrics = num_cols[:2]

    for cat in target_cats:
        for metric in target_metrics:
            try:
                # Setup Plot
                plt.figure(figsize=(12, 7))
                
                # 2. FILTER GARBAGE ROWS
                df_clean = df.copy()
                df_clean = df_clean[df_clean[cat].notna()]
                df_clean = df_clean[~df_clean[cat].astype(str).str.match(r'^\s*$', na=False)]
                df_clean = df_clean[~df_clean[cat].astype(str).str.contains(r'Expenses|Total', case=False, na=False)]
                df_clean = df_clean[~df_clean[cat].astype(str).str.lower().eq('nan')]

                # 3. FORCE NUMERIC
                df_clean[metric] = pd.to_numeric(df_clean[metric], errors='coerce')
                
                # 4. AGGREGATE DATA
                # If there are many rows (Transactional), we must GroupBy first
                # This fixes the issue where multiple M001 rows weren't being summed up
                if len(df_clean) > 20:
                    plot_data = df_clean.groupby(cat)[metric].sum().reset_index()
                else:
                    plot_data = df_clean

                # Filter zero values
                plot_data = plot_data[plot_data[metric].abs() > 0]
                
                # 5. SORT: Highest values on top
                plot_data = plot_data.sort_values(by=metric, ascending=False).head(12)
                
                if plot_data.empty: continue

                # 6. PLOT
                ax = sns.barplot(
                    data=plot_data, 
                    x=metric, 
                    y=cat, 
                    hue=cat, 
                    palette="viridis", 
                    legend=False
                )
                
                plt.title(f"{metric} by {cat}", fontsize=14, fontweight='bold')
                plt.xlabel(metric)
                plt.ylabel("") 

                # Add Data Labels
                for container in ax.containers:
                    ax.bar_label(container, fmt='%.0f', padding=3, fontsize=10)

                plt.tight_layout()
                
                # Save with unique name combining Metric + Dimension
                clean_cat_name = str(cat).replace(" ", "_").replace("/", "")
                clean_metric_name = str(metric).replace(" ", "_").replace("/", "")
                filename = f"{clean_metric_name}_by_{clean_cat_name}.png"
                
                path = os.path.join(output_dir, filename)
                plt.savefig(path)
                plt.close()
                
                charts.append((f"{clean_metric_name} by {clean_cat_name}", path))
                
            except Exception as e:
                print(f"⚠️ Chart Error for {metric} vs {cat}: {e}")
                continue

    return charts