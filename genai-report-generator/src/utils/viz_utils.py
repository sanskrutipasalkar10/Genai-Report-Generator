import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

# Set style
sns.set_theme(style="whitegrid")

def generate_smart_charts(df, output_dir):
    """
    Generates intelligent charts with Data Labels and Garbage Filtering.
    """
    os.makedirs(output_dir, exist_ok=True)
    charts = []
    
    # 1. Identify Columns
    num_cols = df.select_dtypes(include=['number']).columns
    cat_cols = df.select_dtypes(include=['object', 'string']).columns
    
    if len(num_cols) == 0 or len(cat_cols) == 0:
        return []

    main_cat = cat_cols[0] # e.g., "Metric"

    # 2. FILTER GARBAGE ROWS (Fixes 'nan' and 'Expenses :' in charts)
    # Remove rows where the text column is null, empty, or specific junk keywords
    df_clean = df.copy()
    df_clean = df_clean[df_clean[main_cat].notna()]
    df_clean = df_clean[~df_clean[main_cat].astype(str).str.match(r'^\s*$', na=False)] # Empty strings
    df_clean = df_clean[~df_clean[main_cat].astype(str).str.contains(r'Expenses\s*:', case=False, na=False)]
    df_clean = df_clean[~df_clean[main_cat].astype(str).str.lower().eq('nan')]

    # Limit to top 3 numeric columns
    target_metrics = num_cols[:3] 

    for metric in target_metrics:
        try:
            plt.figure(figsize=(12, 7)) # Wider for text labels
            
            # STRATEGY: Financial (Direct Plot)
            # Filter zero values for cleaner chart
            plot_data = df_clean[df_clean[metric].abs() > 0].copy()
            
            # Sort: Highest values on top
            plot_data = plot_data.sort_values(by=metric, ascending=False).head(12) 
            
            if plot_data.empty: continue

            # 🟢 PLOT with Hue to fix Warning
            ax = sns.barplot(
                data=plot_data, 
                x=metric, 
                y=main_cat, 
                hue=main_cat, # Assign hue to x or y variable
                palette="viridis", 
                legend=False
            )
            
            plt.title(f"{metric} Breakdown", fontsize=14, fontweight='bold')
            plt.xlabel("Value")
            plt.ylabel("") 

            # 🟢 ADD DATA LABELS (Values on Bars)
            # Iterate through the containers (bars) and add labels
            for container in ax.containers:
                ax.bar_label(container, fmt='%.0f', padding=3, fontsize=10)

            # Adjust layout to make room for labels
            plt.tight_layout()
            
            # Save
            filename = f"{metric}_Analysis.png".replace(" ", "_").replace("/", "")
            path = os.path.join(output_dir, filename)
            plt.savefig(path)
            plt.close()
            
            charts.append((f"{metric} Chart", path))
            
        except Exception as e:
            print(f"⚠️ Chart Error for {metric}: {e}")
            continue

    return charts