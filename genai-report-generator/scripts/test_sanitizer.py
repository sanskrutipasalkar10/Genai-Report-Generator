import sys
import os
# Add 'src' to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.data_sanitizer import DataSanitizer

# Put your messy file path here
test_file = "data/raw/Q4-FY22-seg.xlsx"

print(f"Testing Sanitizer on: {test_file}")
df = DataSanitizer.clean_file(test_file)

print("\n--- RESULT HEAD ---")
print(df.head())
print("\n--- COLUMN TYPES ---")
print(df.dtypes)