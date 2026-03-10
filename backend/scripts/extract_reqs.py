import pdfplumber
import os

pdf_path = r"c:\Users\Asus\Desktop\IIT  Hackathon\6995b96058f14_Hackathon_Problem_Statement__The__Intelli-Credit__Challenge (3).pdf"
output_path = r"c:\Users\Asus\Desktop\IIT  Hackathon\requirements_extracted.md"

try:
    with pdfplumber.open(pdf_path) as pdf:
        text = "# Hackathon Requirements\n\n"
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"## Page {i+1}\n\n{page_text}\n\n"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
    print(f"Successfully extracted to {output_path}")
except Exception as e:
    print(f"Error: {e}")
