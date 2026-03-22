import asyncio
import os
import sys

# Add backend to path so imports work
sys.path.append(os.path.dirname(__file__))

from src.ingestor.pdf_parser import parse_pdf
from src.ai_extractor import extract_financial_data

async def test_extraction():
    # Pick a known large PDF from the Data folder
    data_dir = os.path.join(os.path.dirname(__file__), "..", "Data")
    pdf_path = os.path.join(data_dir, "Vivriti’s Climate Report 2024-25.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"Error: Could not find test PDF at {pdf_path}")
        print("Available files:")
        for f in os.listdir(data_dir):
            if f.endswith(".pdf"):
                print(" -", f)
        return

    print(f"1. Parsing {os.path.basename(pdf_path)}...")
    parsed_data = parse_pdf(pdf_path)
    
    print(f"Total Pages: {parsed_data['page_count']}")
    print(f"Pages Targeted for Deep Scan: {parsed_data['targeted_pages']}")
    print(f"Tables Extracted: {len(parsed_data['tables'])}")
    print(f"Extracted Text Length: {len(parsed_data['extracted_text'])} characters")
    
    print("\n2. Simulating AI Financial Extraction...")
    fin_text = parsed_data['extracted_text']
    
    # We won't actually hit the Groq API to save credits during this rapid test, 
    # but we will mimic the boundary size we'd pass.
    text_to_send = fin_text[:25000]
    print(f"Text length to send to Groq: {len(text_to_send)} characters")
    
    print("\nPipeline Test Complete.")
    print("-" * 50)
    print("Sample from the beginning of the text to send:")
    print(text_to_send[:500])
    print("-" * 50)
    print("Sample from the END of the text to send (should contain OCR blocks):")
    print(text_to_send[-1000:])

if __name__ == "__main__":
    asyncio.run(test_extraction())
