from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_broken_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "CONFIDENTIAL STOCK REPORT - 2024")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, "The following data is extracted from the legacy ERP system.")
    c.drawString(50, height - 100, "Note: Formatting may be inconsistent.")

    # --- SIMULATE A BROKEN TABLE (Raw Text, No Grid Lines) ---
    # This mimics the "CSV text inside PDF" issue
    
    text_start_y = height - 150
    line_height = 20

    # 1. Merged Header (The problem we want to solve)
    # "Stock_On_Hand" and "In_Transit" are merged with just a space
    c.setFont("Courier-Bold", 10)
    header = 'SKU_ID     Stock_On_Hand In_Transit    Lead_Time'
    c.drawString(50, text_start_y, header)

    # 2. Data Rows (Whitespace separated, no commas)
    data = [
        "SK0010     10000         5000          7",
        "SK0011     12000         2000          3",
        "SK0012     8500          0             5",
        "SK0013     10000         5000          4", # Standard row
        "SK0099     500           9999          2",  # Another standard row
    ]

    c.setFont("Courier", 10)
    y = text_start_y - line_height
    for row in data:
        c.drawString(50, y, row)
        y -= line_height

    # 3. Add a "Trap" for Hallucination / Numeric Validation
    # The AI might try to convert "Two Thousand" to 2000. 
    # Your validator should allow it IF the AI returns "Two Thousand", 
    # but be careful if it returns 2000 (digit) when source is text.
    c.drawString(50, y, "SK0050     3000          Two_Thousand  1") 

    c.save()
    print(f"✅ Generated test file: {filename}")

if __name__ == "__main__":
    create_broken_pdf("data/raw/test_broken_inventory.pdf")