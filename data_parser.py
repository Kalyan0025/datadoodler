import io
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None


def _read_txt(uploaded_file) -> str:
    bytes_data = uploaded_file.read()
    try:
        return bytes_data.decode("utf-8", errors="ignore")
    except Exception:
        return bytes_data.decode(errors="ignore")


def _read_pdf(uploaded_file) -> str:
    if PdfReader is None:
        return "PDF reader library not installed; please install 'pypdf'."

    reader = PdfReader(uploaded_file)
    text_chunks = []
    for page in reader.pages:
        try:
            text_chunks.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n\n".join(text_chunks)


def _read_docx(uploaded_file) -> str:
    if docx is None:
        return "DOCX reader library not installed; please install 'python-docx'."

    # uploaded_file is a SpooledTemporaryFile-like object
    mem = io.BytesIO(uploaded_file.read())
    document = docx.Document(mem)
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _read_csv(uploaded_file) -> str:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding_errors="ignore")

    desc = []
    desc.append(f"Table data with {len(df)} rows and {len(df.columns)} columns.")
    if len(df.columns) > 0:
        desc.append("Columns: " + ", ".join(df.columns.astype(str)))
    head_str = df.head(10).to_string(index=False)
    desc.append("First rows:\n" + head_str)
    return "\n\n".join(desc)


def _read_xlsx(uploaded_file) -> str:
    # Read first sheet only
    xl = pd.ExcelFile(uploaded_file)
    sheet_name = xl.sheet_names[0]
    df = xl.parse(sheet_name)

    desc = []
    desc.append(f"Excel sheet '{sheet_name}' with {len(df)} rows and {len(df.columns)} columns.")
    if len(df.columns) > 0:
        desc.append("Columns: " + ", ".join(df.columns.astype(str)))
    head_str = df.head(10).to_string(index=False)
    desc.append("First rows:\n" + head_str)
    return "\n\n".join(desc)


def _extract_text_from_file(uploaded_file) -> str:
    if uploaded_file is None:
        return ""

    name = uploaded_file.name
    suffix = Path(name).suffix.lower()

    # Reset pointer just in case
    uploaded_file.seek(0)

    if suffix == ".txt":
        return _read_txt(uploaded_file)
    elif suffix == ".pdf":
        return _read_pdf(uploaded_file)
    elif suffix == ".docx":
        return _read_docx(uploaded_file)
    elif suffix == ".csv":
        return _read_csv(uploaded_file)
    elif suffix in [".xlsx", ".xls"]:
        return _read_xlsx(uploaded_file)
    else:
        # Fallback: try to decode as text
        return _read_txt(uploaded_file)


def _normalize_data_type(data_type: str) -> str:
    mapping = {
        "Dream": "dream",
        "Memory": "memory",
        "Daily Routine": "daily_routine",
        "Weekly Routine": "weekly_routine",
        "Office / Attendance Data": "office_attendance",
        "Activity Log": "activity_log",
        "Creative / Story": "creative_story",
        "Mixed / Let AI Detect": "mixed"
    }
    return mapping.get(data_type, "mixed")


def parse_input(
    raw_text: str,
    uploaded_file,
    data_type: str,
    gemini
) -> Dict[str, Any]:
    """
    Main entry used by app.py.

    We DON'T over-structure here.
    We simply:
      - read whatever the user gave (text or file)
      - unify it into a big, descriptive context string
      - attach metadata (type, file name, etc.)

    Gemini will then:
      - understand the content
      - infer scenes / events / patterns
      - design the visual spec in a Data Humanism style.
    """

    source_text = ""

    if uploaded_file is not None:
        file_text = _extract_text_from_file(uploaded_file)
        source_text = file_text
        file_name = uploaded_file.name
        source_kind = "file"
    else:
        source_text = raw_text or ""
        file_name = None
        source_kind = "text"

    normalized_type = _normalize_data_type(data_type)

    # Build a compact meta-description for Gemini
    meta_description_parts = [
        f"Data kind: {data_type} (normalized as '{normalized_type}').",
        f"Source: {source_kind}.",
    ]
    if file_name:
        meta_description_parts.append(f"Original file name: {file_name}.")

    meta_description = " ".join(meta_description_parts)

    # Limit text length gently to avoid crazy-long prompts (Gemini can handle a lot,
    # but we don't need millions of characters).
    max_chars = 20000
    if len(source_text) > max_chars:
        truncated_note = "\n\n[Note: Content truncated for length. Only the first part is shown here.]"
        source_text = source_text[:max_chars] + truncated_note

    input_data: Dict[str, Any] = {
        "data_kind": normalized_type,
        "data_kind_label": data_type,
        "source": source_kind,
        "file_name": file_name,
        "meta_description": meta_description,
        "raw_text": source_text
    }

    return input_data
