"""
New Project creation page for APIC.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from styles import apply_styles
from utils import api_request
from components import render_page_header

st.set_page_config(
    page_title="New Project - APIC",
    page_icon="O",
    layout="wide",
)

apply_styles()


def main():
    """Render the new project creation page."""
    render_page_header(
        "Create New Project",
        "Set up a new consulting engagement. You can add documents after creating the project."
    )

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
                    st.session_state.show_success = "Project created successfully! Now upload your documents to get started."
                    st.switch_page("pages/3_Project.py")

    st.markdown('</div>', unsafe_allow_html=True)

    # Back Button
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("<- Back to Home", use_container_width=True):
            st.switch_page("app.py")


if __name__ == "__main__":
    main()
