"""PDF Parser module — extracts text and tables from uploaded PDF files using pdfplumber."""

import pdfplumber


def parse_pdf(file_path: str) -> dict:
    """Parse a PDF file and return extracted text, tables, and metadata.

    Uses pdfplumber for real text and table extraction.
    """
    all_text = []
    all_tables = []

    with pdfplumber.open(file_path) as pdf:
        page_count = len(pdf.pages)

        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)

            tables = page.extract_tables()
            for table in tables:
                if table and len(table) > 1:
                    headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(table[0])]
                    rows = []
                    for row in table[1:]:
                        row_dict = {}
                        for i, cell in enumerate(row):
                            key = headers[i] if i < len(headers) else f"col_{i}"
                            row_dict[key] = str(cell).strip() if cell else ""
                        rows.append(row_dict)
                    all_tables.append({"headers": headers, "rows": rows})

    combined_text = "\n\n".join(all_text)

    return {
        "filename": file_path,
        "page_count": page_count,
        "extracted_text": combined_text,
        "tables": all_tables,
    }
