import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def create_pdf_with_table():
    # Ensure directory exists
    output_dir = "data/raw"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, "sample_with_table.pdf")

    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Monthly Sales Report (Confidential)", styles['Heading1']))
    elements.append(Paragraph("Below is the financial data for Q1 2024.", styles['Normal']))
    elements.append(Paragraph(" ", styles['Normal'])) # Spacer

    # Define Table Data (Header + Rows)
    data = [
        ['Month', 'Department', 'Revenue', 'Cost'],
        ['January', 'Electronics', '50000', '30000'],
        ['January', 'Clothing', '20000', '10000'],
        ['February', 'Electronics', '55000', '32000'],
        ['February', 'Clothing', '22000', '11000'],
        ['March', 'Electronics', '60000', '35000'],
        ['March', 'Clothing', '25000', '12000'],
    ]

    # Create Table
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(t)
    doc.build(elements)
    print(f"✅ Created test PDF at: {filename}")

if __name__ == "__main__":
    create_pdf_with_table()