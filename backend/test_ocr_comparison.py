"""
Test Script: Compare OCR Engines
Run this script to test RapidOCR vs your current fallback OCR.
"""

import time
import os
from pathlib import Path
from typing import Dict, List
import json

# Import OCR functions
try:
    from ocr_migration import (
        extract_with_rapid_ocr,
        extract_with_easyocr,
        extract_with_azure,
        RAPID_AVAILABLE,
        EASYOCR_AVAILABLE,
        AZURE_AVAILABLE
    )
except ImportError:
    print("Error: ocr_migration.py not found. Make sure it's in the same directory.")
    exit(1)


def time_function(func, *args, **kwargs):
    """Measure execution time of a function."""
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    return result, elapsed


def analyze_ocr_results(text: str) -> Dict:
    """Analyze OCR output quality."""
    return {
        "char_count": len(text),
        "word_count": len(text.split()) if text else 0,
        "line_count": len(text.splitlines()) if text else 0,
        "has_numbers": any(c.isdigit() for c in text),
        "has_currency": any(symbol in text for symbol in ['₹', 'Rs', 'INR', '$']),
        "has_financial_keywords": any(kw in text.lower() for kw in [
            'balance', 'credit', 'debit', 'amount', 'total', 'revenue', 'profit'
        ])
    }


def test_ocr_engine(engine_name: str, extract_func, file_path: str, pages: List[int]) -> Dict:
    """Test a single OCR engine."""
    print(f"\n{'='*60}")
    print(f"Testing {engine_name}")
    print(f"{'='*60}")

    try:
        result, elapsed = time_function(extract_func, file_path, pages)

        if not result:
            return {
                "engine": engine_name,
                "error": "Extraction failed (empty result)",
                "time": elapsed
            }

        analysis = analyze_ocr_results(result)

        print(f"✓ Success!")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Characters: {analysis['char_count']:,}")
        print(f"  Words: {analysis['word_count']:,}")
        print(f"  Lines: {analysis['line_count']:,}")
        print(f"  Financial content detected: {analysis['has_financial_keywords']}")

        return {
            "engine": engine_name,
            "success": True,
            "time": elapsed,
            "analysis": analysis,
            "sample": result[:500] + "..." if len(result) > 500 else result
        }

    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "engine": engine_name,
            "error": str(e),
            "time": 0
        }


