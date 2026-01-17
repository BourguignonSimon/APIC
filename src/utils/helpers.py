"""
Helper Utilities
Common helper functions used across the application.
"""

import hashlib
import os
import re
import uuid
from datetime import datetime
from typing import Optional


def generate_uuid() -> str:
    """Generate a unique identifier."""
    return str(uuid.uuid4())


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string.

    Args:
        dt: Datetime object
        format_str: Format string

    Returns:
        Formatted datetime string
    """
    if dt is None:
        return ""
    return dt.strftime(format_str)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to remove unsafe characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path separators and other unsafe chars
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    return filename or "unnamed_file"


def calculate_file_hash(file_path: str, algorithm: str = "md5") -> Optional[str]:
    """
    Calculate hash of a file.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha256, etc.)

    Returns:
        Hash string or None if file not found
    """
    if not os.path.exists(file_path):
        return None

    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_comma_separated(value: str) -> list:
    """
    Parse comma-separated string into list.

    Args:
        value: Comma-separated string

    Returns:
        List of stripped values
    """
    if not value:
        return []
    return [v.strip() for v in value.split(',') if v.strip()]
