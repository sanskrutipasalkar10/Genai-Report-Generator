import pandas as pd
import numpy as np
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Silence Pandas FutureWarnings
pd.set_option('future.no_silent_downcasting', True)

class DataSanitizer:
    """
    Production-grade Data Cleaning Engine.
    Statistically determines headers and types without AI.
    """

    @staticmethod
    def clean_file(file_path: str) -> pd.DataFrame:
        """
        Main pipeline to load and sanitize a file from disk.
        """
        logger.info(f"🚿 [Sanitizer] Processing File: {file_path}")
        try:
            # 1. LOAD RAW DATA
            if file_path.endswith('.csv'):
                # Read without header first to detect it statistically later
                df = pd.read_csv(file_path, header=None, engine='python')
            elif file_path.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path, header=None)
            else:
                return pd.DataFrame()

            if df.empty: return df

            # Delegate to the DataFrame cleaner
            return DataSanitizer.clean_dataframe(df)

        except Exception as e:
            logger.error(f"❌ Sanitization Failed: {e}")
            return pd.DataFrame()

    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies the FULL sanitization pipeline to an in-memory DataFrame.
        """
        try:
            if df.empty: return df

            # 1. LOCATE REAL HEADER (With Protection for Existing Headers)
            df = DataSanitizer._locate_and_set_header(df)

            # 2. HANDLE MERGED HEADERS
            df = DataSanitizer._flatten_multi_headers(df)

            # 3. CLEAN & DEDUPLICATE COLUMNS
            # Must run BEFORE _fill_merged_cells to prevent errors with duplicate column names
            df = DataSanitizer._clean_column_names(df)

            # 4. HANDLE MERGED CELLS
            df = DataSanitizer._fill_merged_cells(df)

            # 5. ENFORCE DATA TYPES
            df = DataSanitizer._enforce_types(df)

            # 6. FINAL CLEANUP
            df = df.dropna(how='all').reset_index(drop=True)
            
            logger.info(f"✅ [Sanitizer] Success. Columns: {list(df.columns)}")
            return df
        except Exception as e:
            logger.error(f"❌ DataFrame Cleaning Error: {e}")
            return df

    @staticmethod
    def _locate_and_set_header(df: pd.DataFrame) -> pd.DataFrame:
        """
        Smart Header Detection.
        If existing headers look valid (strings), KEEP THEM.
        Only scans for new headers if current ones look like garbage (0, 1, 2 or Unnamed).
        """
        # 1. Analyze Current Header Quality
        current_cols = df.columns
        # Count how many columns are meaningful text (not numbers, not 'unnamed')
        current_header_score = sum(
            1 for x in current_cols 
            if isinstance(x, str) and len(x.strip()) > 0 and "unnamed" not in x.lower() and not str(x).isdigit()
        )
        
        # 🟢 PROTECTION: If >50% of columns are already valid strings, assume header is correct.
        # This protects data coming from AI Parser (PDFs) which already have headers.
        # Excel files loaded with header=None will fail this check (cols are 0,1,2), so they will proceed to scan (Correct behavior).
        if len(current_cols) > 0 and (current_header_score / len(current_cols)) > 0.5:
            # logger.info("   🛡️  Existing header looks valid. Skipping auto-detection.")
            return df

        # 2. If Header is bad (0, 1, 2...), Scan for a better one
        best_idx = -1
        max_text_score = -1
        scan_rows = min(20, len(df))

        for i in range(scan_rows):
            row = df.iloc[i]
            # Score = Number of valid strings that aren't 'nan'
            text_score = sum(1 for x in row if isinstance(x, str) and len(x.strip()) > 0 and "nan" not in x.lower())
            
            # Prefer higher rows if scores are equal (find the top-most header)
            if text_score > max_text_score:
                max_text_score = text_score
                best_idx = i

        # Only promote if we found a row with significantly better text content
        if max_text_score >= 2:
            logger.info(f"   🔧 Dropping {best_idx} rows of metadata. Header found at Row {best_idx}.")
            df.columns = df.iloc[best_idx]
            df = df[best_idx + 1:].reset_index(drop=True)
        else:
            logger.warning("   ⚠️ No clear header row found. Using default index.")
            
        return df

    @staticmethod
    def _flatten_multi_headers(df: pd.DataFrame) -> pd.DataFrame:
        if len(df) < 2: return df
        row0 = df.columns.astype(str)
        row1 = df.iloc[0].astype(str)
        
        unnamed_count = sum("unnamed" in c.lower() for c in row0)
        if unnamed_count > 0 and (unnamed_count / len(df.columns) > 0.3):
            logger.info("   🔧 Multi-row header detected. Flattening...")
            new_cols = []
            for c0, c1 in zip(row0, row1):
                c0 = c0.strip() if "unnamed" not in c0.lower() and "nan" not in c0.lower() else ""
                c1 = c1.strip() if "nan" not in c1.lower() else ""
                
                if c0 and c1: new_cols.append(f"{c0}_{c1}")
                elif c1: new_cols.append(c1)
                else: new_cols.append(c0)
            
            df.columns = new_cols
            df = df[1:].reset_index(drop=True)
        return df

    @staticmethod
    def _fill_merged_cells(df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            # Skip if column is somehow a DataFrame (duplicate name issue wrapper)
            if isinstance(df[col], pd.DataFrame): continue
            
            if df[col].dtype == object:
                if df[col].isna().mean() > 0.1:
                    df[col] = df[col].ffill().infer_objects(copy=False)
        return df

    @staticmethod
    def _clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        new_cols = []
        for i, col in enumerate(df.columns):
            c_str = str(col).strip()
            if c_str.lower() == 'nan' or c_str == '':
                c_str = "Metric" if i == 0 else f"Column_{i}"
            
            c_str = re.sub(r'\s+', '_', c_str)
            c_str = re.sub(r'[^\w]', '', c_str)
            new_cols.append(c_str)
            
        df.columns = new_cols
        
        # Deduplication
        if not df.columns.is_unique:
            logger.info("   🔧 Duplicate headers detected. Renaming...")
            cols = pd.Series(df.columns)
            for dup in cols[cols.duplicated()].unique(): 
                mask = cols == dup
                count = mask.sum()
                new_names = [dup if i == 0 else f"{dup}_{i}" for i in range(count)]
                cols.loc[mask] = new_names
            df.columns = cols
        return df

    @staticmethod
    def _enforce_types(df: pd.DataFrame) -> pd.DataFrame:
        def clean_currency(val):
            if pd.isna(val): return None
            s_val = str(val)
            nums = re.findall(r'-?\d+\.?\d*', s_val.replace(',', ''))
            return float(nums[0]) if nums else None

        for col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            if numeric_col.notna().mean() > 0.5:
                if df[col].dtype == object:
                    df[col] = df[col].apply(clean_currency)
                else:
                    df[col] = numeric_col
            else:
                df[col] = df[col].astype(str).str.strip()
        return df