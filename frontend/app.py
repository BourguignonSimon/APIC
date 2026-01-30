"""
APIC Streamlit Frontend - Home Page
Agentic Process Improvement Consultant
"""

import streamlit as st

from styles import apply_styles
from utils import api_request
from components import (
    display_status_badge,
    render_page_header,
    render_section_title,
    render_metric_card,
    render_feature_card,
)

# Page Configuration
st.set_page_config(
    page_title="APIC - Process Improvement Consultant",
    page_icon="O",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply styles
apply_styles()

# Initialize session state
if "current_project_id" not in st.session_state:
    st.session_state.current_project_id = None
if "show_success" not in st.session_state:
    st.session_state.show_success = None

# Sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-brand">APIC</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">Agentic Process Improvement Consultant</div>', unsafe_allow_html=True)

    st.divider()

    # Help Section
    st.markdown('<div class="sidebar-section-title">Help</div>', unsafe_allow_html=True)
    with st.expander("How to Use APIC"):
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


def main():
    """Render the home page with welcome message and quick stats."""
    # Header
    render_page_header(
        "Welcome to APIC",
        "Your AI-Powered Process Improvement Consultant. Analyze processes, identify gaps, and get actionable recommendations."
    )

    # Quick Actions
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("+ Create New Project", use_container_width=True, type="primary"):
            st.switch_page("pages/2_New_Project.py")
    with col2:
        if st.button("View All Projects", use_container_width=True):
            st.switch_page("pages/1_Projects.py")
    with col3:
        pass  # Placeholder for symmetry

    st.markdown("<br>", unsafe_allow_html=True)

    # How It Works Section
    render_section_title("How It Works")

    col1, col2, col3 = st.columns(3)

    with col1:
        render_feature_card(
            "[1]",
            "Upload Documents",
            "Upload your process documentation including SOPs, workflows, policy documents, and training materials. Supported formats: PDF, Word, PowerPoint, Excel, and text files."
        )

    with col2:
        render_feature_card(
            "[2]",
            "AI-Powered Analysis",
            "APIC analyzes your documents to identify potential inefficiencies and generates a customized interview script with targeted questions for key stakeholders."
        )

    with col3:
        render_feature_card(
            "[3]",
            "Get Recommendations",
            "After the interview, receive comprehensive gap analysis, automation recommendations with technology suggestions, and ROI estimates for each improvement."
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Project Statistics
    projects = api_request("GET", "/projects", show_error=False)

    if projects and len(projects) > 0:
        render_section_title("Project Overview")

        total = len(projects)
        completed = len([p for p in projects if p.get("status") == "completed"])
        interview_ready = len([p for p in projects if p.get("status") == "interview_ready"])
        new_projects = len([p for p in projects if p.get("status") == "created"])

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            render_metric_card(str(total), "Total Projects", "primary")
        with col2:
            render_metric_card(str(completed), "Completed", "success")
        with col3:
            render_metric_card(str(interview_ready), "Awaiting Interview", "warning")
        with col4:
            render_metric_card(str(new_projects), "New", "secondary")

        # Recent Projects
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="subsection-title">Recent Projects</div>', unsafe_allow_html=True)

        for project in projects[:3]:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{project.get('project_name', 'Unnamed')}** - {project.get('client_name', 'N/A')}")
            with col2:
                display_status_badge(project.get('status', 'unknown'))
            with col3:
                if st.button("Open", key=f"home_open_{project['id']}"):
                    st.session_state.current_project_id = project['id']
                    st.switch_page("pages/3_Project.py")


if __name__ == "__main__":
    main()
