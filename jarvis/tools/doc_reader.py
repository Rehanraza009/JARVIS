"""
Document reader and parser for JARVIS.
Safely extracts text from local files (.txt, .md, .py, .pdf, .json, .csv)
to answer questions, debug, and provide summaries.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from jarvis.core.logger import jarvis_logger

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


class DocumentReader:
    SUPPORTED_EXTENSIONS = {
        ".txt", ".md", ".py", ".json", ".csv", ".log", ".html", ".css", ".js", ".sql", ".pdf"
    }

    @classmethod
    def read_file(cls, file_path_str: str, max_chars: int = 15000) -> Dict[str, Any]:
        """
        Safely reads file content. Returns dict:
        {'success': bool, 'filename': str, 'content': str, 'error': str}
        """
        path = Path(file_path_str).resolve()

        if not path.exists():
            return {
                "success": False,
                "filename": path.name,
                "content": "",
                "error": f"File '{path}' does not exist."
            }

        if not path.is_file():
            return {
                "success": False,
                "filename": path.name,
                "content": "",
                "error": f"Path '{path}' is not a regular file."
            }

        ext = path.suffix.lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            return {
                "success": False,
                "filename": path.name,
                "content": "",
                "error": f"File extension '{ext}' is not supported for reading."
            }

        try:
            # Handle PDF
            if ext == ".pdf":
                if not HAS_PYPDF:
                    return {
                        "success": False,
                        "filename": path.name,
                        "content": "",
                        "error": "pypdf library is not installed."
                    }
                reader = PdfReader(str(path))
                text_parts = []
                for idx, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {idx+1} ---\n{page_text}")
                    if sum(len(p) for p in text_parts) >= max_chars:
                        break
                full_text = "\n".join(text_parts)[:max_chars]
                return {
                    "success": True,
                    "filename": path.name,
                    "content": full_text,
                    "error": ""
                }

            # Handle text/code files
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_chars)
                return {
                    "success": True,
                    "filename": path.name,
                    "content": content,
                    "error": ""
                }

        except Exception as e:
            jarvis_logger.error(f"Failed to read file {path}: {e}")
            return {
                "success": False,
                "filename": path.name,
                "content": "",
                "error": str(e)
            }


doc_reader = DocumentReader()
