"""
APIC Streamlit Frontend
Production-ready user interface for the Agentic Process Improvement Consultant.
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List

import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="APIC - Process Improvement Consultant",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# Professional Design System CSS
# ============================================================================

st.markdown("""
<style>
    /* ===== CSS Variables / Design Tokens ===== */
    :root {
        --primary-color: #2563eb;
        --primary-dark: #1d4ed8;
        --primary-light: #3b82f6;
        --secondary-color: #64748b;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --background-color: #f8fafc;
        --card-background: #ffffff;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --text-muted: #94a3b8;
        --border-color: #e2e8f0;
        --border-radius: 12px;
        --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    }

    /* ===== Global Styles ===== */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* ===== Typography ===== */
    .page-title {
        font-size: 2.25rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }

    .page-subtitle {
        font-size: 1.125rem;
        color: var(--text-secondary);
        margin-bottom: 2rem;
        line-height: 1.5;
    }

    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--primary-color);
        display: inline-block;
    }

    .subsection-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.75rem;
    }

    /* ===== Cards ===== */
    .info-card {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }

    .info-card:hover {
        box-shadow: var(--shadow-md);
        border-color: var(--primary-light);
    }

    .feature-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        height: 100%;
        transition: all 0.3s ease;
    }

    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }

    .feature-card-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }

    .feature-card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.75rem;
    }

    .feature-card-text {
        color: var(--text-secondary);
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* ===== Project Cards ===== */
    .project-card {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
    }

    .project-card:hover {
        border-color: var(--primary-color);
        box-shadow: var(--shadow-md);
    }

    .project-name {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }

    .project-client {
        font-size: 0.875rem;
        color: var(--text-secondary);
    }

    .project-meta {
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    /* ===== Status Badges ===== */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.375rem 0.875rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }

    .status-badge::before {
        content: "";
        width: 6px;
        height: 6px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }

    .status-created {
        background-color: #dbeafe;
        color: #1e40af;
    }
    .status-created::before { background-color: #1e40af; }

    .status-analyzing {
        background-color: #fef3c7;
        color: #92400e;
    }
    .status-analyzing::before { background-color: #f59e0b; animation: pulse 1.5s infinite; }

    .status-interview_ready {
        background-color: #fed7aa;
        color: #9a3412;
    }
    .status-interview_ready::before { background-color: #ea580c; }

    .status-processing {
        background-color: #e0e7ff;
        color: #3730a3;
    }
    .status-processing::before { background-color: #4f46e5; animation: pulse 1.5s infinite; }

    .status-completed {
        background-color: #d1fae5;
        color: #065f46;
    }
    .status-completed::before { background-color: #059669; }

    .status-failed {
        background-color: #fee2e2;
        color: #991b1b;
    }
    .status-failed::before { background-color: #dc2626; }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* ===== Metrics Cards ===== */
    .metric-card {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.25rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
    }

    .metric-card.primary::before { background: var(--primary-color); }
    .metric-card.success::before { background: var(--success-color); }
    .metric-card.warning::before { background: var(--warning-color); }
    .metric-card.secondary::before { background: var(--secondary-color); }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1;
        margin-bottom: 0.5rem;
    }

    .metric-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ===== Steps / Workflow Indicator ===== */
    .workflow-step {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        padding: 1rem 0;
    }

    .step-number {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--primary-color);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1.125rem;
        flex-shrink: 0;
    }

    .step-number.completed {
        background: var(--success-color);
    }

    .step-number.pending {
        background: var(--border-color);
        color: var(--text-muted);
    }

    .step-content h4 {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }

    .step-content p {
        color: var(--text-secondary);
        margin: 0;
        font-size: 0.95rem;
    }

    /* ===== Sidebar Styles ===== */
    .sidebar-brand {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 0.25rem;
    }

    .sidebar-tagline {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-bottom: 1.5rem;
    }

    .sidebar-section {
        margin-bottom: 1.5rem;
    }

    .sidebar-section-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.75rem;
    }

    .current-project-info {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        padding: 1rem;
    }

    .current-project-name {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }

    .current-project-client {
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
    }

    /* ===== Buttons ===== */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
    }

    /* ===== Forms ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }

    /* ===== Tabs ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background-color: #f1f5f9;
        padding: 0.5rem;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.25rem;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background-color: white;
        box-shadow: var(--shadow-sm);
    }

    /* ===== Expanders ===== */
    .streamlit-expanderHeader {
        font-weight: 500;
        color: var(--text-primary);
    }

    /* ===== Alerts / Info Boxes ===== */
    .custom-info {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 1px solid #93c5fd;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
    }

    .custom-info-icon {
        font-size: 1.25rem;
        flex-shrink: 0;
    }

    .custom-info-text {
        color: #1e40af;
        font-size: 0.95rem;
    }

    .custom-success {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 1px solid #6ee7b7;
        border-radius: 8px;
        padding: 1rem 1.25rem;
    }

    .custom-success-text {
        color: #065f46;
    }

    .custom-warning {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border: 1px solid #fcd34d;
        border-radius: 8px;
        padding: 1rem 1.25rem;
    }

    .custom-warning-text {
        color: #92400e;
    }

    /* ===== Empty State ===== */
    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        background: var(--background-color);
        border-radius: var(--border-radius);
        border: 2px dashed var(--border-color);
    }

    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }

    .empty-state-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }

    .empty-state-text {
        color: var(--text-secondary);
        margin-bottom: 1.5rem;
    }

    /* ===== Document List ===== */
    .document-item {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        margin-bottom: 0.5rem;
        gap: 0.75rem;
    }

    .document-icon {
        font-size: 1.5rem;
    }

    .document-name {
        font-weight: 500;
        color: var(--text-primary);
        flex-grow: 1;
    }

    .document-meta {
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    .document-status {
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
    }

    .document-status.processed {
        background: #d1fae5;
        color: #065f46;
    }

    .document-status.pending {
        background: #fef3c7;
        color: #92400e;
    }

    /* ===== Question Cards ===== */
    .question-card {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.25rem;
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary-color);
    }

    .question-number {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--primary-color);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .question-role {
        display: inline-block;
        background: #eff6ff;
        color: #1e40af;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-bottom: 0.75rem;
    }

    .question-text {
        font-size: 1rem;
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 0.75rem;
        line-height: 1.5;
    }

    .question-intent {
        font-size: 0.875rem;
        color: var(--text-secondary);
        font-style: italic;
        margin-bottom: 0.75rem;
    }

    .follow-up-list {
        margin: 0;
        padding-left: 1.25rem;
    }

    .follow-up-list li {
        color: var(--text-secondary);
        font-size: 0.875rem;
        margin-bottom: 0.25rem;
    }

    /* ===== Gap/Solution Cards ===== */
    .analysis-card {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    .analysis-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border-color);
    }

    .analysis-card-title {
        font-weight: 600;
        color: var(--text-primary);
    }

    .priority-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .priority-high {
        background: #fee2e2;
        color: #991b1b;
    }

    .priority-medium {
        background: #fef3c7;
        color: #92400e;
    }

    .priority-low {
        background: #d1fae5;
        color: #065f46;
    }

    /* ===== Report Summary ===== */
    .report-summary {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1px solid #86efac;
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .report-metric {
        text-align: center;
        padding: 1rem;
    }

    .report-metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #166534;
        margin-bottom: 0.25rem;
    }

    .report-metric-label {
        font-size: 0.8rem;
        color: #15803d;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ===== Help Tooltip ===== */
    .help-text {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-top: 0.25rem;
    }

    /* ===== Loading Indicator ===== */
    .loading-container {
        text-align: center;
        padding: 2rem;
    }

    .loading-spinner {
        font-size: 2rem;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    /* ===== Responsive Design ===== */
    @media (max-width: 768px) {
        .page-title {
            font-size: 1.75rem;
        }

        .feature-card {
            padding: 1rem;
        }

        .metric-value {
            font-size: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Helper Functions
# ============================================================================

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
        return dt.strftime("%b %d, %Y • %I:%M %p")
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


def display_status_badge(status: str):
    """Display status badge with appropriate styling."""
    info = get_status_info(status)
    st.markdown(
        f'<span class="status-badge {info["class"]}">{info["label"]}</span>',
        unsafe_allow_html=True
    )


def get_file_icon(file_type: str) -> str:
    """Get icon for file type."""
    icons = {
        "pdf": "📄",
        "docx": "📝",
        "doc": "📝",
        "xlsx": "📊",
        "xls": "📊",
        "pptx": "📑",
        "ppt": "📑",
        "txt": "📃",
    }
    return icons.get(file_type.lower(), "📄")


def render_empty_state(icon: str, title: str, message: str, show_button: bool = False, button_label: str = "", button_key: str = "") -> bool:
    """Render an empty state message. Returns True if button was clicked."""
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-text">{message}</div>
    </div>
    """, unsafe_allow_html=True)

    if show_button:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            return st.button(button_label, key=button_key, use_container_width=True, type="primary")
    return False


def render_info_message(message: str, icon: str = "ℹ️"):
    """Render a custom info message."""
    st.markdown(f"""
    <div class="custom-info">
        <span class="custom-info-icon">{icon}</span>
        <span class="custom-info-text">{message}</span>
    </div>
    """, unsafe_allow_html=True)


def render_success_message(message: str, icon: str = "✅"):
    """Render a custom success message."""
    st.markdown(f"""
    <div class="custom-success">
        <span class="custom-info-icon">{icon}</span>
        <span class="custom-success-text">{message}</span>
    </div>
    """, unsafe_allow_html=True)


def render_warning_message(message: str, icon: str = "⚠️"):
    """Render a custom warning message."""
    st.markdown(f"""
    <div class="custom-warning">
        <span class="custom-info-icon">{icon}</span>
        <span class="custom-warning-text">{message}</span>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# Session State Initialization
# ============================================================================

if "current_project" not in st.session_state:
    st.session_state.current_project = None
if "page" not in st.session_state:
    st.session_state.page = "home"
if "show_success" not in st.session_state:
    st.session_state.show_success = None


# ============================================================================
# Sidebar Navigation
# ============================================================================

with st.sidebar:
    st.markdown('<div class="sidebar-brand">🔄 APIC</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">Agentic Process Improvement Consultant</div>', unsafe_allow_html=True)

    st.divider()

    # Navigation Section
    st.markdown('<div class="sidebar-section-title">Navigation</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Home", use_container_width=True, key="nav_home"):
            st.session_state.page = "home"
            st.session_state.current_project = None
            st.rerun()
    with col2:
        if st.button("📁 Projects", use_container_width=True, key="nav_projects"):
            st.session_state.page = "projects"
            st.rerun()

    if st.button("➕ New Project", use_container_width=True, type="primary", key="nav_new"):
        st.session_state.page = "new_project"
        st.rerun()

    st.divider()

    # Current Project Section
    if st.session_state.current_project:
        st.markdown('<div class="sidebar-section-title">Current Project</div>', unsafe_allow_html=True)
        project = st.session_state.current_project
        st.markdown(f"""
        <div class="current-project-info">
            <div class="current-project-name">{project.get('project_name', 'Unnamed Project')}</div>
            <div class="current-project-client">{project.get('client_name', 'No client')}</div>
        </div>
        """, unsafe_allow_html=True)
        display_status_badge(project.get('status', 'unknown'))

        st.divider()

    # Help Section
    st.markdown('<div class="sidebar-section-title">Help</div>', unsafe_allow_html=True)
    with st.expander("📖 How to Use APIC"):
        st.markdown("""
        **1. Create a Project**
        Start by creating a new project with your client's information.

        **2. Upload Documents**
        Upload SOPs, process docs, and training materials.

        **3. Run Analysis**
        Let APIC analyze documents and generate interview questions.

        **4. Conduct Interview**
        Use the generated script to interview stakeholders.

        **5. Submit Transcript**
        Paste the interview notes to get recommendations.

        **6. Review Results**
        Get gap analysis, solutions, and ROI estimates.
        """)

    st.markdown("---")
    st.markdown('<div style="font-size: 0.75rem; color: #94a3b8; text-align: center;">APIC v1.0</div>', unsafe_allow_html=True)


# ============================================================================
# Page: Home
# ============================================================================

def page_home():
    """Render the home page with welcome message and quick stats."""

    # Header
    st.markdown('<div class="page-title">Welcome to APIC</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Your AI-Powered Process Improvement Consultant. Analyze processes, identify gaps, and get actionable recommendations.</div>', unsafe_allow_html=True)

    # Quick Actions
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("➕ Create New Project", use_container_width=True, type="primary"):
            st.session_state.page = "new_project"
            st.rerun()
    with col2:
        if st.button("📁 View All Projects", use_container_width=True):
            st.session_state.page = "projects"
            st.rerun()
    with col3:
        pass  # Placeholder for symmetry

    st.markdown("<br>", unsafe_allow_html=True)

    # How It Works Section
    st.markdown('<div class="section-title">How It Works</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-card-icon">📤</div>
            <div class="feature-card-title">1. Upload Documents</div>
            <div class="feature-card-text">
                Upload your process documentation including SOPs, workflows, policy documents, and training materials. Supported formats: PDF, Word, PowerPoint, Excel, and text files.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-card-icon">🎯</div>
            <div class="feature-card-title">2. AI-Powered Analysis</div>
            <div class="feature-card-text">
                APIC analyzes your documents to identify potential inefficiencies and generates a customized interview script with targeted questions for key stakeholders.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-card-icon">📊</div>
            <div class="feature-card-title">3. Get Recommendations</div>
            <div class="feature-card-text">
                After the interview, receive comprehensive gap analysis, automation recommendations with technology suggestions, and ROI estimates for each improvement.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Project Statistics
    projects = api_request("GET", "/projects", show_error=False)

    if projects and len(projects) > 0:
        st.markdown('<div class="section-title">Project Overview</div>', unsafe_allow_html=True)

        total = len(projects)
        completed = len([p for p in projects if p.get("status") == "completed"])
        interview_ready = len([p for p in projects if p.get("status") == "interview_ready"])
        new_projects = len([p for p in projects if p.get("status") == "created"])

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card primary">
                <div class="metric-value">{total}</div>
                <div class="metric-label">Total Projects</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card success">
                <div class="metric-value">{completed}</div>
                <div class="metric-label">Completed</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card warning">
                <div class="metric-value">{interview_ready}</div>
                <div class="metric-label">Awaiting Interview</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card secondary">
                <div class="metric-value">{new_projects}</div>
                <div class="metric-label">New</div>
            </div>
            """, unsafe_allow_html=True)

        # Recent Projects
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="subsection-title">Recent Projects</div>', unsafe_allow_html=True)

        for project in projects[:3]:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{project.get('project_name', 'Unnamed')}** — {project.get('client_name', 'N/A')}")
            with col2:
                display_status_badge(project.get('status', 'unknown'))
            with col3:
                if st.button("Open", key=f"home_open_{project['id']}"):
                    full_project = api_request("GET", f"/projects/{project['id']}")
                    if full_project:
                        st.session_state.current_project = full_project
                        st.session_state.page = "project_detail"
                        st.rerun()


# ============================================================================
# Page: New Project
# ============================================================================

def page_new_project():
    """Render the new project creation page."""

    st.markdown('<div class="page-title">Create New Project</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Set up a new consulting engagement. You can add documents after creating the project.</div>', unsafe_allow_html=True)

    # Form Container
    st.markdown('<div class="info-card">', unsafe_allow_html=True)

    with st.form("new_project_form", clear_on_submit=False):
        # Client Information
        st.markdown("##### Client Information")

        col1, col2 = st.columns(2)
        with col1:
            client_name = st.text_input(
                "Client Name *",
                placeholder="e.g., Acme Corporation",
                help="The name of the client organization"
            )
        with col2:
            project_name = st.text_input(
                "Project Name *",
                placeholder="e.g., Q1 2025 Process Optimization",
                help="A descriptive name for this engagement"
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Project Details")

        description = st.text_area(
            "Description",
            placeholder="Describe the scope and objectives of this consulting engagement...",
            help="Optional: Provide context about the project goals",
            height=100
        )

        departments = st.text_input(
            "Target Departments",
            placeholder="e.g., Finance, Operations, HR",
            help="Comma-separated list of departments to analyze"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submitted = st.form_submit_button("Create Project", use_container_width=True, type="primary")

        if submitted:
            # Validation
            errors = []
            if not client_name or not client_name.strip():
                errors.append("Client name is required")
            if not project_name or not project_name.strip():
                errors.append("Project name is required")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                dept_list = [d.strip() for d in departments.split(",") if d.strip()] if departments else []

                with st.spinner("Creating project..."):
                    result = api_request(
                        "POST",
                        "/projects",
                        json={
                            "client_name": client_name.strip(),
                            "project_name": project_name.strip(),
                            "description": description.strip() if description else "",
                            "target_departments": dept_list,
                        }
                    )

                if result:
                    st.session_state.current_project = result
                    st.session_state.page = "project_detail"
                    st.session_state.show_success = "Project created successfully! Now upload your documents to get started."
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Cancel Button
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()


# ============================================================================
# Page: Project List
# ============================================================================

def page_projects():
    """Render the project listing page."""

    st.markdown('<div class="page-title">All Projects</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">View and manage your consulting projects.</div>', unsafe_allow_html=True)

    # Action Bar
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ New Project", use_container_width=True, type="primary"):
            st.session_state.page = "new_project"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Fetch Projects
    projects = api_request("GET", "/projects")

    if not projects or len(projects) == 0:
        if render_empty_state(
            "📁",
            "No Projects Yet",
            "Create your first project to get started with process improvement analysis.",
            show_button=True,
            button_label="Create First Project",
            button_key="empty_create_project"
        ):
            st.session_state.page = "new_project"
            st.rerun()
        return

    # Project List
    for project in projects:
        with st.container():
            col1, col2, col3, col4 = st.columns([2.5, 1.5, 1, 1])

            with col1:
                st.markdown(f"""
                <div class="project-name">{project.get('project_name', 'Unnamed Project')}</div>
                <div class="project-client">📍 {project.get('client_name', 'No client specified')}</div>
                """, unsafe_allow_html=True)

            with col2:
                display_status_badge(project.get('status', 'unknown'))
                st.markdown(f'<div class="project-meta">{format_datetime(project.get("created_at", ""))}</div>', unsafe_allow_html=True)

            with col3:
                # Show document count if available
                docs = project.get('documents', [])
                if docs:
                    st.markdown(f'<div class="project-meta">📄 {len(docs)} docs</div>', unsafe_allow_html=True)

            with col4:
                if st.button("Open →", key=f"open_{project['id']}", use_container_width=True):
                    with st.spinner("Loading project..."):
                        full_project = api_request("GET", f"/projects/{project['id']}")
                        if full_project:
                            st.session_state.current_project = full_project
                            st.session_state.page = "project_detail"
                            st.rerun()

            st.divider()


# ============================================================================
# Page: Project Detail
# ============================================================================

def page_project_detail():
    """Render the project detail page with tabs for different sections."""

    project = st.session_state.current_project

    if not project:
        st.error("No project selected. Please select a project from the list.")
        if st.button("← Go to Projects"):
            st.session_state.page = "projects"
            st.rerun()
        return

    # Show success message if set
    if st.session_state.show_success:
        render_success_message(st.session_state.show_success)
        st.session_state.show_success = None
        st.markdown("<br>", unsafe_allow_html=True)

    # Header
    col1, col2, col3 = st.columns([2.5, 1, 0.5])
    with col1:
        st.markdown(f'<div class="page-title">{project.get("project_name", "Project")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="page-subtitle">📍 {project.get("client_name", "No client")} • Created {format_datetime(project.get("created_at", ""))}</div>', unsafe_allow_html=True)
    with col2:
        display_status_badge(project.get('status', 'unknown'))
    with col3:
        if st.button("🔄", help="Refresh project data", key="refresh_project"):
            with st.spinner("Refreshing..."):
                updated = api_request("GET", f"/projects/{project['id']}")
                if updated:
                    st.session_state.current_project = updated
                    st.rerun()

    st.divider()

    project_id = project.get('id')

    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Documents",
        "🔍 Analysis",
        "🎤 Interview",
        "📊 Results",
        "📋 Report"
    ])

    # =========== Documents Tab ===========
    with tab1:
        render_documents_tab(project_id)

    # =========== Analysis Tab ===========
    with tab2:
        render_analysis_tab(project_id)

    # =========== Interview Tab ===========
    with tab3:
        render_interview_tab(project_id)

    # =========== Results Tab ===========
    with tab4:
        render_results_tab(project_id)

    # =========== Report Tab ===========
    with tab5:
        render_report_tab(project_id)


def render_documents_tab(project_id: str):
    """Render the documents upload and listing tab."""

    st.markdown("### Upload Documents")
    st.markdown("Upload your process documentation to begin analysis. Supported formats: PDF, Word, PowerPoint, Excel, and text files.")

    # File Uploader
    uploaded_files = st.file_uploader(
        "Drag and drop files here or click to browse",
        type=["pdf", "docx", "doc", "txt", "pptx", "xlsx", "xls"],
        accept_multiple_files=True,
        help="Maximum file size: 50MB per file",
        key="doc_uploader"
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected**")
        for f in uploaded_files:
            st.markdown(f"• {f.name} ({f.size / 1024:.1f} KB)")

        if st.button("📤 Upload Files", use_container_width=True, type="primary"):
            with st.spinner(f"Uploading {len(uploaded_files)} file(s)..."):
                files = [("files", (f.name, f, f.type or "application/octet-stream")) for f in uploaded_files]
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/projects/{project_id}/documents",
                        files=files,
                        timeout=120
                    )
                    if response.ok:
                        render_success_message("Files uploaded successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to upload files: {response.text}")
                except Exception as e:
                    st.error(f"Upload error: {str(e)}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # Existing Documents
    st.markdown("### Uploaded Documents")

    docs_response = api_request("GET", f"/projects/{project_id}/documents", show_error=False)

    if docs_response and docs_response.get("documents"):
        docs = docs_response["documents"]
        st.markdown(f"**{len(docs)} document(s)** uploaded")
        st.markdown("<br>", unsafe_allow_html=True)

        for doc in docs:
            file_type = doc.get('file_type', 'unknown')
            icon = get_file_icon(file_type)
            status_class = "processed" if doc.get('processed') else "pending"
            status_text = "Processed" if doc.get('processed') else "Pending"

            st.markdown(f"""
            <div class="document-item">
                <span class="document-icon">{icon}</span>
                <span class="document-name">{doc.get('filename', 'Unknown file')}</span>
                <span class="document-meta">{file_type.upper()}</span>
                <span class="document-status {status_class}">{status_text}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        render_empty_state(
            "📄",
            "No Documents Yet",
            "Upload your first document to begin the analysis process."
        )


def render_analysis_tab(project_id: str):
    """Render the analysis tab with document analysis controls."""

    st.markdown("### Document Analysis")
    st.markdown("APIC will analyze your uploaded documents to identify potential process inefficiencies and generate targeted interview questions.")

    # Check for documents
    docs_response = api_request("GET", f"/projects/{project_id}/documents", show_error=False)
    has_docs = docs_response and len(docs_response.get("documents", [])) > 0

    if not has_docs:
        render_warning_message("Please upload documents before starting analysis. Go to the Documents tab to upload your process documentation.")
        return

    doc_count = len(docs_response["documents"])
    render_info_message(f"Ready to analyze {doc_count} document(s). This process may take a few minutes depending on the document size.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Analysis Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Analysis", use_container_width=True, type="primary"):
            with st.spinner("Analyzing documents and generating interview script... This may take a few minutes."):
                result = api_request(
                    "POST",
                    "/workflow/start",
                    json={"project_id": project_id},
                )

                if result:
                    render_success_message("Analysis complete! Interview script has been generated. Go to the Interview tab to view it.")
                    # Refresh project
                    updated = api_request("GET", f"/projects/{project_id}")
                    if updated:
                        st.session_state.current_project = updated
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # Show hypotheses and interview document download if available
    status_response = api_request("GET", f"/workflow/{project_id}/status", show_error=False)
    if status_response and status_response.get("current_node") not in ["not_started", None]:
        # Interview Document Download Section
        st.markdown("### AI-Generated Interview Document")
        st.markdown("The AI agent has analyzed your documents and generated a comprehensive interview script. Download it in your preferred format.")
        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            try:
                response = requests.get(
                    f"{API_BASE_URL}/workflow/{project_id}/interview-script/export/pdf",
                    timeout=30
                )
                if response.ok:
                    st.download_button(
                        label="📄 Download PDF",
                        data=response.content,
                        file_name=f"interview_script_{project_id}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="analysis_download_pdf"
                    )
                else:
                    st.button("📄 PDF Not Available", disabled=True, use_container_width=True, key="analysis_pdf_disabled")
            except Exception:
                st.button("📄 PDF Error", disabled=True, use_container_width=True, key="analysis_pdf_error")

        with col2:
            try:
                response = requests.get(
                    f"{API_BASE_URL}/workflow/{project_id}/interview-script/export/docx",
                    timeout=30
                )
                if response.ok:
                    st.download_button(
                        label="📝 Download Word",
                        data=response.content,
                        file_name=f"interview_script_{project_id}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key="analysis_download_docx"
                    )
                else:
                    st.button("📝 Word Not Available", disabled=True, use_container_width=True, key="analysis_docx_disabled")
            except Exception:
                st.button("📝 Word Error", disabled=True, use_container_width=True, key="analysis_docx_error")

        with col3:
            try:
                response = requests.get(
                    f"{API_BASE_URL}/workflow/{project_id}/interview-script/export/markdown",
                    timeout=30
                )
                if response.ok:
                    st.download_button(
                        label="📋 Download Markdown",
                        data=response.content,
                        file_name=f"interview_script_{project_id}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key="analysis_download_md"
                    )
                else:
                    st.button("📋 Markdown Not Available", disabled=True, use_container_width=True, key="analysis_md_disabled")
            except Exception:
                st.button("📋 Markdown Error", disabled=True, use_container_width=True, key="analysis_md_error")

        st.markdown("<br>", unsafe_allow_html=True)
        render_info_message("The interview document contains targeted questions based on identified hypotheses. Use it to conduct stakeholder interviews.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        # Generated Hypotheses Section
        hypo_response = api_request("GET", f"/workflow/{project_id}/hypotheses", show_error=False)
        if hypo_response and hypo_response.get("hypotheses"):
            st.markdown("### Generated Hypotheses")
            st.markdown("Based on document analysis, APIC has identified the following potential areas for improvement:")
            st.markdown("<br>", unsafe_allow_html=True)

            for hypo in hypo_response["hypotheses"]:
                confidence = hypo.get('confidence', 0)
                confidence_color = "#10b981" if confidence > 0.7 else "#f59e0b" if confidence > 0.4 else "#94a3b8"

                with st.expander(f"📌 {hypo.get('process_area', 'Unknown Area')} — {hypo.get('category', 'general').title()}", expanded=False):
                    st.markdown(f"**Description:** {hypo.get('description', 'No description')}")
                    st.markdown(f"**Confidence:** <span style='color: {confidence_color}; font-weight: 600;'>{confidence:.0%}</span>", unsafe_allow_html=True)

                    if hypo.get('evidence'):
                        st.markdown("**Supporting Evidence:**")
                        for e in hypo['evidence'][:5]:
                            st.markdown(f"• {e}")


def get_default_interview_script():
    """Return a default interview script with general process improvement questions."""
    return {
        "target_roles": ["Process Owner", "Team Lead", "End User", "Manager"],
        "target_departments": ["Operations", "General"],
        "estimated_duration_minutes": 45,
        "introduction": """Thank you for taking the time to participate in this process improvement interview.

The purpose of this conversation is to understand how current processes work in practice, identify any challenges or inefficiencies you may encounter, and gather your insights on potential improvements.

Your feedback is valuable and will help us identify opportunities to streamline operations, reduce manual work, and improve overall efficiency. There are no right or wrong answers - we're interested in your honest perspective and experience.

Please feel free to share specific examples where possible, as they help us better understand the context and impact of the issues you describe.""",
        "questions": [
            {
                "question": "Can you walk me through a typical day in your role? What are the main tasks you perform?",
                "role": "General",
                "intent": "Understand daily workflows and key responsibilities",
                "follow_ups": [
                    "Which tasks take the most time?",
                    "Are there any tasks that feel repetitive or could be automated?",
                    "How do these tasks connect to other team members' work?"
                ]
            },
            {
                "question": "What processes or workflows do you follow most frequently? Are these documented somewhere?",
                "role": "Process Owner",
                "intent": "Identify key processes and documentation gaps",
                "follow_ups": [
                    "How closely do you follow the documented procedures?",
                    "Are there any informal processes that aren't documented?",
                    "When was the last time these procedures were updated?"
                ]
            },
            {
                "question": "What are the biggest challenges or pain points you experience in your daily work?",
                "role": "End User",
                "intent": "Identify inefficiencies and frustration points",
                "follow_ups": [
                    "How often does this issue occur?",
                    "What is the impact when this happens?",
                    "Have you found any workarounds?"
                ]
            },
            {
                "question": "Are there any manual, repetitive tasks that you think could be automated or simplified?",
                "role": "General",
                "intent": "Discover automation opportunities",
                "follow_ups": [
                    "How much time do you spend on these tasks weekly?",
                    "What tools or systems are involved?",
                    "What would an ideal solution look like?"
                ]
            },
            {
                "question": "How do you communicate and collaborate with other teams or departments?",
                "role": "Team Lead",
                "intent": "Understand cross-functional interactions and handoffs",
                "follow_ups": [
                    "Are there any communication bottlenecks?",
                    "How is information typically shared?",
                    "What happens when there's a miscommunication?"
                ]
            },
            {
                "question": "What tools and systems do you use to complete your work? How well do they integrate with each other?",
                "role": "General",
                "intent": "Assess technology landscape and integration gaps",
                "follow_ups": [
                    "Do you ever have to enter the same data in multiple systems?",
                    "Are there any tools you wish you had?",
                    "What are the limitations of your current tools?"
                ]
            },
            {
                "question": "How do you handle exceptions or situations that fall outside the normal process?",
                "role": "Process Owner",
                "intent": "Identify edge cases and process flexibility",
                "follow_ups": [
                    "How often do exceptions occur?",
                    "Who has authority to approve exceptions?",
                    "How are exceptions documented or tracked?"
                ]
            },
            {
                "question": "How do you measure success in your role? What metrics or KPIs are you evaluated on?",
                "role": "Manager",
                "intent": "Understand performance measurement and alignment",
                "follow_ups": [
                    "How is performance data collected?",
                    "Are there any metrics you think should be tracked but aren't?",
                    "How often is performance reviewed?"
                ]
            },
            {
                "question": "If you could change one thing about how work gets done here, what would it be?",
                "role": "General",
                "intent": "Capture improvement ideas and priorities",
                "follow_ups": [
                    "What would be the impact of this change?",
                    "What obstacles might prevent this change?",
                    "Who would need to be involved to make it happen?"
                ]
            },
            {
                "question": "Have there been any recent changes to processes or systems? How did they go?",
                "role": "Team Lead",
                "intent": "Assess change management and adoption patterns",
                "follow_ups": [
                    "What worked well during the transition?",
                    "What could have been done better?",
                    "How was training handled?"
                ]
            }
        ],
        "discovery_questions": [
            {
                "question": "What do you think your customers (internal or external) value most about what you deliver?",
                "role": "General",
                "intent": "Understand customer value and priorities",
                "follow_ups": []
            },
            {
                "question": "Are there any compliance or regulatory requirements that affect how you work?",
                "role": "Manager",
                "intent": "Identify compliance constraints",
                "follow_ups": []
            },
            {
                "question": "Is there anything else you'd like to share that we haven't covered?",
                "role": "General",
                "intent": "Capture any additional insights",
                "follow_ups": []
            }
        ],
        "closing_notes": """Thank you for your time and valuable insights today. Your input will be instrumental in identifying opportunities for process improvement.

**Next Steps:**
- We will analyze the information gathered from all interviews
- Findings will be compiled into a comprehensive report
- Recommendations will be prioritized based on impact and feasibility
- You may be contacted for follow-up questions or clarification

If you think of anything else after our conversation, please don't hesitate to reach out. We appreciate your participation in this process improvement initiative.""",
        "customer_context": None,
        "diagnostic_leads": []
    }


def render_interview_tab(project_id: str):
    """Render the interview script tab."""

    script_response = api_request("GET", f"/workflow/{project_id}/interview-script", show_error=False)

    # Check if we have an AI-generated script or should use the default
    has_ai_script = script_response and script_response.get("interview_script")

    if has_ai_script:
        script = script_response["interview_script"]
        script_type = "ai_generated"
    else:
        script = get_default_interview_script()
        script_type = "default"

    # Header Section
    st.markdown("### Interview Script")

    # Show appropriate message based on script type
    if script_type == "default":
        render_info_message(
            "This is a default interview script with general process improvement questions. "
            "Run the document analysis in the Analysis tab to generate a customized AI-powered interview script "
            "tailored to your specific documents and identified hypotheses."
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("Use this script as a starting point for stakeholder interviews.")
    else:
        render_success_message(
            "AI-Generated Script: This interview script has been customized based on the analysis "
            "of your uploaded documents and identified improvement opportunities."
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("Use this script to conduct stakeholder interviews. Download in your preferred format for offline use.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Script Overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Estimated Duration", f"{script.get('estimated_duration_minutes', 60)} min")
    with col2:
        roles = script.get('target_roles', [])
        st.metric("Target Roles", len(roles))
    with col3:
        questions = script.get('questions', [])
        st.metric("Questions", len(questions))

    st.markdown("<br>", unsafe_allow_html=True)

    # Download Section - Only show for AI-generated scripts
    if script_type == "ai_generated":
        st.markdown("#### Download Script")
        col1, col2, col3 = st.columns(3)

        with col1:
            try:
                response = requests.get(
                    f"{API_BASE_URL}/workflow/{project_id}/interview-script/export/pdf",
                    timeout=30
                )
                if response.ok:
                    st.download_button(
                        label="Download PDF",
                        data=response.content,
                        file_name=f"interview_script_{project_id}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="interview_download_pdf"
                    )
                else:
                    st.button("PDF Not Available", disabled=True, use_container_width=True, key="interview_pdf_disabled")
            except Exception:
                st.button("PDF Error", disabled=True, use_container_width=True, key="interview_pdf_error")

        with col2:
            try:
                response = requests.get(
                    f"{API_BASE_URL}/workflow/{project_id}/interview-script/export/docx",
                    timeout=30
                )
                if response.ok:
                    st.download_button(
                        label="Download Word",
                        data=response.content,
                        file_name=f"interview_script_{project_id}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key="interview_download_docx"
                    )
                else:
                    st.button("Word Not Available", disabled=True, use_container_width=True, key="interview_docx_disabled")
            except Exception:
                st.button("Word Error", disabled=True, use_container_width=True, key="interview_docx_error")

        with col3:
            try:
                response = requests.get(
                    f"{API_BASE_URL}/workflow/{project_id}/interview-script/export/markdown",
                    timeout=30
                )
                if response.ok:
                    st.download_button(
                        label="Download Markdown",
                        data=response.content,
                        file_name=f"interview_script_{project_id}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key="interview_download_md"
                    )
                else:
                    st.button("Markdown Not Available", disabled=True, use_container_width=True, key="interview_md_disabled")
            except Exception:
                st.button("Markdown Error", disabled=True, use_container_width=True, key="interview_md_error")

        st.markdown("<br>", unsafe_allow_html=True)

    st.divider()

    # Script Content
    st.markdown("#### 📖 Script Preview")

    # Target Roles
    if script.get("target_roles"):
        st.markdown(f"**Target Roles:** {', '.join(script['target_roles'])}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Introduction
    with st.expander("📢 Introduction", expanded=True):
        st.markdown(script.get("introduction", "No introduction provided."))

    # Questions
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### Interview Questions")

    questions = script.get("questions", [])
    for i, q in enumerate(questions, 1):
        role = q.get('role', 'General')

        st.markdown(f"""
        <div class="question-card">
            <div class="question-number">Question {i}</div>
            <div class="question-role">{role}</div>
            <div class="question-text">{q.get('question', 'No question')}</div>
            <div class="question-intent">💡 Intent: {q.get('intent', 'Gather information')}</div>
        """, unsafe_allow_html=True)

        if q.get("follow_ups"):
            st.markdown('<div style="margin-top: 0.5rem; font-size: 0.875rem; font-weight: 500;">Follow-up Questions:</div>', unsafe_allow_html=True)
            for fu in q["follow_ups"]:
                st.markdown(f"<div style='font-size: 0.875rem; color: #64748b; margin-left: 1rem;'>• {fu}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Discovery Questions (if available)
    discovery_questions = script.get("discovery_questions", [])
    if discovery_questions:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Discovery Questions")
        st.markdown("*Additional open-ended questions to uncover new insights:*")

        for i, q in enumerate(discovery_questions, 1):
            role = q.get('role', 'General')

            st.markdown(f"""
            <div class="question-card" style="border-left-color: #10b981;">
                <div class="question-number" style="color: #10b981;">Discovery {i}</div>
                <div class="question-role">{role}</div>
                <div class="question-text">{q.get('question', 'No question')}</div>
                <div class="question-intent">💡 Intent: {q.get('intent', 'Gather information')}</div>
            </div>
            """, unsafe_allow_html=True)

    # Closing Notes
    if script.get("closing_notes"):
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("Closing Notes", expanded=False):
            st.markdown(script["closing_notes"])

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # Transcript Submission
    st.markdown("### Submit Interview Transcript")
    st.markdown("After conducting the interview, paste the transcript or notes below to generate recommendations.")

    # Show warning if using default script
    if script_type == "default":
        render_warning_message(
            "Note: You are using the default interview script. For best results, run document analysis first "
            "to generate a customized script. You can still submit a transcript, but recommendations will be "
            "based on general process improvement patterns rather than your specific documents."
        )
        st.markdown("<br>", unsafe_allow_html=True)

    transcript = st.text_area(
        "Interview Transcript",
        height=250,
        placeholder="Paste your interview notes or transcript here...\n\nInclude:\n• Responses to each question\n• Any additional insights shared\n• Pain points mentioned\n• Current workarounds described",
        help="The more detailed your notes, the better the recommendations will be."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Submit & Generate Recommendations", use_container_width=True, type="primary"):
            if not transcript or not transcript.strip():
                st.error("Please enter the interview transcript before submitting.")
            elif len(transcript.strip()) < 100:
                st.warning("The transcript seems very short. Consider adding more detail for better recommendations.")
            else:
                with st.spinner("Processing transcript and generating recommendations... This may take a few minutes."):
                    result = api_request(
                        "POST",
                        "/workflow/resume",
                        json={
                            "project_id": project_id,
                            "transcript": transcript.strip(),
                        },
                    )

                    if result:
                        render_success_message("Analysis complete! Check the Results tab to view recommendations.")
                        updated = api_request("GET", f"/projects/{project_id}")
                        if updated:
                            st.session_state.current_project = updated
                        st.rerun()


def render_results_tab(project_id: str):
    """Render the results tab with gap analysis and solutions."""

    # Gap Analysis Section
    gaps_response = api_request("GET", f"/workflow/{project_id}/gaps", show_error=False)
    solutions_response = api_request("GET", f"/workflow/{project_id}/solutions", show_error=False)

    has_gaps = gaps_response and gaps_response.get("gap_analyses")
    has_solutions = solutions_response and solutions_response.get("solutions")

    if not has_gaps and not has_solutions:
        render_empty_state(
            "📊",
            "Results Not Available Yet",
            "Complete the interview process to generate gap analysis and recommendations. Go to the Interview tab to submit your transcript."
        )
        return

    # Gap Analysis
    if has_gaps:
        st.markdown("### Gap Analysis")
        st.markdown("Identified discrepancies between documented processes and actual practices:")
        st.markdown("<br>", unsafe_allow_html=True)

        for gap in gaps_response["gap_analyses"]:
            st.markdown(f"""
            <div class="analysis-card">
                <div class="analysis-card-header">
                    <span class="analysis-card-title">📍 {gap.get('process_step', 'Unknown Step')}</span>
                </div>
                <div style="display: grid; gap: 0.75rem;">
                    <div><strong>📋 SOP Says:</strong> {gap.get('sop_description', 'N/A')}</div>
                    <div><strong>👁️ Observed:</strong> {gap.get('observed_behavior', 'N/A')}</div>
                    <div><strong>⚠️ Gap:</strong> {gap.get('gap_description', 'N/A')}</div>
                    <div><strong>💥 Impact:</strong> {gap.get('impact', 'N/A')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Solutions
    if has_solutions:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Recommended Solutions")
        st.markdown("Actionable recommendations with estimated ROI:")
        st.markdown("<br>", unsafe_allow_html=True)

        for sol in solutions_response["solutions"]:
            severity = sol.get('pain_point_severity', 'medium').lower()
            priority_class = "priority-high" if severity == "high" else "priority-medium" if severity == "medium" else "priority-low"

            tech_stack = sol.get('tech_stack_recommendation', [])
            tech_text = ', '.join(tech_stack) if tech_stack else 'N/A'

            st.markdown(f"""
            <div class="analysis-card">
                <div class="analysis-card-header">
                    <span class="analysis-card-title">💡 {sol.get('process_step', 'Unknown')}</span>
                    <span class="priority-badge {priority_class}">{severity} priority</span>
                </div>
                <div style="display: grid; gap: 0.75rem;">
                    <div><strong>🔧 Solution:</strong> {sol.get('proposed_solution', 'N/A')}</div>
                    <div><strong>🛠️ Tech Stack:</strong> {tech_text}</div>
                    <div><strong>📈 ROI:</strong> {sol.get('estimated_roi_hours', 0)} hours/month saved</div>
                    <div><strong>⚙️ Complexity:</strong> {sol.get('implementation_complexity', 'N/A')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_report_tab(project_id: str):
    """Render the final report tab."""

    report_response = api_request("GET", f"/workflow/{project_id}/report", show_error=False)

    if not report_response or not report_response.get("report"):
        render_empty_state(
            "📋",
            "Report Not Generated Yet",
            "The final report will be available after completing the full workflow including document analysis and interview submission."
        )
        return

    report = report_response["report"]

    st.markdown("### Executive Summary")

    # Executive Summary
    if report.get("executive_summary"):
        summary = report["executive_summary"]

        st.markdown(f"""
        <div class="report-summary">
            <div style="margin-bottom: 1rem;">{summary.get('overview', 'No overview available.')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Key Metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            savings = summary.get('total_potential_savings', 0)
            st.markdown(f"""
            <div class="report-metric">
                <div class="report-metric-value">${savings:,.0f}</div>
                <div class="report-metric-label">Potential Annual Savings</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            cost = summary.get('total_implementation_cost', 0)
            st.markdown(f"""
            <div class="report-metric">
                <div class="report-metric-value">${cost:,.0f}</div>
                <div class="report-metric-label">Implementation Cost</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            roi = summary.get('overall_roi_percentage', 0)
            st.markdown(f"""
            <div class="report-metric">
                <div class="report-metric-value">{roi:.1f}%</div>
                <div class="report-metric-label">Projected ROI</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Download PDF
    if report_response.get("report_pdf_path"):
        st.markdown("### Download Report")

        pdf_path = report_response["report_pdf_path"]

        # Try to fetch and provide download
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                # Attempt to read the PDF file if it's accessible
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Full Report (PDF)",
                            data=f.read(),
                            file_name=f"APIC_Report_{project_id}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            type="primary"
                        )
                else:
                    render_info_message(f"Report generated at: {pdf_path}")
            except Exception:
                render_info_message(f"Report available at: {pdf_path}")


# ============================================================================
# Main App Logic
# ============================================================================

def main():
    """Main application entry point."""
    page = st.session_state.page

    if page == "home":
        page_home()
    elif page == "new_project":
        page_new_project()
    elif page == "projects":
        page_projects()
    elif page == "project_detail":
        page_project_detail()
    else:
        page_home()


if __name__ == "__main__":
    main()
