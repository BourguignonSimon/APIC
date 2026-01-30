"""
Utility functions for the APIC frontend.
"""

import requests
from datetime import datetime
from typing import Optional, Dict, Any

import streamlit as st

from config import API_BASE_URL


def api_request(method: str, endpoint: str, show_error: bool = True, **kwargs) -> Optional[Dict[str, Any]]:
    """Make API request with error handling."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, timeout=120, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        if show_error:
            st.error("Request timed out. The server is taking too long to respond. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        if show_error:
            st.error("Unable to connect to the server. Please check if the backend service is running.")
        return None
    except requests.exceptions.HTTPError as e:
        if show_error:
            if e.response.status_code == 404:
                st.error("The requested resource was not found.")
            elif e.response.status_code == 500:
                st.error("Server error occurred. Please try again or contact support.")
            else:
                st.error(f"Request failed: {e.response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        if show_error:
            st.error(f"An error occurred: {str(e)}")
        return None


def format_datetime(dt_str: str) -> str:
    """Format datetime string for display."""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y @ %I:%M %p")
    except Exception:
        return dt_str


def get_status_info(status: str) -> Dict[str, str]:
    """Get status display information."""
    status_map = {
        "created": {"label": "New", "class": "status-created", "description": "Project created, awaiting documents"},
        "analyzing": {"label": "Analyzing", "class": "status-analyzing", "description": "AI is analyzing documents"},
        "interview_ready": {"label": "Interview Ready", "class": "status-interview_ready", "description": "Interview script generated"},
        "processing": {"label": "Processing", "class": "status-processing", "description": "Processing interview results"},
        "completed": {"label": "Completed", "class": "status-completed", "description": "Analysis complete"},
        "failed": {"label": "Failed", "class": "status-failed", "description": "An error occurred"},
    }
    return status_map.get(status, {"label": status.replace("_", " ").title(), "class": "status-created", "description": ""})


def get_file_icon(file_type: str) -> str:
    """Get icon for file type."""
    icons = {
        "pdf": "PDF",
        "docx": "DOC",
        "doc": "DOC",
        "xlsx": "XLS",
        "xls": "XLS",
        "pptx": "PPT",
        "ppt": "PPT",
        "txt": "TXT",
    }
    return icons.get(file_type.lower(), "FILE")
