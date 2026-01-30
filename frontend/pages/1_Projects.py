"""
Projects listing page for APIC.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from styles import apply_styles
from utils import api_request, format_datetime
from components import (
    display_status_badge,
    render_empty_state,
    render_page_header,
)

st.set_page_config(
    page_title="Projects - APIC",
    page_icon="O",
    layout="wide",
)

apply_styles()


def main():
    """Render the project listing page."""
    render_page_header(
        "All Projects",
        "View and manage your consulting projects."
    )

    # Action Bar
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("+ New Project", use_container_width=True, type="primary"):
            st.switch_page("pages/2_New_Project.py")

    st.markdown("<br>", unsafe_allow_html=True)

    # Fetch Projects
    projects = api_request("GET", "/projects")

    if not projects or len(projects) == 0:
        if render_empty_state(
            "[Empty]",
            "No Projects Yet",
            "Create your first project to get started with process improvement analysis.",
            show_button=True,
            button_label="Create First Project",
            button_key="empty_create_project"
        ):
            st.switch_page("pages/2_New_Project.py")
        return

    # Project List
    for project in projects:
        with st.container():
            col1, col2, col3, col4 = st.columns([2.5, 1.5, 1, 1])

            with col1:
                st.markdown(f"""
                <div class="project-name">{project.get('project_name', 'Unnamed Project')}</div>
                <div class="project-client">{project.get('client_name', 'No client specified')}</div>
                """, unsafe_allow_html=True)

            with col2:
                display_status_badge(project.get('status', 'unknown'))
                st.markdown(f'<div class="project-meta">{format_datetime(project.get("created_at", ""))}</div>', unsafe_allow_html=True)

            with col3:
                docs = project.get('documents', [])
                if docs:
                    st.markdown(f'<div class="project-meta">{len(docs)} docs</div>', unsafe_allow_html=True)

            with col4:
                if st.button("Open ->", key=f"open_{project['id']}", use_container_width=True):
                    full_project = api_request("GET", f"/projects/{project['id']}")
                    if full_project:
                        st.session_state.current_project = full_project
                        st.switch_page("pages/3_Project.py")

            st.divider()


if __name__ == "__main__":
    main()
