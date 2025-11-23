# data_parser.py

"""
Utilities to turn user input (text or uploaded files)
into a single plain-text string for Gemini.

We keep imports light and do OPTIONAL imports inside functions
so that missing libraries don't crash the whole app on import.
"""

from typing import Optional
from io import BytesIO


def parse_input_data(
    text_input: Optional[str] = "",
    uploaded_file: Optional[BytesIO] = None,
) -> str:
    """
    Return a plain-text version of the user's input.

    Priority:
    1. If text_input is non-empty -> use that.
    2. Else, if uploaded_file is provided -> extract based on extension.
    """

    # 1. If user typed/pasted text, just use it.
    if text_input and text_input.strip():
        return text_input.strip()

    # 2. If a file is uploaded, handle based on extension.
    if uploaded_file is None:
        return ""

    filename = (uploaded_file.name or "").lower()

    if filename.endswith(".txt"):
        return _read_txt(uploaded_file)

    if filename.endswith(".pdf"):
        return _read_pdf(uploaded_file)

    if filename.endswith((".docx", ".doc")):
        return _read_docx(uploaded_file)

    if filename.endswith(".csv"):
        return _read_csv(uploaded_file)

    if filename.endswith((".xlsx", ".xlsm", ".xls")):
        return _read_xlsx(uploaded_file)

    # Fallback: just try to decode as text
    try:
        return uploaded_file.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


# -------------------------
# Individual format readers
# -------------------------


def _read_txt(file_obj: BytesIO) -> str:
    try:
        content = file_obj.read().decode("utf-8", errors="ignore")
        return content.strip()
    finally:
        file_obj.seek(0)


def _read_pdf(file_obj: BytesIO) -> str:
    """
    Lightweight PDF text extractor using PyPDF2.
    If PyPDF2 is not installed, return an empty string instead of crashing.
    """
    try:
        import PyPDF2  # type: ignore
    except ImportError:
        return ""

    text_chunks = []
    try:
        reader = PyPDF2.PdfReader(file_obj)
        for page in reader.pages:
            try:
                page_text = page.extract_text() or ""
                text_chunks.append(page_text)
            except Exception:
                continue
    finally:
        file_obj.seek(0)

    return "\n".join(text_chunks).strip()


def _read_docx(file_obj: BytesIO) -> str:
    """
    DOCX text extractor using python-docx.
    If python-docx is not installed, return empty string.
    """
    try:
        import docx  # type: ignore
    except ImportError:
        return ""

    try:
        document = docx.Document(file_obj)
        paragraphs = [p.text for p in document.paragraphs if p.text]
        return "\n".join(paragraphs).strip()
    finally:
        file_obj.seek(0)


def _read_csv(file_obj: BytesIO) -> str:
    """
    Convert CSV into a readable text summary using pandas.
    If pandas is not installed, return raw decoded text.
    """
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        try:
            content = file_obj.read().decode("utf-8", errors="ignore")
            return content.strip()
        finally:
            file_obj.seek(0)

    try:
        df = pd.read_csv(file_obj)
        return df.to_csv(index=False)
    finally:
        file_obj.seek(0)


def _read_xlsx(file_obj: BytesIO) -> str:
    """
    Convert Excel into a readable text summary using pandas.
    If pandas/openpyxl are not installed, return empty string.
    """
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        return ""

    try:
        # read all sheets and join
        excel = pd.read_excel(file_obj, sheet_name=None)
        parts = []
        for name, df in excel.items():
            parts.append(f"Sheet: {name}")
            parts.append(df.to_csv(index=False))
        return "\n\n".join(parts).strip()
    finally:
        file_obj.seek(0)