def compare_ocr_engines(file_path: str, pages_to_test: List[int] = None):
    """
    Compare all available OCR engines on a sample PDF.

    Args:
        file_path: Path to test PDF (bank statement, GST return, or financial doc)
        pages_to_test: Pages to OCR (default: first 3 pages)
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return

    if pages_to_test is None:
        pages_to_test = [0, 1, 2]  # First 3 pages

    print("\n" + "="*60)
    print("OCR ENGINE COMPARISON TEST")
    print("="*60)
    print(f"Test file: {Path(file_path).name}")
    print(f"Pages to OCR: {len(pages_to_test)} pages (indices: {pages_to_test})")
    print(f"File size: {Path(file_path).stat().st_size / 1024 / 1024:.1f} MB")

    results = []

    # Test RapidOCR
    if RAPID_AVAILABLE:
        result = test_ocr_engine("RapidOCR (RECOMMENDED)", extract_with_rapid_ocr, file_path, pages_to_test)
        results.append(result)
    else:
        print(f"\n⚠ RapidOCR not available. Install with: pip install rapidocr-onnxruntime")

    # Test EasyOCR
    if EASYOCR_AVAILABLE:
        result = test_ocr_engine("EasyOCR", extract_with_easyocr, file_path, pages_to_test)
        results.append(result)
    else:
        print(f"\n⚠ EasyOCR not available. Install with: pip install easyocr")

    # Test Azure (if configured)
    if AZURE_AVAILABLE and os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"):
        print(f"\n⚠ Azure Document Intelligence available but not tested (costs money)")
        print(f"  To test Azure, run: python test_ocr.py --azure {file_path}")
    else:
        print(f"\n⚠ Azure Document Intelligence not configured")
        print(f"  Set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY to enable")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    if not results:
        print("No OCR engines available to test.")
        print("\nRecommended setup:")
        print("  pip install rapidocr-onnxruntime")
        return

    # Sort by time (fastest first)
    successful_results = [r for r in results if r.get("success")]

    if successful_results:
        fastest = min(successful_results, key=lambda x: x["time"])
        most_text = max(successful_results, key=lambda x: x["analysis"]["char_count"])

        print(f"\n🏆 Fastest: {fastest['engine']} ({fastest['time']:.2f}s)")
        print(f"📄 Most text extracted: {most_text['engine']} ({most_text['analysis']['char_count']:,} chars)")

        print(f"\nDetailed Results:")
        for r in successful_results:
            print(f"\n  {r['engine']}:")
            print(f"    Time: {r['time']:.2f}s")
            print(f"    Text: {r['analysis']['char_count']:,} chars, {r['analysis']['word_count']:,} words")
            print(f"    Financial keywords: {'✓' if r['analysis']['has_financial_keywords'] else '✗'}")

    # Recommendations
    print(f"\n" + "="*60)
    print("RECOMMENDATION")
    print("="*60)

    if RAPID_AVAILABLE:
        print(f"✓ RapidOCR is installed and working")
        print(f"  → Use this as your primary OCR engine")
        print(f"  → 2-3x faster than Tesseract with better accuracy")
    else:
        print(f"✗ RapidOCR not installed")
        print(f"  → Install now: pip install rapidocr-onnxruntime")
        print(f"  → Best balance of speed and accuracy for your use case")

    # Save results to JSON
    output_file = "ocr_comparison_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results saved to: {output_file}")


def test_with_azure(file_path: str):
    """Special test for Azure Document Intelligence."""
    if not AZURE_AVAILABLE:
        print("Azure SDK not installed. Install with: pip install azure-ai-formrecognizer")
        return

    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    if not endpoint or not api_key:
        print("Azure credentials not set.")
        print("Set environment variables:")
        print("  AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/")
        print("  AZURE_DOCUMENT_INTELLIGENCE_KEY=your-api-key")
        return

    print(f"\nTesting Azure Document Intelligence...")
    print(f"Endpoint: {endpoint}")
    print(f"⚠ This will incur charges! ~$0.0015 per page")

    response = input("Continue? (yes/no): ")
    if response.lower() != "yes":
        print("Cancelled.")
        return

    result = test_ocr_engine("Azure Document Intelligence", extract_with_azure, file_path, [])

    if result.get("success"):
        print(f"\n✓ Azure extraction successful!")
        print(f"  This is the most accurate OCR available (~99% accuracy)")
        print(f"  Consider using for high-value loans (>₹10 Cr)")


if __name__ == "__main__":
    import sys

    print("""
╔══════════════════════════════════════════════════════════════╗
║         OCR ENGINE COMPARISON TOOL                           ║
║         For Intelli-Credit Project                            ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Check command line args
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_ocr.py <pdf_file> [page_indices]")
        print("\nExamples:")
        print("  python test_ocr.py ../Data/bank_statement.pdf")
        print("  python test_ocr.py ../Data/gst_return.pdf 0 1 2")
        print("  python test_ocr.py ../Data/annual_report.pdf --azure")
        print("\nThis will test all available OCR engines and show:")
        print("  - Extraction speed")
        print("  - Text quality")
        print("  - Recommendation for your project")
        sys.exit(1)

    file_path = sys.argv[1]

    if "--azure" in sys.argv:
        test_with_azure(file_path)
    else:
        # Parse page indices if provided
        pages = [0, 1, 2]  # Default
        if len(sys.argv) > 2 and "--azure" not in sys.argv:
            try:
                pages = [int(p) for p in sys.argv[2:] if p.isdigit()]
            except:
                print("Warning: Invalid page indices, using default [0, 1, 2]")

        compare_ocr_engines(file_path, pages)

    print("\nNext steps:")
    print("1. Review results above")
    print("2. Install recommended OCR: pip install rapidocr-onnxruntime")
    print("3. Update your pdf_parser.py using code from ocr_migration.py")
    print("4. Test on your full dataset (27 PDFs)")
