"""
CSS styles for the APIC frontend.
"""

import streamlit as st


def apply_styles():
    """Apply the professional design system CSS to the app."""
    st.markdown("""
<style>
    /* CSS Variables / Design Tokens */
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

    /* Global Styles */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Typography */
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

    /* Cards */
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

    .feature-card-icon { font-size: 2.5rem; margin-bottom: 1rem; }
    .feature-card-title { font-size: 1.25rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.75rem; }
    .feature-card-text { color: var(--text-secondary); font-size: 0.95rem; line-height: 1.6; }

    /* Project Cards */
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

    .project-card:hover { border-color: var(--primary-color); box-shadow: var(--shadow-md); }
    .project-name { font-size: 1.125rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem; }
    .project-client { font-size: 0.875rem; color: var(--text-secondary); }
    .project-meta { font-size: 0.8rem; color: var(--text-muted); }

    /* Status Badges */
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

    .status-created { background-color: #dbeafe; color: #1e40af; }
    .status-created::before { background-color: #1e40af; }
    .status-analyzing { background-color: #fef3c7; color: #92400e; }
    .status-analyzing::before { background-color: #f59e0b; animation: pulse 1.5s infinite; }
    .status-interview_ready { background-color: #fed7aa; color: #9a3412; }
    .status-interview_ready::before { background-color: #ea580c; }
    .status-processing { background-color: #e0e7ff; color: #3730a3; }
    .status-processing::before { background-color: #4f46e5; animation: pulse 1.5s infinite; }
    .status-completed { background-color: #d1fae5; color: #065f46; }
    .status-completed::before { background-color: #059669; }
    .status-failed { background-color: #fee2e2; color: #991b1b; }
    .status-failed::before { background-color: #dc2626; }

    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

    /* Metrics Cards */
    .metric-card {
        background: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.25rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px; }
    .metric-card.primary::before { background: var(--primary-color); }
    .metric-card.success::before { background: var(--success-color); }
    .metric-card.warning::before { background: var(--warning-color); }
    .metric-card.secondary::before { background: var(--secondary-color); }
    .metric-value { font-size: 2rem; font-weight: 700; color: var(--text-primary); line-height: 1; margin-bottom: 0.5rem; }
    .metric-label { font-size: 0.875rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }

    /* Sidebar Styles */
    .sidebar-brand { font-size: 1.5rem; font-weight: 700; color: var(--primary-color); margin-bottom: 0.25rem; }
    .sidebar-tagline { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1.5rem; }
    .sidebar-section { margin-bottom: 1.5rem; }
    .sidebar-section-title { font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.75rem; }

    .current-project-info {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        padding: 1rem;
    }
    .current-project-name { font-size: 0.95rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem; }
    .current-project-client { font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.5rem; }

    /* Buttons */
    .stButton > button { border-radius: 8px; font-weight: 500; transition: all 0.2s ease; }
    .stButton > button:hover { transform: translateY(-1px); }

    /* Forms */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea { border-radius: 8px; border: 1px solid var(--border-color); }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus { border-color: var(--primary-color); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1); }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; background-color: #f1f5f9; padding: 0.5rem; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 0.75rem 1.25rem; font-weight: 500; }
    .stTabs [aria-selected="true"] { background-color: white; box-shadow: var(--shadow-sm); }

    /* Expanders */
    .streamlit-expanderHeader { font-weight: 500; color: var(--text-primary); }

    /* Alerts / Info Boxes */
    .custom-info {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 1px solid #93c5fd;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
    }
    .custom-info-icon { font-size: 1.25rem; flex-shrink: 0; }
    .custom-info-text { color: #1e40af; font-size: 0.95rem; }

    .custom-success {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 1px solid #6ee7b7;
        border-radius: 8px;
        padding: 1rem 1.25rem;
    }
    .custom-success-text { color: #065f46; }

    .custom-warning {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border: 1px solid #fcd34d;
        border-radius: 8px;
        padding: 1rem 1.25rem;
    }
    .custom-warning-text { color: #92400e; }

    /* Empty State */
    .empty-state { text-align: center; padding: 3rem 2rem; background: var(--background-color); border-radius: var(--border-radius); border: 2px dashed var(--border-color); }
    .empty-state-icon { font-size: 3rem; margin-bottom: 1rem; }
    .empty-state-title { font-size: 1.25rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem; }
    .empty-state-text { color: var(--text-secondary); margin-bottom: 1.5rem; }

    /* Document List */
    .document-item { display: flex; align-items: center; padding: 0.75rem 1rem; background: var(--card-background); border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 0.5rem; gap: 0.75rem; }
    .document-icon { font-size: 1.5rem; }
    .document-name { font-weight: 500; color: var(--text-primary); flex-grow: 1; }
    .document-meta { font-size: 0.8rem; color: var(--text-muted); }
    .document-status { font-size: 0.75rem; padding: 0.25rem 0.5rem; border-radius: 4px; }
    .document-status.processed { background: #d1fae5; color: #065f46; }
    .document-status.pending { background: #fef3c7; color: #92400e; }

    /* Question Cards */
    .question-card { background: var(--card-background); border: 1px solid var(--border-color); border-radius: var(--border-radius); padding: 1.25rem; margin-bottom: 1rem; border-left: 4px solid var(--primary-color); }
    .question-number { font-size: 0.75rem; font-weight: 600; color: var(--primary-color); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
    .question-role { display: inline-block; background: #eff6ff; color: #1e40af; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 500; margin-bottom: 0.75rem; }
    .question-text { font-size: 1rem; font-weight: 500; color: var(--text-primary); margin-bottom: 0.75rem; line-height: 1.5; }
    .question-intent { font-size: 0.875rem; color: var(--text-secondary); font-style: italic; margin-bottom: 0.75rem; }
    .follow-up-list { margin: 0; padding-left: 1.25rem; }
    .follow-up-list li { color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.25rem; }

    /* Gap/Solution Cards */
    .analysis-card { background: var(--card-background); border: 1px solid var(--border-color); border-radius: var(--border-radius); padding: 1.25rem; margin-bottom: 1rem; }
    .analysis-card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-color); }
    .analysis-card-title { font-weight: 600; color: var(--text-primary); }
    .priority-badge { padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .priority-high { background: #fee2e2; color: #991b1b; }
    .priority-medium { background: #fef3c7; color: #92400e; }
    .priority-low { background: #d1fae5; color: #065f46; }

    /* Report Summary */
    .report-summary { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1px solid #86efac; border-radius: var(--border-radius); padding: 1.5rem; margin-bottom: 1.5rem; }
    .report-metric { text-align: center; padding: 1rem; }
    .report-metric-value { font-size: 1.75rem; font-weight: 700; color: #166534; margin-bottom: 0.25rem; }
    .report-metric-label { font-size: 0.8rem; color: #15803d; text-transform: uppercase; letter-spacing: 0.05em; }

    /* Responsive Design */
    @media (max-width: 768px) {
        .page-title { font-size: 1.75rem; }
        .feature-card { padding: 1rem; }
        .metric-value { font-size: 1.5rem; }
    }
</style>
""", unsafe_allow_html=True)
