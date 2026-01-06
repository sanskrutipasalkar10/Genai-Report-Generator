import pandas as pd

def summarize_dataframe(df, max_categories=10):
    """
    Takes a large DataFrame and returns a text summary optimized for LLMs.
    """
    summary = []
    
    # 1. Overall Stats
    total_rows = len(df)
    summary.append("--- DATASET STATISTICAL SUMMARY ---")
    summary.append(f"Total Records: {total_rows}")
    summary.append(f"Columns: {', '.join(df.columns)}")
    summary.append("\n--- COLUMN ANALYSIS ---")

    # 2. Iterate through columns
    for col in df.columns:
        summary.append(f"\nCOLUMN: '{col}'")
        dtype = df[col].dtype
        
        # A. Categorical / Text
        if pd.api.types.is_object_dtype(dtype) or pd.api.types.is_categorical_dtype(dtype):
            unique_count = df[col].nunique()
            summary.append(f"Type: Categorical | Unique Values: {unique_count}")
            
            if unique_count > 50 and unique_count > total_rows * 0.5:
                 summary.append("Note: High cardinality (likely IDs/Names). Skipped detailed breakdown.")
            else:
                top_values = df[col].value_counts().head(max_categories)
                summary.append(f"Top {max_categories} Values:")
                for val, count in top_values.items():
                    pct = (count / total_rows) * 100
                    summary.append(f"   - {val}: {count} ({pct:.1f}%)")

        # B. Numerical
        elif pd.api.types.is_numeric_dtype(dtype):
            summary.append("Type: Numerical")
            desc = df[col].describe()
            summary.append(f"   - Mean: {desc['mean']:.2f} | Median: {desc['50%']} | Max: {desc['max']}")
            
        # C. Dates
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            summary.append(f"Type: Date | Range: {df[col].min()} to {df[col].max()}")
            
    return "\n".join(summary)