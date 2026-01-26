"""
APIC Streamlit Frontend
MVP user interface for the Agentic Process Improvement Consultant.
"""

import os
import sys
import json
import requests
from datetime import datetime

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
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        font-weight: 500;
    }
    .status-created { background-color: #e3f2fd; color: #1565c0; }
    .status-interview_ready { background-color: #fff3e0; color: #e65100; }
    .status-completed { background-color: #e8f5e9; color: #2e7d32; }
    .status-failed { background-color: #ffebee; color: #c62828; }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Helper Functions
# ============================================================================

def api_request(method: str, endpoint: str, **kwargs) -> dict:
    """Make API request with error handling."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None


def format_datetime(dt_str: str) -> str:
    """Format datetime string for display."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except Exception:
        return dt_str


def display_status_badge(status: str):
    """Display status badge with appropriate styling."""
    status_colors = {
        "created": "status-created",
        "interview_ready": "status-interview_ready",
        "completed": "status-completed",
        "failed": "status-failed",
    }
    css_class = status_colors.get(status, "status-created")
    st.markdown(
        f'<span class="status-badge {css_class}">{status.replace("_", " ").title()}</span>',
        unsafe_allow_html=True
    )


# ============================================================================
# Session State Initialization
# ============================================================================

if "current_project" not in st.session_state:
    st.session_state.current_project = None
if "page" not in st.session_state:
    st.session_state.page = "home"


# ============================================================================
# Sidebar Navigation
# ============================================================================

with st.sidebar:
    st.markdown("## APIC")
    st.markdown("*Agentic Process Improvement Consultant*")
    st.divider()

    # Navigation
    st.markdown("### Navigation")

    if st.button("Home", use_container_width=True):
        st.session_state.page = "home"
        st.session_state.current_project = None

    if st.button("New Project", use_container_width=True):
        st.session_state.page = "new_project"

    if st.button("All Projects", use_container_width=True):
        st.session_state.page = "projects"

    st.divider()

    # Current Project Info
    if st.session_state.current_project:
        st.markdown("### Current Project")
        st.markdown(f"**{st.session_state.current_project.get('project_name', 'N/A')}**")
        st.markdown(f"Client: {st.session_state.current_project.get('client_name', 'N/A')}")
        display_status_badge(st.session_state.current_project.get('status', 'unknown'))


# ============================================================================
# Page: Home
# ============================================================================

def page_home():
    st.markdown('<p class="main-header">Welcome to APIC</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Your AI-Powered Process Improvement Consultant</p>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Step 1: Upload Documents")
        st.markdown("""
        Upload your process documentation:
        - Standard Operating Procedures (SOPs)
        - Process flow diagrams
        - Policy documents
        - Training materials
        """)

    with col2:
        st.markdown("### Step 2: Review Interview Script")
        st.markdown("""
        APIC will analyze your documents and generate:
        - Hypotheses about inefficiencies
        - Targeted interview questions
        - Role-specific question sets
        """)

    with col3:
        st.markdown("### Step 3: Get Recommendations")
        st.markdown("""
        After the interview, receive:
        - Gap analysis report
        - Automation recommendations
        - ROI estimates
        - Implementation roadmap
        """)

    st.divider()

    # Quick Stats
    projects = api_request("GET", "/projects")
    if projects:
        col1, col2, col3, col4 = st.columns(4)

        total = len(projects)
        completed = len([p for p in projects if p.get("status") == "completed"])
        in_progress = len([p for p in projects if p.get("status") == "interview_ready"])
        created = len([p for p in projects if p.get("status") == "created"])

        col1.metric("Total Projects", total)
        col2.metric("Completed", completed)
        col3.metric("Awaiting Interview", in_progress)
        col4.metric("New", created)


# ============================================================================
# Page: New Project
# ============================================================================

def page_new_project():
    st.markdown("## Create New Project")

    with st.form("new_project_form"):
        client_name = st.text_input("Client Name *", placeholder="Acme Corporation")
        project_name = st.text_input("Project Name *", placeholder="Q1 Process Optimization")
        description = st.text_area(
            "Description",
            placeholder="Brief description of the consulting engagement..."
        )
        departments = st.text_input(
            "Target Departments",
            placeholder="Finance, Operations, HR (comma-separated)"
        )

        submitted = st.form_submit_button("Create Project", use_container_width=True)

        if submitted:
            if not client_name or not project_name:
                st.error("Client name and project name are required.")
            else:
                dept_list = [d.strip() for d in departments.split(",") if d.strip()]

                result = api_request(
                    "POST",
                    "/projects",
                    json={
                        "client_name": client_name,
                        "project_name": project_name,
                        "description": description,
                        "target_departments": dept_list,
                    }
                )

                if result:
                    st.success(f"Project created successfully!")
                    st.session_state.current_project = result
                    st.session_state.page = "project_detail"
                    st.rerun()


# ============================================================================
# Page: Project List
# ============================================================================

def page_projects():
    st.markdown("## All Projects")

    projects = api_request("GET", "/projects")

    if not projects:
        st.info("No projects found. Create your first project to get started!")
        return

    for project in projects:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.markdown(f"### {project.get('project_name', 'Unnamed')}")
                st.markdown(f"**Client:** {project.get('client_name', 'N/A')}")

            with col2:
                display_status_badge(project.get('status', 'unknown'))
                st.caption(f"Created: {format_datetime(project.get('created_at', ''))}")

            with col3:
                if st.button("Open", key=f"open_{project['id']}"):
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
    project = st.session_state.current_project

    if not project:
        st.error("No project selected.")
        return

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"## {project.get('project_name', 'Project')}")
        st.markdown(f"**Client:** {project.get('client_name', 'N/A')}")
    with col2:
        display_status_badge(project.get('status', 'unknown'))

    st.divider()

    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Documents", "Analysis", "Interview", "Results", "Report"
    ])

    project_id = project.get('id')

    # Documents Tab
    with tab1:
        st.markdown("### Upload Documents")

        uploaded_files = st.file_uploader(
            "Upload SOPs, process documents, etc.",
            type=["pdf", "docx", "doc", "txt", "pptx", "xlsx"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            if st.button("Upload Files"):
                files = [("files", (f.name, f, f.type)) for f in uploaded_files]
                response = requests.post(
                    f"{API_BASE_URL}/projects/{project_id}/documents",
                    files=files,
                )
                if response.ok:
                    st.success("Files uploaded successfully!")
                    st.rerun()
                else:
                    st.error("Failed to upload files.")

        # List existing documents
        st.markdown("### Uploaded Documents")
        docs_response = api_request("GET", f"/projects/{project_id}/documents")

        if docs_response and docs_response.get("documents"):
            for doc in docs_response["documents"]:
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.markdown(f"**{doc.get('filename', 'Unknown')}**")
                col2.markdown(f"Type: {doc.get('file_type', 'N/A').upper()}")
                col3.markdown(f"{'Processed' if doc.get('processed') else 'Pending'}")
        else:
            st.info("No documents uploaded yet.")

    # Analysis Tab
    with tab2:
        st.markdown("### Start Analysis")

        docs_response = api_request("GET", f"/projects/{project_id}/documents")
        has_docs = docs_response and len(docs_response.get("documents", [])) > 0

        if not has_docs:
            st.warning("Please upload documents before starting analysis.")
        else:
            st.markdown(f"**{len(docs_response['documents'])} documents** ready for analysis.")

            if st.button("Start Analysis", disabled=not has_docs, use_container_width=True):
                with st.spinner("Analyzing documents and generating interview script..."):
                    result = api_request(
                        "POST",
                        "/workflow/start",
                        json={"project_id": project_id},
                    )

                    if result:
                        st.success("Analysis complete! Interview script generated.")
                        # Refresh project
                        updated = api_request("GET", f"/projects/{project_id}")
                        if updated:
                            st.session_state.current_project = updated
                        st.rerun()

        # Show hypotheses if available
        status_response = api_request("GET", f"/workflow/{project_id}/status")
        if status_response and status_response.get("current_node") != "not_started":
            hypo_response = api_request("GET", f"/workflow/{project_id}/hypotheses")
            if hypo_response and hypo_response.get("hypotheses"):
                st.markdown("### Generated Hypotheses")
                for hypo in hypo_response["hypotheses"]:
                    with st.expander(f"{hypo.get('process_area', 'Unknown')} - {hypo.get('category', 'general')}"):
                        st.markdown(hypo.get('description', ''))
                        st.markdown(f"**Confidence:** {hypo.get('confidence', 0):.0%}")
                        if hypo.get('evidence'):
                            st.markdown("**Evidence:**")
                            for e in hypo['evidence'][:3]:
                                st.markdown(f"- {e}")

    # Interview Tab
    with tab3:
        st.markdown("### Interview Script")

        script_response = api_request("GET", f"/workflow/{project_id}/interview-script")

        if script_response and script_response.get("interview_script"):
            script = script_response["interview_script"]

            # Download buttons section
            st.markdown("#### Download Interview Script")
            st.markdown("Export the interview script to use during customer interviews:")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Download PDF", key="download_pdf", use_container_width=True):
                    try:
                        response = requests.get(
                            f"{API_BASE_URL}/workflow/{project_id}/interview-script/export/pdf"
                        )
                        if response.ok:
                            st.download_button(
                                label="Save PDF File",
                                data=response.content,
                                file_name=f"interview_script_{project_id}.pdf",
                                mime="application/pdf",
                                key="save_pdf"
                            )
                        else:
                            st.error("Failed to download PDF")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

            with col2:
                if st.button("Download Word", key="download_docx", use_container_width=True):
                    try:
                        response = requests.get(
                            f"{API_BASE_URL}/workflow/{project_id}/interview-script/export/docx"
                        )
                        if response.ok:
                            st.download_button(
                                label="Save Word File",
                                data=response.content,
                                file_name=f"interview_script_{project_id}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key="save_docx"
                            )
                        else:
                            st.error("Failed to download Word document")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

            with col3:
                if st.button("Download Markdown", key="download_md", use_container_width=True):
                    try:
                        response = requests.get(
                            f"{API_BASE_URL}/workflow/{project_id}/interview-script/export/markdown"
                        )
                        if response.ok:
                            st.download_button(
                                label="Save Markdown File",
                                data=response.content,
                                file_name=f"interview_script_{project_id}.md",
                                mime="text/markdown",
                                key="save_md"
                            )
                        else:
                            st.error("Failed to download Markdown")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

            # Show available files info
            script_files = script_response.get("script_files")
            if script_files:
                with st.expander("Available Script Files"):
                    for format_name, file_path in script_files.items():
                        if file_path:
                            st.markdown(f"- **{format_name.upper()}**: `{file_path}`")

            st.divider()

            st.info(f"Estimated duration: {script.get('estimated_duration_minutes', 60)} minutes")
            st.markdown(f"**Target Roles:** {', '.join(script.get('target_roles', []))}")

            st.markdown("#### Introduction")
            st.markdown(script.get("introduction", ""))

            st.markdown("#### Questions")
            for i, q in enumerate(script.get("questions", []), 1):
                with st.expander(f"Q{i}: {q.get('role', 'General')}"):
                    st.markdown(f"**Question:** {q.get('question', '')}")
                    st.markdown(f"**Intent:** {q.get('intent', '')}")
                    if q.get("follow_ups"):
                        st.markdown("**Follow-ups:**")
                        for fu in q["follow_ups"]:
                            st.markdown(f"- {fu}")

            st.markdown("#### Closing Notes")
            st.markdown(script.get("closing_notes", ""))

            # Transcript submission
            st.divider()
            st.markdown("### Submit Interview Transcript")

            transcript = st.text_area(
                "Paste the interview transcript here",
                height=300,
                placeholder="Enter the interview notes or transcript..."
            )

            if st.button("Submit Transcript and Continue", use_container_width=True):
                if not transcript:
                    st.error("Please enter the interview transcript.")
                else:
                    with st.spinner("Processing transcript and generating recommendations..."):
                        result = api_request(
                            "POST",
                            "/workflow/resume",
                            json={
                                "project_id": project_id,
                                "transcript": transcript,
                            },
                        )

                        if result:
                            st.success("Analysis complete! Check the Results tab.")
                            updated = api_request("GET", f"/projects/{project_id}")
                            if updated:
                                st.session_state.current_project = updated
                            st.rerun()
        else:
            st.info("Interview script not yet generated. Start analysis first.")

    # Results Tab
    with tab4:
        st.markdown("### Analysis Results")

        # Gap Analysis
        gaps_response = api_request("GET", f"/workflow/{project_id}/gaps")
        if gaps_response and gaps_response.get("gap_analyses"):
            st.markdown("#### Gap Analysis")
            for gap in gaps_response["gap_analyses"]:
                with st.expander(f"{gap.get('process_step', 'Unknown')}"):
                    st.markdown(f"**SOP says:** {gap.get('sop_description', 'N/A')}")
                    st.markdown(f"**Actually:** {gap.get('observed_behavior', 'N/A')}")
                    st.markdown(f"**Gap:** {gap.get('gap_description', 'N/A')}")
                    st.markdown(f"**Impact:** {gap.get('impact', 'N/A')}")

        # Solutions
        solutions_response = api_request("GET", f"/workflow/{project_id}/solutions")
        if solutions_response and solutions_response.get("solutions"):
            st.markdown("#### Recommended Solutions")
            for sol in solutions_response["solutions"]:
                with st.expander(f"{sol.get('process_step', 'Unknown')} - {sol.get('pain_point_severity', 'N/A')} Priority"):
                    st.markdown(f"**Solution:** {sol.get('proposed_solution', 'N/A')}")
                    st.markdown(f"**Tech Stack:** {', '.join(sol.get('tech_stack_recommendation', []))}")
                    st.markdown(f"**ROI:** {sol.get('estimated_roi_hours', 0)} hours/month saved")
                    st.markdown(f"**Complexity:** {sol.get('implementation_complexity', 'N/A')}")

        if not gaps_response or not gaps_response.get("gap_analyses"):
            st.info("Results not yet available. Complete the interview process first.")

    # Report Tab
    with tab5:
        st.markdown("### Final Report")

        report_response = api_request("GET", f"/workflow/{project_id}/report")

        if report_response and report_response.get("report"):
            report = report_response["report"]

            # Executive Summary
            if report.get("executive_summary"):
                summary = report["executive_summary"]
                st.markdown("#### Executive Summary")
                st.markdown(summary.get("overview", ""))

                col1, col2, col3 = st.columns(3)
                col1.metric(
                    "Potential Annual Savings",
                    f"${summary.get('total_potential_savings', 0):,.0f}"
                )
                col2.metric(
                    "Implementation Cost",
                    f"${summary.get('total_implementation_cost', 0):,.0f}"
                )
                col3.metric(
                    "Projected ROI",
                    f"{summary.get('overall_roi_percentage', 0):.1f}%"
                )

            # Download PDF
            if report_response.get("report_pdf_path"):
                st.markdown("#### Download Report")
                pdf_path = report_response["report_pdf_path"]
                st.markdown(f"PDF available at: `{pdf_path}`")
                # Note: In production, serve this via the API
        else:
            st.info("Report not yet generated. Complete the full workflow first.")


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
