"""
Project detail page with tabs for APIC.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import streamlit as st

from config import API_BASE_URL
from styles import apply_styles
from utils import api_request, format_datetime, get_file_icon
from components import (
    display_status_badge,
    render_empty_state,
    render_info_message,
    render_success_message,
    render_warning_message,
)

st.set_page_config(
    page_title="Project - APIC",
    page_icon="O",
    layout="wide",
)

apply_styles()

# Initialize session state
if "current_project_id" not in st.session_state:
    st.session_state.current_project_id = None
if "show_success" not in st.session_state:
    st.session_state.show_success = None


def get_default_interview_script():
    """Return a default interview script with general process improvement questions."""
    return {
        "target_roles": ["Process Owner", "Team Lead", "End User", "Manager"],
        "target_departments": ["Operations", "General"],
        "estimated_duration_minutes": 45,
        "introduction": """Thank you for taking the time to participate in this process improvement interview.

The purpose of this conversation is to understand how current processes work in practice, identify any challenges or inefficiencies you may encounter, and gather your insights on potential improvements.

Your feedback is valuable and will help us identify opportunities to streamline operations, reduce manual work, and improve overall efficiency. There are no right or wrong answers - we're interested in your honest perspective and experience.""",
        "questions": [
            {"question": "Can you walk me through a typical day in your role? What are the main tasks you perform?", "role": "General", "intent": "Understand daily workflows and key responsibilities", "follow_ups": ["Which tasks take the most time?", "Are there any tasks that feel repetitive or could be automated?"]},
            {"question": "What processes or workflows do you follow most frequently? Are these documented somewhere?", "role": "Process Owner", "intent": "Identify key processes and documentation gaps", "follow_ups": ["How closely do you follow the documented procedures?", "When was the last time these procedures were updated?"]},
            {"question": "What are the biggest challenges or pain points you experience in your daily work?", "role": "End User", "intent": "Identify inefficiencies and frustration points", "follow_ups": ["How often does this issue occur?", "What is the impact when this happens?"]},
            {"question": "Are there any manual, repetitive tasks that you think could be automated or simplified?", "role": "General", "intent": "Discover automation opportunities", "follow_ups": ["How much time do you spend on these tasks weekly?", "What tools or systems are involved?"]},
            {"question": "How do you communicate and collaborate with other teams or departments?", "role": "Team Lead", "intent": "Understand cross-functional interactions and handoffs", "follow_ups": ["Are there any communication bottlenecks?", "How is information typically shared?"]},
            {"question": "What tools and systems do you use to complete your work? How well do they integrate with each other?", "role": "General", "intent": "Assess technology landscape and integration gaps", "follow_ups": ["Do you ever have to enter the same data in multiple systems?", "Are there any tools you wish you had?"]},
            {"question": "If you could change one thing about how work gets done here, what would it be?", "role": "General", "intent": "Capture improvement ideas and priorities", "follow_ups": ["What would be the impact of this change?", "What obstacles might prevent this change?"]},
        ],
        "discovery_questions": [
            {"question": "What do you think your customers (internal or external) value most about what you deliver?", "role": "General", "intent": "Understand customer value and priorities", "follow_ups": []},
            {"question": "Is there anything else you'd like to share that we haven't covered?", "role": "General", "intent": "Capture any additional insights", "follow_ups": []},
        ],
        "closing_notes": """Thank you for your time and valuable insights today. Your input will be instrumental in identifying opportunities for process improvement.

Next Steps:
- We will analyze the information gathered from all interviews
- Findings will be compiled into a comprehensive report
- Recommendations will be prioritized based on impact and feasibility""",
    }


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
            st.markdown(f"- {f.name} ({f.size / 1024:.1f} KB)")

        if st.button("Upload Files", use_container_width=True, type="primary"):
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

    st.divider()

    # Existing Documents
    st.markdown("### Uploaded Documents")

    docs_response = api_request("GET", f"/projects/{project_id}/documents", show_error=False)

    if docs_response and docs_response.get("documents"):
        docs = docs_response["documents"]
        st.markdown(f"**{len(docs)} document(s)** uploaded")

        for doc in docs:
            file_type = doc.get('file_type', 'unknown')
            source_type = doc.get('source_type', 'file')
            source_url = doc.get('source_url', '')
            icon = get_file_icon(file_type)
            status_class = "processed" if doc.get('processed') else "pending"
            status_text = "Processed" if doc.get('processed') else "Pending"

            if source_type == "url" and source_url:
                display_name = f"<a href='{source_url}' target='_blank' style='color: #4CAF50;'>{doc.get('filename', 'Unknown')}</a>"
                icon = "URL"
            else:
                display_name = doc.get('filename', 'Unknown file')

            st.markdown(f"""
            <div class="document-item">
                <span class="document-icon">[{icon}]</span>
                <span class="document-name">{display_name}</span>
                <span class="document-meta">{file_type.upper()}</span>
                <span class="document-status {status_class}">{status_text}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        render_empty_state("[Doc]", "No Documents Yet", "Upload your first document to begin the analysis process.")


def render_analysis_tab(project_id: str):
    """Render the analysis tab with document analysis controls."""
    st.markdown("### Document Analysis")
    st.markdown("APIC will analyze your uploaded documents to identify potential process inefficiencies and generate targeted interview questions.")

    docs_response = api_request("GET", f"/projects/{project_id}/documents", show_error=False)
    has_docs = docs_response and len(docs_response.get("documents", [])) > 0

    if not has_docs:
        render_warning_message("Please upload documents before starting analysis. Go to the Documents tab to upload your process documentation.")
        return

    doc_count = len(docs_response["documents"])
    render_info_message(f"Ready to analyze {doc_count} document(s). This process may take a few minutes depending on the document size.")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start Analysis", use_container_width=True, type="primary"):
            with st.spinner("Analyzing documents and generating interview script..."):
                result = api_request("POST", "/workflow/start", json={"project_id": project_id})
                if result:
                    render_success_message("Analysis complete! Interview script has been generated. Go to the Interview tab to view it.")
                    st.rerun()

    st.divider()

    # Show hypotheses if available
    status_response = api_request("GET", f"/workflow/{project_id}/status", show_error=False)
    if status_response and status_response.get("current_node") not in ["not_started", None]:
        hypo_response = api_request("GET", f"/workflow/{project_id}/hypotheses", show_error=False)
        if hypo_response and hypo_response.get("hypotheses"):
            st.markdown("### Generated Hypotheses")
            st.markdown("Based on document analysis, APIC has identified the following potential areas for improvement:")

            for hypo in hypo_response["hypotheses"]:
                confidence = hypo.get('confidence', 0)
                confidence_color = "#10b981" if confidence > 0.7 else "#f59e0b" if confidence > 0.4 else "#94a3b8"

                with st.expander(f"[*] {hypo.get('process_area', 'Unknown Area')} - {hypo.get('category', 'general').title()}", expanded=False):
                    st.markdown(f"**Description:** {hypo.get('description', 'No description')}")
                    st.markdown(f"**Confidence:** <span style='color: {confidence_color}; font-weight: 600;'>{confidence:.0%}</span>", unsafe_allow_html=True)

                    if hypo.get('evidence'):
                        st.markdown("**Supporting Evidence:**")
                        for e in hypo['evidence'][:5]:
                            st.markdown(f"- {e}")


def render_interview_tab(project_id: str):
    """Render the interview script tab."""
    script_response = api_request("GET", f"/workflow/{project_id}/interview-script", show_error=False)

    has_ai_script = script_response and script_response.get("interview_script")
    script = script_response["interview_script"] if has_ai_script else get_default_interview_script()
    script_type = "ai_generated" if has_ai_script else "default"

    st.markdown("### Interview Script")

    if script_type == "default":
        render_info_message("This is a default interview script. Run the document analysis in the Analysis tab to generate a customized AI-powered interview script.")
    else:
        render_success_message("AI-Generated Script: This interview script has been customized based on the analysis of your uploaded documents.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Script Overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Estimated Duration", f"{script.get('estimated_duration_minutes', 60)} min")
    with col2:
        st.metric("Target Roles", len(script.get('target_roles', [])))
    with col3:
        st.metric("Questions", len(script.get('questions', [])))

    st.divider()

    # Script Content
    st.markdown("#### Script Preview")

    if script.get("target_roles"):
        st.markdown(f"**Target Roles:** {', '.join(script['target_roles'])}")

    with st.expander("Introduction", expanded=True):
        st.markdown(script.get("introduction", "No introduction provided."))

    st.markdown("##### Interview Questions")

    for i, q in enumerate(script.get("questions", []), 1):
        role = q.get('role', 'General')

        st.markdown(f"""
        <div class="question-card">
            <div class="question-number">Question {i}</div>
            <div class="question-role">{role}</div>
            <div class="question-text">{q.get('question', 'No question')}</div>
            <div class="question-intent">Intent: {q.get('intent', 'Gather information')}</div>
        """, unsafe_allow_html=True)

        if q.get("follow_ups"):
            st.markdown('<div style="margin-top: 0.5rem; font-size: 0.875rem; font-weight: 500;">Follow-up Questions:</div>', unsafe_allow_html=True)
            for fu in q["follow_ups"]:
                st.markdown(f"<div style='font-size: 0.875rem; color: #64748b; margin-left: 1rem;'>- {fu}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    if script.get("closing_notes"):
        with st.expander("Closing Notes", expanded=False):
            st.markdown(script["closing_notes"])

    st.divider()

    # Transcript Submission
    st.markdown("### Submit Interview Transcript")
    st.markdown("After conducting the interview, paste the transcript or notes below to generate recommendations.")

    if script_type == "default":
        render_warning_message("Note: You are using the default interview script. For best results, run document analysis first.")

    transcript = st.text_area(
        "Interview Transcript",
        height=250,
        placeholder="Paste your interview notes or transcript here...\n\nInclude:\n- Responses to each question\n- Any additional insights shared\n- Pain points mentioned\n- Current workarounds described",
        help="The more detailed your notes, the better the recommendations will be."
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Submit & Generate Recommendations", use_container_width=True, type="primary"):
            if not transcript or not transcript.strip():
                st.error("Please enter the interview transcript before submitting.")
            elif len(transcript.strip()) < 100:
                st.warning("The transcript seems very short. Consider adding more detail for better recommendations.")
            else:
                with st.spinner("Processing transcript and generating recommendations..."):
                    result = api_request("POST", "/workflow/resume", json={"project_id": project_id, "transcript": transcript.strip()})
                    if result:
                        render_success_message("Analysis complete! Check the Results tab to view recommendations.")
                        st.rerun()


def render_results_tab(project_id: str):
    """Render the results tab with gap analysis and solutions."""
    gaps_response = api_request("GET", f"/workflow/{project_id}/gaps", show_error=False)
    solutions_response = api_request("GET", f"/workflow/{project_id}/solutions", show_error=False)

    has_gaps = gaps_response and gaps_response.get("gap_analyses")
    has_solutions = solutions_response and solutions_response.get("solutions")

    if not has_gaps and not has_solutions:
        render_empty_state("[Chart]", "Results Not Available Yet", "Complete the interview process to generate gap analysis and recommendations. Go to the Interview tab to submit your transcript.")
        return

    if has_gaps:
        st.markdown("### Gap Analysis")
        st.markdown("Identified discrepancies between documented processes and actual practices:")

        for gap in gaps_response["gap_analyses"]:
            st.markdown(f"""
            <div class="analysis-card">
                <div class="analysis-card-header">
                    <span class="analysis-card-title">[*] {gap.get('process_step', 'Unknown Step')}</span>
                </div>
                <div style="display: grid; gap: 0.75rem;">
                    <div><strong>SOP Says:</strong> {gap.get('sop_description', 'N/A')}</div>
                    <div><strong>Observed:</strong> {gap.get('observed_behavior', 'N/A')}</div>
                    <div><strong>Gap:</strong> {gap.get('gap_description', 'N/A')}</div>
                    <div><strong>Impact:</strong> {gap.get('impact', 'N/A')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    if has_solutions:
        st.markdown("### Recommended Solutions")
        st.markdown("Actionable recommendations with estimated ROI:")

        for sol in solutions_response["solutions"]:
            priority = sol.get('pain_point_priority', 'medium').lower()
            priority_class = "priority-high" if priority == "high" else "priority-medium" if priority == "medium" else "priority-low"
            tech_stack = sol.get('tech_stack_recommendation', [])
            tech_text = ', '.join(tech_stack) if tech_stack else 'N/A'

            st.markdown(f"""
            <div class="analysis-card">
                <div class="analysis-card-header">
                    <span class="analysis-card-title">[!] {sol.get('process_step', 'Unknown')}</span>
                    <span class="priority-badge {priority_class}">{priority} priority</span>
                </div>
                <div style="display: grid; gap: 0.75rem;">
                    <div><strong>Solution:</strong> {sol.get('proposed_solution', 'N/A')}</div>
                    <div><strong>Tech Stack:</strong> {tech_text}</div>
                    <div><strong>ROI:</strong> {sol.get('estimated_roi_hours', 0)} hours/month saved</div>
                    <div><strong>Implementation Priority:</strong> {sol.get('implementation_priority', 'N/A')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_report_tab(project_id: str):
    """Render the final report tab."""
    report_response = api_request("GET", f"/workflow/{project_id}/report", show_error=False)

    if not report_response or not report_response.get("report"):
        render_empty_state("[Report]", "Report Not Generated Yet", "The final report will be available after completing the full workflow including document analysis and interview submission.")
        return

    report = report_response["report"]

    st.markdown("### Executive Summary")

    if report.get("executive_summary"):
        summary = report["executive_summary"]

        st.markdown(f"""
        <div class="report-summary">
            <div style="margin-bottom: 1rem;">{summary.get('overview', 'No overview available.')}</div>
        </div>
        """, unsafe_allow_html=True)

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

    if report_response.get("report_pdf_path"):
        st.markdown("### Download Report")

        pdf_path = report_response["report_pdf_path"]

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Download Full Report (PDF)",
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


def main():
    """Render the project detail page with tabs."""
    project_id = st.session_state.current_project_id

    if not project_id:
        st.error("No project selected. Please select a project from the list.")
        if st.button("<- Go to Projects"):
            st.switch_page("pages/1_Projects.py")
        return

    # Fetch project from API (single source of truth)
    project = api_request("GET", f"/projects/{project_id}", show_error=False)
    if not project:
        st.error("Failed to load project. It may have been deleted.")
        if st.button("<- Go to Projects"):
            st.session_state.current_project_id = None
            st.switch_page("pages/1_Projects.py")
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
        st.markdown(f'<div class="page-subtitle">{project.get("client_name", "No client")} | Created {format_datetime(project.get("created_at", ""))}</div>', unsafe_allow_html=True)
    with col2:
        display_status_badge(project.get('status', 'unknown'))
    with col3:
        if st.button("Refresh", help="Refresh project data", key="refresh_project"):
            st.rerun()

    st.divider()

    project_id = project.get('id')

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Documents", "Analysis", "Interview", "Results", "Report"])

    with tab1:
        render_documents_tab(project_id)
    with tab2:
        render_analysis_tab(project_id)
    with tab3:
        render_interview_tab(project_id)
    with tab4:
        render_results_tab(project_id)
    with tab5:
        render_report_tab(project_id)


if __name__ == "__main__":
    main()
