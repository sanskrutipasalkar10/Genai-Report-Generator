import os
import pandas as pd
from pypdf import PdfReader
from app.config import RAW_DATA_PATH, PROCESSED_PATH

def extract_text(file_path):
    ext = file_path.split(".")[-1].lower()

    if ext == "pdf":
        reader = PdfReader(file_path)
        return "\n".join(
            page.extract_text() or "" for page in reader.pages
        )

    elif ext == "csv":
        df = pd.read_csv(file_path)
        return df.to_string(index=False)

    elif ext == "xlsx":
        xls = pd.ExcelFile(file_path)
        all_sheets = []
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            # Optional: add sheet name for reference
            df.insert(0, "sheet_name", sheet_name)
            all_sheets.append(df)
        combined_df = pd.concat(all_sheets, ignore_index=True)
        return combined_df.to_string(index=False)

    elif ext == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    else:
        raise ValueError(f"Unsupported file type: {ext}")

def ingest_files():
    os.makedirs(PROCESSED_PATH, exist_ok=True)

    for file in os.listdir(RAW_DATA_PATH):
        file_path = os.path.join(RAW_DATA_PATH, file)

        if not os.path.isfile(file_path):
            continue

        try:
            text = extract_text(file_path)
        except Exception as e:
            print(f"⚠️ Failed to ingest {file}: {e}")
            continue

        # Save as TXT
        output_file = file + ".txt"
        output_path = os.path.join(PROCESSED_PATH, output_file)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"✅ Ingested: {file}")

if __name__ == "__main__":
    ingest_files()
