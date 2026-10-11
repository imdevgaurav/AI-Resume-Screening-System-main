from pathlib import Path

from pypdf import PdfReader


class FileParserError(Exception):
    pass


def allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")

    if extension == ".pdf":
        return _extract_pdf_text(path)

    raise FileParserError(f"Unsupported file type: {extension}")


def _extract_pdf_text(file_path: Path) -> str:
    try:
        reader = PdfReader(str(file_path))
        parts = [(page.extract_text() or "").strip() for page in reader.pages]
    except Exception as exc:
        raise FileParserError("Unable to read PDF file.") from exc

    text = "\n".join(part for part in parts if part)
    if not text.strip():
        raise FileParserError("No extractable text found in PDF.")
    return text
