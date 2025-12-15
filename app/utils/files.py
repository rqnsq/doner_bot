"""
Utility helpers for file operations.

Single responsibility: encapsulate file I/O logic to avoid duplication across modules.
"""

from typing import Optional
from pathlib import Path


def read_file(filename: str) -> Optional[str]:
    """Read file content as UTF-8 and return string or None on error.

    Args:
        filename: File path (relative or absolute).

    Returns:
        File contents as string, or None if file not found or read fails.
    """
    try:
        filepath = Path(filename)
        return filepath.read_text(encoding='utf-8')
    except FileNotFoundError:
        return None
    except Exception:
        return None
