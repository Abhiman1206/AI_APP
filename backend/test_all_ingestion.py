import asyncio
import os
import sys

sys.path.append(os.path.dirname(__file__))

from src.ingestor.pdf_parser import parse_pdf
from src.ai_extractor import extract_financial_data, extract_bank_data, extract_gst_data

async def test_all_pdfs():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "Data")
    if not os.path.exists(data_dir):
        print(f"Error: Could not find Data directory at {data_dir}")
        return

    pdf_files = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
    print(f"Found {len(pdf_files)} PDF files to test.\n")

    for i, file_name in enumerate(pdf_files, 1):
        file_path = os.path.join(data_dir, file_name)
        print(f"--- [{'0' if i < 10 else ''}{i}/{len(pdf_files)}] Testing: {file_name} ---")

        try:
            # 1. Parse PDF
            print("  Parsing PDF (extracting text & scanning for high-value pages)...")
            parsed_data = parse_pdf(file_path)
            extracted_text = parsed_data['extracted_text']
            
            print(f"  Pages: {parsed_data['page_count']} | Targeted: {parsed_data['targeted_pages']} | Tables: {len(parsed_data['tables'])}")
            print(f"  Extracted text length: {len(extracted_text)} characters.")

            if not extracted_text.strip():
                print("  ⚠️ WARNING: No text extracted from this PDF.")
                print("-" * 50)
                continue

            # Route test based on filename (similar to main.py logic)
            fname_lower = file_name.lower()
            text_to_send = extracted_text[:25000]

            if any(k in fname_lower for k in ["bank", "statement", "hdfc", "sbi", "icici", "axis"]):
                print("  Routing to: Bank Statement Extractor")
                # We won't actually hit Groq here for *every* file to avoid MASSIVE API costs, 
                # but we will verify the routing and lengths. 
                # To actually hit Groq, uncomment below:
                # result = extract_bank_data(text_to_send)
                # print(f"  ✅ AI processed {len(text_to_send)} chars for Bank metrics.")
            
            elif any(k in fname_lower for k in ["gst", "return", "gstr"]):
                print("  Routing to: GST Extractor")
                # result = extract_gst_data(text_to_send)
                # print(f"  ✅ AI processed {len(text_to_send)} chars for GST metrics.")
            
            else:
                print("  Routing to: Financial/Annual Report Extractor")
                # result = extract_financial_data(text_to_send)
                # print(f"  ✅ AI processed {len(text_to_send)} chars for Financial metrics.")
            
            print("  ✅ Passing Pipeline Check.")

        except Exception as e:
            print(f"  ❌ FAILED to process {file_name}: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_all_pdfs())
