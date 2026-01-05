import sys
import os

# Add the project root to python path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.rag.ingestion import ingest_file

# Create a dummy CSV for testing if you don't have one
dummy_csv = "data/raw/test_sales.csv"
os.makedirs("data/raw", exist_ok=True)

with open(dummy_csv, "w") as f:
    f.write("product,sales,month\nWidget A,100,Jan\nWidget B,200,Jan\nWidget A,150,Feb")

if __name__ == "__main__":
    # Run ingestion
    ingest_file(dummy_csv)