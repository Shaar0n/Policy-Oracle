from pathlib import Path
import fitz  # PyMuPDF
from docx import Document


def parse_pdf(path: Path) -> list[dict]:
    doc = fitz.open(str(path))
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text()
        if text.strip():
            pages.append({"text": text, "page": i, "file": path.name})
    doc.close()
    return pages


def parse_docx(path: Path) -> list[dict]:
    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    # Group paragraphs into pseudo-pages of 50 paragraphs each
    page_size = 50
    pages = []
    for i in range(0, max(len(paragraphs), 1), page_size):
        text = "\n".join(paragraphs[i : i + page_size])
        if text.strip():
            pages.append({"text": text, "page": i // page_size + 1, "file": path.name})
    return pages


def parse_txt(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    # Split into pseudo-pages of ~3000 chars
    page_size = 3000
    pages = []
    for i in range(0, max(len(text), 1), page_size):
        chunk = text[i : i + page_size]
        if chunk.strip():
            pages.append({"text": chunk, "page": i // page_size + 1, "file": path.name})
    return pages


_PARSERS = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".doc": parse_docx,
    ".txt": parse_txt,
    ".md": parse_txt,
}

SUPPORTED_EXTENSIONS = set(_PARSERS.keys())


def parse_file(path: Path) -> list[dict]:
    parser = _PARSERS.get(path.suffix.lower())
    if parser is None:
        return []
    try:
        return parser(path)
    except Exception as e:
        print(f"    [warn] Could not parse {path.name}: {e}")
        return []
