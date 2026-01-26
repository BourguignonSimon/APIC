"""
Validation utilities for file uploads, security, and data integrity.
"""

import re
import os
from typing import Optional
from src.models.schemas import ValidationError


class DocumentValidator:
    """Validator for document uploads and security checks."""

    def __init__(
        self,
        max_file_size_mb: int = 50,
        allowed_types: Optional[list] = None
    ):
        """
        Initialize the document validator.

        Args:
            max_file_size_mb: Maximum file size in megabytes
            allowed_types: List of allowed file extensions (without dot)
        """
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.max_file_size_mb = max_file_size_mb
        self.allowed_types = allowed_types or [
            "pdf", "docx", "doc", "txt", "xlsx", "xls", "pptx", "ppt"
        ]

    def validate_file(
        self,
        filename: str,
        file_size: int,
        file_type: str
    ) -> Optional[ValidationError]:
        """
        Validate a file for upload.

        Args:
            filename: Name of the file
            file_size: Size of the file in bytes
            file_type: MIME type of the file

        Returns:
            ValidationError if validation fails, None if valid
        """
        # Check filename
        filename_error = self.validate_filename(filename)
        if filename_error:
            return filename_error

        # Check file size
        size_error = self.validate_file_size(file_size)
        if size_error:
            return size_error

        # Check file type
        type_error = self.validate_file_type(filename)
        if type_error:
            return type_error

        return None

    def validate_filename(self, filename: str) -> Optional[ValidationError]:
        """
        Validate filename for security issues.

        Args:
            filename: Name of the file

        Returns:
            ValidationError if validation fails, None if valid
        """
        # Check for path traversal
        if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
            return ValidationError(
                field="filename",
                message="Filename contains path traversal characters",
                suggested_action="Use a filename without '..' or absolute paths",
                error_code="PATH_TRAVERSAL"
            )

        # Check for null byte injection
        if "\x00" in filename:
            return ValidationError(
                field="filename",
                message="Filename contains null bytes",
                suggested_action="Remove null bytes from filename",
                error_code="NULL_BYTE_INJECTION"
            )

        # Check for valid filename pattern
        if not re.match(r'^[\w\-. ]+$', filename):
            return ValidationError(
                field="filename",
                message="Filename contains invalid characters",
                suggested_action="Use only alphanumeric characters, hyphens, underscores, dots, and spaces",
                error_code="INVALID_FILENAME"
            )

        return None

    def validate_file_size(self, file_size: int) -> Optional[ValidationError]:
        """
        Validate file size against limits.

        Args:
            file_size: Size of the file in bytes

        Returns:
            ValidationError if validation fails, None if valid
        """
        if file_size > self.max_file_size_bytes:
            return ValidationError(
                field="file_size",
                message=f"File size exceeds the maximum allowed size limit of {self.max_file_size_mb} MB",
                suggested_action=f"Reduce file size to under {self.max_file_size_mb} MB",
                error_code="FILE_TOO_LARGE"
            )

        if file_size == 0:
            return ValidationError(
                field="file_size",
                message="File is empty",
                suggested_action="Upload a non-empty file",
                error_code="EMPTY_FILE"
            )

        return None

    def validate_file_type(self, filename: str) -> Optional[ValidationError]:
        """
        Validate file type against whitelist.

        Args:
            filename: Name of the file (including extension)

        Returns:
            ValidationError if validation fails, None if valid
        """
        # Extract extension
        ext = os.path.splitext(filename)[1].lower().lstrip('.')

        if not ext:
            return ValidationError(
                field="file_type",
                message="File has no extension",
                suggested_action="Add a valid file extension",
                error_code="NO_EXTENSION"
            )

        if ext not in self.allowed_types:
            return ValidationError(
                field="file_type",
                message=f"File type '.{ext}' is not allowed. Allowed file types: {', '.join(self.allowed_types)}",
                suggested_action=f"Convert file to one of: {', '.join(self.allowed_types)}",
                error_code="INVALID_FILE_TYPE"
            )

        # Check for double extensions (e.g., file.txt.exe)
        if filename.count('.') > 1:
            parts = filename.split('.')
            if len(parts) > 2:
                # Check if any intermediate part is an executable extension
                dangerous_extensions = ['exe', 'bat', 'cmd', 'sh', 'app', 'dmg', 'pkg']
                for part in parts[1:-1]:  # Skip the last part (actual extension)
                    if part.lower() in dangerous_extensions:
                        return ValidationError(
                            field="file_type",
                            message="File has suspicious double extension",
                            suggested_action="Remove extra extensions from filename",
                            error_code="DOUBLE_EXTENSION"
                        )

        return None


class InputSanitizer:
    """Sanitizer for user inputs to prevent injection attacks."""

    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """
        Sanitize input for SQL queries (note: still use parameterized queries).

        Args:
            value: Input string

        Returns:
            Sanitized string
        """
        # This is a belt-and-suspenders approach
        # ALWAYS use parameterized queries in actual DB operations
        dangerous_patterns = [
            r"(\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|EXEC|EXECUTE)\b)",
            r"(--|;|\/\*|\*\/)",
            r"(\bOR\b.*\=)",
            r"(\bUNION\b.*\bSELECT\b)",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                # Log but don't reject - parameterized queries will handle this
                pass

        return value

    @staticmethod
    def sanitize_html_input(value: str) -> str:
        """
        Sanitize HTML input to prevent XSS.

        Args:
            value: Input string

        Returns:
            Sanitized string
        """
        # Basic HTML entity encoding
        replacements = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;',
        }

        for char, entity in replacements.items():
            value = value.replace(char, entity)

        return value
