---
name: pdf-official
description: "PDF processing operations using Python libraries (pdfplumber, pypdf, reportlab). Covers text/table extraction, merging, splitting, OCR, and creation."
risk: unknown
source: community
date_added: "2026-02-27"
---

# PDF Processing Guide

## Overview
Essential PDF processing operations using Python libraries. Uses pdfplumber as primary extractor and pypdf as fallback — matching project conventions.

## Python Libraries

### pypdf - Basic Operations

```python
from pypdf import PdfReader, PdfWriter

# Read a PDF
reader = PdfReader("document.pdf")
text = ""
for page in reader.pages:
    text += page.extract_text()

# Merge PDFs
writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)
with open("merged.pdf", "wb") as output:
    writer.write(output)

# Split PDF
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

### pdfplumber - Text and Table Extraction (PRIMARY)

```python
import pdfplumber

# Extract text with layout
with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)

# Extract tables → DataFrame
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)

if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)
    combined_df.to_excel("extracted_tables.xlsx", index=False)
```

### Fallback pattern (project convention)
```python
try:
    with pdfplumber.open(path) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
except Exception:
    reader = PdfReader(path)
    text = "\n".join(p.extract_text() or "" for p in reader.pages)
```

## OCR for Scanned PDFs
```python
# pip install pytesseract pdf2image
import pytesseract
from pdf2image import convert_from_path

images = convert_from_path('scanned.pdf')
text = ""
for i, image in enumerate(images):
    text += f"Page {i+1}:\n"
    text += pytesseract.image_to_string(image)
    text += "\n\n"
```

## Quick Reference

| Task | Best Tool |
|------|-----------|
| Extract text | pdfplumber (primary), pypdf (fallback) |
| Extract tables | pdfplumber → pd.DataFrame |
| Merge PDFs | pypdf PdfWriter |
| Split PDFs | pypdf, one page per file |
| OCR scanned | pytesseract + pdf2image |
| Create PDFs | reportlab |
